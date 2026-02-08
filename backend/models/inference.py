"""
Prediction utilities that safely handle new data with unknown categorical values.
Use these functions for inference with production data.
"""

import pandas as pd
import numpy as np
import joblib
import os
from pathlib import Path
import torch
import torch.nn as nn
from sklearn.preprocessing import LabelEncoder
import shap
import lime
import lime.lime_tabular
import warnings
warnings.filterwarnings('ignore')


def _normalize_category_value(value):
    normalized = str(value).strip().lower().replace("-", " ")
    normalized = " ".join(normalized.split())
    return normalized


def _match_known_category(value, known_values, normalized_lookup):
    key = _normalize_category_value(value)
    return normalized_lookup.get(key, str(value).strip())


class SafePredictorWrapper:
    """
    Wrapper for safe prediction with support for unseen categorical values.
    Automatically handles label encoding and scaling for new data.
    """
    
    def __init__(self, model_path, label_encoders_path, scaler_path):
        """
        Initialize the predictor with saved model and preprocessing artifacts.
        
        Parameters:
        -----------
        model_path : str
            Path to the saved model (joblib file)
        label_encoders_path : str
            Path to the saved label encoders (joblib file)
        scaler_path : str
            Path to the saved scaler (joblib file)
        """
        self.model = joblib.load(model_path)
        self.label_encoders = joblib.load(label_encoders_path)
        self.scaler = joblib.load(scaler_path)
        
        self.categorical_cols = list(self.label_encoders.keys())
        print(f"✓ Model loaded from {model_path}")
        print(f"✓ Categorical columns: {self.categorical_cols}")
    
    def preprocess_data(self, df):
        """
        Preprocess new data with safe encoding.
        Handles unknown categorical values gracefully.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Input data with raw (unencoded) feature values
        
        Returns:
        --------
        pandas.DataFrame : Preprocessed and scaled data ready for prediction
        """
        df_encoded = df.copy()
        
        # Encode categorical variables safely
        for col in self.categorical_cols:
            if col not in df_encoded.columns:
                raise ValueError(f"Missing required column: {col}")
            
            encoder = self.label_encoders[col]
            known_values = list(encoder.classes_)
            normalized_lookup = {
                _normalize_category_value(val): val for val in known_values
            }
            normalized_col = df_encoded[col].map(
                lambda v: _match_known_category(v, known_values, normalized_lookup)
            )
            unknown_mask = ~normalized_col.astype(str).isin(known_values)
            
            # Transform known values
            encoded_values = encoder.transform(normalized_col.astype(str))
            df_encoded[col] = encoded_values
            
            if unknown_mask.any():
                num_unknown = unknown_mask.sum()
                print(f"⚠ Warning: {num_unknown} unknown values in '{col}':")
                print(f"  Unknown values: {df_encoded.loc[unknown_mask, col].unique()}")
                print(f"  These will be encoded as -1")
        
        # Scale numerical features
        df_scaled = self.scaler.transform(df_encoded)
        df_scaled = pd.DataFrame(df_scaled, columns=df_encoded.columns)
        
        return df_scaled
    
    def predict(self, df):
        """
        Make predictions on new data with unknown values.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Input data with features (can include unknown categorical values)
        
        Returns:
        --------
        numpy.ndarray : Model predictions
        """
        print(f"\n📊 Processing {len(df)} samples for prediction...")
        
        # Preprocess
        df_processed = self.preprocess_data(df)
        
        # Predict
        predictions = self.model.predict(df_processed)
        
        print(f"✓ Predictions completed")
        return predictions
    
    def predict_with_confidence(self, df):
        """
        Make predictions and return confidence metrics if available.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Input data
        
        Returns:
        --------
        tuple : (predictions, confidence_scores)
        """
        df_processed = self.preprocess_data(df)
        
        # Get predictions
        predictions = self.model.predict(df_processed)
        
        # Try to get feature importance-based confidence
        if hasattr(self.model, 'predict_proba'):
            confidence = np.max(self.model.predict_proba(df_processed), axis=1)
        elif hasattr(self.model, 'feature_importances_'):
            # Use feature importance as proxy for confidence
            confidence = np.ones_like(predictions) * np.mean(self.model.feature_importances_)
        else:
            confidence = np.ones_like(predictions)
        
        return predictions, confidence


# ============================================================================
# Stacked Ensemble Predictor
# ============================================================================

class TabTransformer(nn.Module):
    """TabTransformer model architecture for loading trained PyTorch model."""
    
    def __init__(self, num_features, cat_dims, cat_idxs, num_idxs, embed_dim=32, num_heads=4, num_layers=2, mlp_hidden=128, dropout=0.1):
        super(TabTransformer, self).__init__()
        self.cat_idxs = cat_idxs
        self.num_idxs = num_idxs
        
        # Embeddings for categorical features
        self.cat_embeddings = nn.ModuleList([
            nn.Embedding(dim + 1, embed_dim) for dim in cat_dims
        ])
        
        # Transformer for categorical embeddings
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=embed_dim * 4,
            dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Calculate input dimension for MLP
        total_dim = len(cat_idxs) * embed_dim + len(num_idxs)
        
        self.mlp = nn.Sequential(
            nn.Linear(total_dim, mlp_hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_hidden, mlp_hidden // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_hidden // 2, 1)
        )
    
    def forward(self, x):
        # Process categorical features through Transformer
        if len(self.cat_idxs) > 0:
            cat_embeds = []
            for i, idx in enumerate(self.cat_idxs):
                cat_embeds.append(self.cat_embeddings[i](x[:, idx].long()))
            
            cat_embeds = torch.stack(cat_embeds, dim=1)
            cat_transformed = self.transformer(cat_embeds)
            cat_part = cat_transformed.flatten(start_dim=1)
        
        # Process numerical features
        if len(self.num_idxs) > 0:
            num_features = x[:, self.num_idxs]
        else:
            num_features = None
        
        # Combine
        if len(self.cat_idxs) > 0 and len(self.num_idxs) > 0:
            combined = torch.cat([cat_part, num_features], dim=1)
        elif len(self.cat_idxs) > 0:
            combined = cat_part
        else:
            combined = num_features
            
        output = self.mlp(combined)
        return output.squeeze()


class StackedEnsemblePredictor:
    """
    Stacked ensemble predictor combining Random Forest, LightGBM, and TabTransformer
    with a Linear Regression meta-learner.
    """
    
    def __init__(self, models_dir=None):
        """
        Initialize the stacked ensemble predictor.
        
        Parameters:
        -----------
        models_dir : str, optional
            Directory containing the model files. If None, uses the script directory.
        """
        if models_dir is None:
            models_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.models_dir = models_dir
        
        # Define paths
        self.rf_path = os.path.join(models_dir, 'random_forest_model.joblib')
        self.lgbm_path = os.path.join(models_dir, 'lightgbm_model.joblib')
        self.transformer_path = os.path.join(models_dir, 'tab_transformer_model.pth')
        self.meta_learner_path = os.path.join(models_dir, 'meta_learner.joblib')
        self.encoders_path = os.path.join(models_dir, 'label_encoders.joblib')
        self.scaler_path = os.path.join(models_dir, 'scaler.joblib')
        
        # Load models
        self._load_models()
        
    def _load_models(self):
        """Load all base models and meta-learner."""
        print("\n" + "=" * 60)
        print("LOADING STACKED ENSEMBLE MODELS")
        print("=" * 60)
        
        # Check if all required files exist
        required_files = {
            'Random Forest': self.rf_path,
            'LightGBM': self.lgbm_path,
            'TabTransformer': self.transformer_path,
            'Meta-Learner': self.meta_learner_path,
            'Label Encoders': self.encoders_path,
            'Scaler': self.scaler_path
        }
        
        missing_files = [name for name, path in required_files.items() if not os.path.exists(path)]
        
        if missing_files:
            raise FileNotFoundError(
                f"Missing required files: {', '.join(missing_files)}\n"
                f"Please ensure all models are trained:\n"
                f"  1. Run preprocessing.py\n"
                f"  2. Run random_forest.py\n"
                f"  3. Run lightgbm_model.py\n"
                f"  4. Run tab_transformer.py\n"
                f"  5. Run stacked_ensemble.py"
            )
        
        # Load preprocessing components
        print("\nLoading preprocessing components...")
        self.label_encoders = joblib.load(self.encoders_path)
        self.scaler = joblib.load(self.scaler_path)
        self.categorical_cols = list(self.label_encoders.keys())
        print(f"  ✓ Label encoders and scaler loaded")
        
        # Load Random Forest
        print("\nLoading base models...")
        self.rf_model = joblib.load(self.rf_path)
        print(f"  ✓ Random Forest loaded")
        
        # Load LightGBM
        self.lgbm_model = joblib.load(self.lgbm_path)
        print(f"  ✓ LightGBM loaded")
        
        # Load TabTransformer
        self._load_transformer()
        print(f"  ✓ TabTransformer loaded (device: {self.device})")
        
        # Load meta-learner
        self.meta_learner = joblib.load(self.meta_learner_path)
        print(f"  ✓ Meta-learner (Linear Regression) loaded")
        
        print("\n" + "=" * 60)
        print("✓ ALL ENSEMBLE MODELS LOADED SUCCESSFULLY")
        print("=" * 60)
        
    def _load_transformer(self):
        """Load TabTransformer model."""
        # Need to load original dataset to get categorical dimensions
        project_dir = os.path.dirname(self.models_dir)
        original_path = os.path.join(project_dir, 'dataset', 'credit_data.csv')
        
        if not os.path.exists(original_path):
            raise FileNotFoundError(f"Original dataset not found: {original_path}")
        
        df_original = pd.read_csv(original_path)
        feature_columns = ['Age', 'Income', 'Credit History Length', 'Number of Existing Loans', 
                          'Existing Customer', 'State', 'City', 'LTV Ratio', 
                          'Employment Profile', 'Occupation']
        X_original = df_original[feature_columns]
        
        # Get categorical and numerical columns
        categorical_cols = X_original.select_dtypes(include=['object']).columns.tolist()
        numerical_cols = X_original.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        # Encode to get dimensions
        X_temp = X_original.copy()
        for col in categorical_cols:
            le = LabelEncoder()
            X_temp[col] = le.fit_transform(X_temp[col].astype(str))
        
        # Get dimensions for transformer
        self.cat_dims = [X_temp[col].nunique() for col in categorical_cols]
        self.cat_idxs = [X_temp.columns.tolist().index(col) for col in categorical_cols]
        self.num_idxs = [X_temp.columns.tolist().index(col) for col in numerical_cols]
        
        # Initialize model
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.transformer_model = TabTransformer(
            num_features=X_temp.shape[1],
            cat_dims=self.cat_dims,
            cat_idxs=self.cat_idxs,
            num_idxs=self.num_idxs,
            embed_dim=32,
            num_heads=4,
            num_layers=2,
            mlp_hidden=128,
            dropout=0.1
        ).to(self.device)
        
        # Load weights
        self.transformer_model.load_state_dict(torch.load(self.transformer_path, map_location=self.device))
        self.transformer_model.eval()
    
    def preprocess_data(self, df):
        """
        Preprocess input data (encoding and scaling).
        Returns both scaled and encoded-only versions.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Raw input data
        
        Returns:
        --------
        tuple : (df_scaled, df_encoded_only)
            - df_scaled: For RF and LightGBM
            - df_encoded_only: For TabTransformer
        """
        df_encoded = df.copy()
        
        # Encode categorical variables
        for col in self.categorical_cols:
            if col not in df_encoded.columns:
                raise ValueError(f"Missing required column: {col}")
            
            encoder = self.label_encoders[col]
            known_values = list(encoder.classes_)
            normalized_lookup = {
                _normalize_category_value(val): val for val in known_values
            }
            normalized_col = df_encoded[col].map(
                lambda v: _match_known_category(v, known_values, normalized_lookup)
            )
            unknown_mask = ~normalized_col.astype(str).isin(known_values)
            
            # Transform known values
            encoded_values = encoder.transform(normalized_col.astype(str))
            df_encoded[col] = encoded_values
            
            if unknown_mask.any():
                num_unknown = unknown_mask.sum()
                print(f"⚠ Warning: {num_unknown} unknown values in '{col}' - encoded as -1")
        
        # Keep encoded-only version for TabTransformer
        df_encoded_only = df_encoded.copy()
        
        # Scale features for RF and LightGBM
        df_scaled = self.scaler.transform(df_encoded)
        df_scaled = pd.DataFrame(df_scaled, columns=df_encoded.columns, index=df_encoded.index)
        
        return df_scaled, df_encoded_only
    
    def _get_base_predictions(self, df_scaled, df_encoded):
        """
        Get predictions from all base models.
        
        Parameters:
        -----------
        df_scaled : pandas.DataFrame
            Scaled data for RF and LightGBM
        df_encoded : pandas.DataFrame
            Encoded (not scaled) data for TabTransformer
        
        Returns:
        --------
        numpy.ndarray : Stacked predictions from base models (shape: n_samples x 3)
        """
        # Ensure all data is numeric (for SHAP compatibility)
        df_scaled_safe = df_scaled.copy()
        for col in df_scaled_safe.columns:
            if df_scaled_safe[col].dtype == 'object':
                df_scaled_safe[col] = pd.to_numeric(df_scaled_safe[col], errors='coerce').fillna(0)
        
        # Random Forest predictions (uses scaled data)
        rf_pred = self.rf_model.predict(df_scaled_safe)
        
        # LightGBM predictions (uses scaled data)
        lgbm_pred = self.lgbm_model.predict(df_scaled_safe)
        
        # TabTransformer predictions (uses encoded but not scaled data)
        # Replace -1 (unknown values) with the last valid embedding index (dim - 1)
        df_encoded_safe = df_encoded.copy()
        for i, col in enumerate(df_encoded.columns):
            # Ensure column is numeric first
            if df_encoded_safe[col].dtype == 'object':
                df_encoded_safe[col] = pd.to_numeric(df_encoded_safe[col], errors='coerce').fillna(-1)
            
            if col in self.categorical_cols:
                # Find the categorical index
                cat_col_idx = list(self.categorical_cols).index(col)
                max_valid_idx = self.cat_dims[cat_col_idx]  # The embedding size is dim + 1, so max valid is dim
                # Replace -1 with max_valid_idx (the last embedding, which we'll treat as "unknown")
                df_encoded_safe.loc[df_encoded_safe[col] < 0, col] = max_valid_idx
        
        with torch.no_grad():
            X_tensor = torch.FloatTensor(df_encoded_safe.values).to(self.device)
            transformer_pred = self.transformer_model(X_tensor).cpu().numpy()
        
        # Stack predictions
        base_predictions = np.column_stack([rf_pred, lgbm_pred, transformer_pred])
        
        return base_predictions
    
    def predict(self, df):
        """
        Make ensemble predictions on new data.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Raw input data with features
        
        Returns:
        --------
        numpy.ndarray : Final ensemble predictions
        """
        print(f"\n📊 Processing {len(df)} samples with Stacked Ensemble...")
        
        # Preprocess (returns both scaled and encoded versions)
        df_scaled, df_encoded = self.preprocess_data(df)
        
        # Get base model predictions
        print("  - Getting predictions from base models...")
        base_predictions = self._get_base_predictions(df_scaled, df_encoded)
        
        # Get final prediction from meta-learner
        print("  - Combining with meta-learner...")
        ensemble_predictions = self.meta_learner.predict(base_predictions)
        
        print("✓ Ensemble predictions completed")
        return ensemble_predictions
    
    def predict_with_base_models(self, df):
        """
        Make predictions and return both base model and ensemble predictions.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Raw input data
        
        Returns:
        --------
        dict : Dictionary containing predictions from each model and the ensemble
        """
        # Preprocess (returns both scaled and encoded versions)
        df_scaled, df_encoded = self.preprocess_data(df)
        
        # Get base model predictions
        base_predictions = self._get_base_predictions(df_scaled, df_encoded)
        
        # Get ensemble prediction
        ensemble_predictions = self.meta_learner.predict(base_predictions)
        
        return {
            'random_forest': base_predictions[:, 0],
            'lightgbm': base_predictions[:, 1],
            'tab_transformer': base_predictions[:, 2],
            'ensemble': ensemble_predictions
        }
    
    def get_model_weights(self):
        """
        Get the weights (coefficients) assigned to each base model by the meta-learner.
        
        Returns:
        --------
        dict : Dictionary with model names and their weights
        """
        return {
            'random_forest': self.meta_learner.coef_[0],
            'lightgbm': self.meta_learner.coef_[1],
            'tab_transformer': self.meta_learner.coef_[2],
            'intercept': self.meta_learner.intercept_
        }
    
    def _ensemble_predict_fn(self, X_raw):
        """
        Wrapper function for SHAP/LIME that takes raw features and returns ensemble predictions.
        Handles both numeric and mixed data types.
        
        Parameters:
        -----------
        X_raw : numpy.ndarray or pandas.DataFrame
            Raw input features
        
        Returns:
        --------
        numpy.ndarray : Ensemble predictions
        """
        if isinstance(X_raw, np.ndarray):
            # Convert to DataFrame with proper column names
            X_df = pd.DataFrame(X_raw, columns=self.feature_columns)
        else:
            X_df = X_raw.copy()
        
        # Ensure categorical columns are strings
        categorical_cols = self.categorical_cols
        for col in categorical_cols:
            if col in X_df.columns:
                X_df[col] = X_df[col].astype(str)
        
        # Get predictions (suppress warnings)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            predictions = self.predict(X_df)
        
        return predictions
    
    def explain_meta_learner(self, df):
        """
        Explain which base model predictions are most influential for the meta-learner.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Input data
        
        Returns:
        --------
        pandas.DataFrame : Base model predictions with their contributions
        """
        print("\n" + "="*60)
        print("META-LEARNER EXPLANATION")
        print("="*60)
        
        # Get base model predictions
        df_scaled, df_encoded = self.preprocess_data(df)
        base_predictions = self._get_base_predictions(df_scaled, df_encoded)
        
        # Get ensemble prediction
        ensemble_pred = self.meta_learner.predict(base_predictions)
        
        # Calculate contributions
        weights = self.meta_learner.coef_
        intercept = self.meta_learner.intercept_
        
        results = []
        for i in range(len(df)):
            contributions = base_predictions[i] * weights
            result = {
                'Sample': i + 1,
                'RF_Prediction': base_predictions[i, 0],
                'RF_Contribution': contributions[0],
                'LightGBM_Prediction': base_predictions[i, 1],
                'LightGBM_Contribution': contributions[1],
                'Transformer_Prediction': base_predictions[i, 2],
                'Transformer_Contribution': contributions[2],
                'Intercept': intercept,
                'Ensemble_Prediction': ensemble_pred[i]
            }
            results.append(result)
        
        results_df = pd.DataFrame(results)
        
        print("\nBase Model Contributions to Ensemble Predictions:")
        print(results_df.to_string(index=False))
        
        # Show average importance
        avg_contributions = np.abs(base_predictions * weights).mean(axis=0)
        total_contribution = avg_contributions.sum()
        
        importance_df = pd.DataFrame({
            'Base Model': ['Random Forest', 'LightGBM', 'TabTransformer'],
            'Avg Absolute Contribution': avg_contributions,
            'Importance %': (avg_contributions / total_contribution * 100)
        })
        
        print("\n" + "="*60)
        print("Average Base Model Importance:")
        print("="*60)
        print(importance_df.to_string(index=False))
        
        return results_df
    
    def explain_with_shap(self, X_sample, X_background=None, sample_size=100):
        """
        Explain ensemble predictions using SHAP values on original features.
        
        Parameters:
        -----------
        X_sample : pandas.DataFrame
            Samples to explain
        X_background : pandas.DataFrame, optional
            Background dataset for SHAP. If None, uses a subset of X_sample
        sample_size : int, default=100
            Number of samples to use for SHAP calculation
        
        Returns:
        --------
        tuple : (shap_values, shap_explainer)
        """
        print("\n" + "="*60)
        print("SHAP ANALYSIS - ENSEMBLE MODEL")
        print("="*60)
        
        # Store feature columns
        self.feature_columns = X_sample.columns.tolist()
        
        # Prepare background data
        if X_background is None:
            if len(X_sample) > sample_size:
                X_background = X_sample.sample(n=sample_size, random_state=42)
            else:
                X_background = X_sample
        
        print(f"\nCalculating SHAP values for {len(X_sample)} samples...")
        print(f"Using {len(X_background)} background samples...")
        
        # Create SHAP explainer
        explainer = shap.KernelExplainer(
            self._ensemble_predict_fn, 
            X_background.values,
            link='identity'
        )
        
        # Calculate SHAP values
        shap_values = explainer.shap_values(X_sample.values, nsamples=100)
        
        # Create importance DataFrame
        shap_importance = pd.DataFrame({
            'Feature': X_sample.columns,
            'SHAP Importance': np.abs(shap_values).mean(axis=0)
        }).sort_values('SHAP Importance', ascending=False)
        
        print("\n" + "="*60)
        print("SHAP Feature Importance (Top 10):")
        print("="*60)
        print(shap_importance.head(10).to_string(index=False))
        
        return shap_values, explainer
    
    def explain_with_lime(self, X_sample, X_train, sample_idx=0, num_features=10):
        """
        Explain a specific prediction using LIME.
        
        Parameters:
        -----------
        X_sample : pandas.DataFrame
            Sample to explain
        X_train : pandas.DataFrame
            Training data for LIME reference
        sample_idx : int, default=0
            Index of sample to explain
        num_features : int, default=10
            Number of top features to show
        
        Returns:
        --------
        lime.explanation.Explanation : LIME explanation object
        """
        print("\n" + "="*60)
        print("LIME ANALYSIS - ENSEMBLE MODEL")
        print("="*60)
        
        # Store feature columns
        self.feature_columns = X_sample.columns.tolist()
        
        # Preprocess training data to get numeric representation
        # LIME needs numeric data to compute quartiles
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            X_train_scaled, X_train_encoded = self.preprocess_data(X_train)
        
        # Identify categorical features by index
        categorical_features = [i for i, col in enumerate(X_sample.columns) 
                               if col in self.categorical_cols]
        
        # Create LIME explainer with properly encoded training data
        lime_explainer = lime.lime_tabular.LimeTabularExplainer(
            training_data=X_train_scaled.values,  # Use scaled/encoded data
            feature_names=X_sample.columns.tolist(),
            mode='regression',
            categorical_features=categorical_features,
            random_state=42
        )
        
        # Get prediction for the sample
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            prediction = self.predict(X_sample.iloc[[sample_idx]])
        
        print(f"\nExplaining Sample {sample_idx + 1}:")
        print(f"Ensemble Prediction: {prediction[0]:.2f}")
        
        # Preprocess the sample for LIME
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            X_sample_scaled, X_sample_encoded = self.preprocess_data(X_sample)
        
        # Generate explanation
        lime_exp = lime_explainer.explain_instance(
            data_row=X_sample_scaled.iloc[sample_idx].values,  # Use scaled data
            predict_fn=lambda x: self._ensemble_predict_fn_preprocessed(x),  # Use preprocessed version
            num_features=num_features
        )
        
        print("\n" + "="*60)
        print(f"LIME Feature Contributions (Top {num_features}):")
        print("="*60)
        
        lime_list = lime_exp.as_list()
        lime_df = pd.DataFrame(lime_list, columns=['Feature Rule', 'Contribution'])
        print(lime_df.to_string(index=False))
        
        return lime_exp
    
    def _ensemble_predict_fn_preprocessed(self, X_preprocessed):
        """
        Wrapper for LIME that takes already preprocessed (scaled) data.
        
        Parameters:
        -----------
        X_preprocessed : numpy.ndarray
            Already scaled and encoded data
        
        Returns:
        --------
        numpy.ndarray : Ensemble predictions
        """
        # Create DataFrame from preprocessed data
        df_scaled = pd.DataFrame(X_preprocessed, columns=self.feature_columns)
        
        # For TabTransformer, we need the encoded-only version
        # Since we have scaled data, we need to inverse transform and re-encode
        # For simplicity with LIME, we'll use a unified approach
        
        # Get both versions needed
        df_encoded = df_scaled.copy()  # For TabTransformer (will be adjusted in _get_base_predictions)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            base_predictions = self._get_base_predictions(df_scaled, df_encoded)
            ensemble_predictions = self.meta_learner.predict(base_predictions)
        
        return ensemble_predictions
    
    def explain_sample_detailed(self, X_sample, sample_idx=0):
        """
        Provide a comprehensive explanation for a single sample showing:
        1. Base model predictions
        2. Meta-learner contributions
        3. Feature-level explanations
        
        Parameters:
        -----------
        X_sample : pandas.DataFrame
            Sample data
        sample_idx : int, default=0
            Index of sample to explain
        
        Returns:
        --------
        dict : Comprehensive explanation dictionary
        """
        print("\n" + "="*70)
        print(f"COMPREHENSIVE EXPLANATION - SAMPLE {sample_idx + 1}")
        print("="*70)
        
        # Get the specific sample
        sample = X_sample.iloc[[sample_idx]]
        
        # 1. Base Model Predictions
        print("\n[1] BASE MODEL PREDICTIONS")
        print("-" * 70)
        all_preds = self.predict_with_base_models(sample)
        
        base_df = pd.DataFrame({
            'Model': ['Random Forest', 'LightGBM', 'TabTransformer', 'Ensemble'],
            'Prediction': [
                all_preds['random_forest'][0],
                all_preds['lightgbm'][0],
                all_preds['tab_transformer'][0],
                all_preds['ensemble'][0]
            ]
        })
        print(base_df.to_string(index=False))
        
        # 2. Meta-Learner Contributions
        print("\n[2] META-LEARNER CONTRIBUTIONS")
        print("-" * 70)
        weights = self.get_model_weights()
        
        contributions = {
            'RF': all_preds['random_forest'][0] * weights['random_forest'],
            'LightGBM': all_preds['lightgbm'][0] * weights['lightgbm'],
            'Transformer': all_preds['tab_transformer'][0] * weights['tab_transformer'],
            'Intercept': weights['intercept']
        }
        
        contrib_df = pd.DataFrame({
            'Component': list(contributions.keys()),
            'Value': list(contributions.values()),
            'Weight': [weights['random_forest'], weights['lightgbm'], 
                      weights['tab_transformer'], 1.0]
        })
        print(contrib_df.to_string(index=False))
        print(f"\nSum of Contributions: {sum(contributions.values()):.2f}")
        print(f"Final Prediction: {all_preds['ensemble'][0]:.2f}")
        
        # 3. Input Features
        print("\n[3] INPUT FEATURES")
        print("-" * 70)
        feature_df = pd.DataFrame({
            'Feature': sample.columns,
            'Value': sample.iloc[0].values
        })
        print(feature_df.to_string(index=False))
        
        return {
            'sample_idx': sample_idx,
            'base_predictions': all_preds,
            'contributions': contributions,
            'weights': weights,
            'features': sample.to_dict('records')[0]
        }


# ============================================================================
# Example Usage Functions
# ============================================================================

def predict_single_sample(sample_dict, model_path, encoders_path, scaler_path):
    """
    Convenience function to predict on a single sample.
    
    Example:
    --------
    sample = {
        'Age': 45,
        'Income': 75000,
        'State': 'California',  # Could be unknown
        'City': 'Los Angeles',  # Could be unknown
        'Employment Profile': 'Employed',
        'Occupation': 'Engineer',
        'Credit History Length': 10,
        'Number of Existing Loans': 2,
        'Existing Customer': 'Yes',
        'LTV Ratio': 0.8
    }
    
    prediction = predict_single_sample(sample, model_path, encoders_path, scaler_path)
    """
    df = pd.DataFrame([sample_dict])
    predictor = SafePredictorWrapper(model_path, encoders_path, scaler_path)
    return predictor.predict(df)[0]


def predict_batch(df, model_path, encoders_path, scaler_path):
    """
    Convenience function for batch predictions on a DataFrame.
    """
    predictor = SafePredictorWrapper(model_path, encoders_path, scaler_path)
    return predictor.predict(df)


def handle_unknown_values_report(df, label_encoders):
    """
    Generate a report of unknown categorical values in the data.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Data to check
    label_encoders : dict
        Dictionary of encoders
    
    Returns:
    --------
    dict : Report with unknown values
    """
    report = {}
    
    for col, encoder in label_encoders.items():
        if col in df.columns:
            known_set = set(encoder.classes_)
            df_values = set(df[col].astype(str))
            unknown = df_values - known_set
            
            if unknown:
                report[col] = {
                    'unknown_values': list(unknown),
                    'count': len(unknown),
                    'known_values': len(encoder.classes_)
                }
    
    return report


def compare_predictions_by_location(samples_df, predictor, location_variations=None):
    """
    Compare predictions for samples with different state/city combinations.
    
    Parameters:
    -----------
    samples_df : pandas.DataFrame
        Original sample data
    predictor : SafePredictorWrapper
        Initialized predictor instance
    location_variations : list, default=None
        List of (state, city) tuples to test. 
        If None, uses: [Delhi/New Delhi, West Bengal/Kolkata, Karnataka/Bengaluru]
    
    Returns:
    --------
    pandas.DataFrame : Comparison table with predictions for each location
    """
    if location_variations is None:
        location_variations = [
            ('Delhi', 'New Delhi'),
            ('West Bengal', 'Kolkata'),
            ('Karnataka', 'Bengaluru')
        ]
    
    results = []
    
    for idx, row in samples_df.iterrows():
        sample_num = idx + 1
        
        # Get original prediction
        pred_original = predictor.predict(samples_df.iloc[[idx]])[0]
        
        original_state = row['State']
        original_city = row['City']
        
        print(f"\n{'='*80}")
        print(f"SAMPLE {sample_num} - Location Impact Analysis")
        print(f"{'='*80}")
        print(f"\nOriginal Location: {original_state}, {original_city}")
        print(f"Original Prediction: {pred_original:.2f}\n")
        
        sample_results = [{
            'Sample': sample_num,
            'State': original_state,
            'City': original_city,
            'Prediction': pred_original,
            'Difference': 0.0,
            'Pct_Change': 0.0
        }]
        
        # Test with each location variation
        for state, city in location_variations:
            # Create variant with new location
            variant = samples_df.iloc[[idx]].copy()
            variant['State'] = state
            variant['City'] = city
            
            # Get prediction for variant
            pred_variant = predictor.predict(variant)[0]
            
            # Calculate differences
            diff = pred_variant - pred_original
            pct_change = (diff / pred_original * 100) if pred_original != 0 else 0
            
            print(f"Variant: {state}, {city}")
            print(f"  Prediction: {pred_variant:.2f}")
            print(f"  Difference: {diff:+.2f} ({pct_change:+.2f}%)\n")
            
            sample_results.append({
                'Sample': sample_num,
                'State': state,
                'City': city,
                'Prediction': pred_variant,
                'Difference': diff,
                'Pct_Change': pct_change
            })
        
        results.extend(sample_results)
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Print summary
    print(f"\n{'='*80}")
    print("SUMMARY TABLE - All Predictions Across Locations")
    print(f"{'='*80}\n")
    print(results_df.to_string(index=False))
    
    return results_df


def compare_state_city_impact(predictor, base_sample):
    """
    Analyze the impact of state and city on a single sample prediction.
    Shows the most impactful locations.
    
    Parameters:
    -----------
    predictor : SafePredictorWrapper
        Initialized predictor instance
    base_sample : dict
        Base sample with all required features
    
    Returns:
    --------
    pandas.DataFrame : DataFrame with state/city combinations and predictions
    """
    # Get base prediction
    base_df = pd.DataFrame([base_sample])
    base_pred = predictor.predict(base_df)[0]
    
    # Get all known states and cities from encoders
    state_encoder = predictor.label_encoders.get('State')
    city_encoder = predictor.label_encoders.get('City')
    
    if state_encoder is None or city_encoder is None:
        print("State or City encoder not found!")
        return None
    
    known_states = state_encoder.classes_.tolist()
    known_cities = city_encoder.classes_.tolist()
    
    print(f"Base sample prediction: {base_pred:.2f}")
    print(f"Testing {len(known_states)} states × {len(known_cities)} cities = {len(known_states) * len(known_cities)} combinations...")
    
    results = []
    
    # Test all combinations
    for state in known_states:
        for city in known_cities:
            variant = base_sample.copy()
            variant['State'] = state
            variant['City'] = city
            
            variant_df = pd.DataFrame([variant])
            pred = predictor.predict(variant_df)[0]
            
            diff = pred - base_pred
            pct_change = (diff / base_pred * 100) if base_pred != 0 else 0
            
            results.append({
                'State': state,
                'City': city,
                'Prediction': pred,
                'Difference': diff,
                'Pct_Change': pct_change
            })
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('Difference', ascending=False)
    
    print(f"\n{'='*80}")
    print("Top 10 - Highest predictions")
    print(f"{'='*80}\n")
    print(results_df.head(10).to_string(index=False))
    
    print(f"\n{'='*80}")
    print("Bottom 10 - Lowest predictions")
    print(f"{'='*80}\n")
    print(results_df.tail(10).to_string(index=False))
    
    return results_df


# ============================================================================
# Testing Example
# ============================================================================

if __name__ == "__main__":
    # Example: Test with unknown values and compare locations
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    model_path = os.path.join(script_dir, 'random_forest_model.joblib')
    encoders_path = os.path.join(script_dir, 'label_encoders.joblib')
    scaler_path = os.path.join(script_dir, 'scaler.joblib')
    
    # Check if files exist
    if all(os.path.exists(p) for p in [model_path, encoders_path, scaler_path]):
        # Create test data with a mix of known and unknown values
        test_data = pd.DataFrame({
            'Age': [35, 45, 50],
            'Income': [50000, 75000, 100000],
            'Credit History Length': [5, 15, 20],
            'Number of Existing Loans': [1, 2, 3],
            'Existing Customer': ['Yes', 'No', 'Yes'],
            'State': ['California', 'Texas', 'Florida'],
            'City': ['Los Angeles', 'Houston', 'Miami'],
            'LTV Ratio': [0.8, 0.7, 0.75],
            'Employment Profile': ['Freelancer', 'Self-Employed', 'Salaried'],
            'Occupation': ['Software Engineer', 'Doctor', 'Business Owner']
        })
        
        print("📋 Test Data:")
        print(test_data)
        
        predictor = SafePredictorWrapper(model_path, encoders_path, scaler_path)
        
        # Test 1: Basic predictions
        print("\n" + "="*80)
        print("TEST 1: Basic Predictions")
        print("="*80)
        predictions = predictor.predict(test_data)
        
        print("\n🎯 Basic Predictions:")
        for i, pred in enumerate(predictions):
            print(f"  Sample {i+1}: {pred:.2f}")
        
        # Test 2: Compare predictions by location
        print("\n\n" + "="*80)
        print("TEST 2: Location-Based Prediction Comparison")
        print("="*80)
        
        location_variations = [
            ('Delhi', 'New Delhi'),
            ('West Bengal', 'Kolkata'),
            ('Karnataka', 'Bengaluru')
        ]
        
        comparison_results = compare_predictions_by_location(
            test_data, 
            predictor,
            location_variations=location_variations
        )
        
        # Save comparison results
        output_file = os.path.join(script_dir, 'location_comparison_results.csv')
        comparison_results.to_csv(output_file, index=False)
        print(f"\n✓ Results saved to: {output_file}")
        
        # Test 3: Stacked Ensemble Predictions
        print("\n\n" + "="*80)
        print("TEST 3: Stacked Ensemble Predictions")
        print("="*80)
        
        try:
            ensemble_predictor = StackedEnsemblePredictor(script_dir)
            
            # Get predictions from all models
            all_predictions = ensemble_predictor.predict_with_base_models(test_data)
            
            print("\n🎯 Predictions from All Models:")
            comparison_df = pd.DataFrame({
                'Sample': range(1, len(test_data) + 1),
                'Random Forest': all_predictions['random_forest'],
                'LightGBM': all_predictions['lightgbm'],
                'TabTransformer': all_predictions['tab_transformer'],
                'Ensemble': all_predictions['ensemble']
            })
            print(comparison_df.to_string(index=False))
            
            # Show model weights
            print("\n📊 Meta-Learner Model Weights:")
            weights = ensemble_predictor.get_model_weights()
            weights_df = pd.DataFrame({
                'Model': ['Random Forest', 'LightGBM', 'TabTransformer', 'Intercept'],
                'Weight': [weights['random_forest'], weights['lightgbm'], 
                          weights['tab_transformer'], weights['intercept']]
            })
            print(weights_df.to_string(index=False))
            
        except FileNotFoundError as e:
            print(f"\n⚠ Ensemble model not available: {e}")
            print("   Run stacked_ensemble.py to train the ensemble model.")
        
    else:
        print("❌ Missing model files. Please run preprocessing.py and model training scripts first.")
        print(f"   Looking for:")
        print(f"   - {model_path}")
        print(f"   - {encoders_path}")
        print(f"   - {scaler_path}")
