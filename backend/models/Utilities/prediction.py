"""
Credit Score Prediction Utility
================================
A clean, user-friendly interface for predicting credit scores using the stacked ensemble model.
Includes built-in support for SHAP and LIME explanations.

Author: FairScore Team
Date: February 2026
"""

import pandas as pd
import numpy as np
import os
import sys
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path to import inference module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inference import StackedEnsemblePredictor


class CreditScorePredictor:
    """
    High-level interface for credit score prediction using the stacked ensemble model.
    
    Features:
    ---------
    - Simple prediction interface
    - Automatic data validation and preprocessing
    - Built-in SHAP and LIME explanations
    - Handles unknown categorical values gracefully
    - Production-ready with comprehensive error handling
    
    Example:
    --------
    >>> predictor = CreditScorePredictor()
    >>> 
    >>> # Single prediction
    >>> data = {
    ...     'Age': 45,
    ...     'Income': 75000,
    ...     'Credit History Length': 15,
    ...     'Number of Existing Loans': 2,
    ...     'Existing Customer': 'Yes',
    ...     'State': 'Maharashtra',
    ...     'City': 'Mumbai',
    ...     'LTV Ratio': 0.7,
    ...     'Employment Profile': 'Salaried',
    ...     'Occupation': 'Engineer'
    ... }
    >>> 
    >>> result = predictor.predict(data)
    >>> print(f"Predicted Credit Score: {result['prediction']}")
    >>> 
    >>> # Get explanation
    >>> explanation = predictor.explain_prediction_shap(data)
    """
    
    def __init__(self, models_dir=None):
        """
        Initialize the credit score predictor.
        
        Parameters:
        -----------
        models_dir : str, optional
            Directory containing the trained models. 
            If None, uses the default models directory.
        """
        if models_dir is None:
            # Default to the models directory
            models_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.models_dir = models_dir
        self.ensemble = None
        self._background_data = None
        self._training_data = None
        
        # Required feature columns (in order)
        self.required_features = [
            'Age',
            'Income', 
            'Credit History Length',
            'Number of Existing Loans',
            'Existing Customer',
            'State',
            'City',
            'LTV Ratio',
            'Employment Profile',
            'Occupation'
        ]
        
        # Load the ensemble model
        self._load_model()
    
    def _load_model(self):
        """Load the stacked ensemble model."""
        try:
            print("Loading stacked ensemble model...")
            self.ensemble = StackedEnsemblePredictor(self.models_dir)
            print("Model loaded successfully!")
        except Exception as e:
            raise RuntimeError(f"Failed to load stacked ensemble model: {e}")
    
    def _validate_input(self, data):
        """
        Validate input data format and features.
        
        Parameters:
        -----------
        data : dict or pandas.DataFrame
            Input data to validate
        
        Returns:
        --------
        pandas.DataFrame : Validated and formatted data
        """
        # Convert dict to DataFrame if needed
        if isinstance(data, dict):
            # Check if it's a single record or multiple records
            if all(isinstance(v, (list, tuple, np.ndarray)) for v in data.values()):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data])
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            raise ValueError("Input data must be a dictionary or pandas DataFrame")
        
        # Check for required features
        missing_features = set(self.required_features) - set(df.columns)
        if missing_features:
            raise ValueError(f"Missing required features: {missing_features}")
        
        # Reorder columns to match expected order
        df = df[self.required_features]
        
        # Validate data types
        numeric_features = ['Age', 'Income', 'Credit History Length', 
                          'Number of Existing Loans', 'LTV Ratio']
        
        for feat in numeric_features:
            if not pd.api.types.is_numeric_dtype(df[feat]):
                try:
                    df[feat] = pd.to_numeric(df[feat])
                except:
                    raise ValueError(f"Feature '{feat}' must be numeric")
        
        # Ensure categorical features are strings
        categorical_features = ['Existing Customer', 'State', 'City', 
                               'Employment Profile', 'Occupation']
        
        for feat in categorical_features:
            df[feat] = df[feat].astype(str)
        
        return df
    
    def predict(self, data, return_base_predictions=False):
        """
        Predict credit score for given input data.
        
        Parameters:
        -----------
        data : dict or pandas.DataFrame
            Input data containing all required features:
            - Age: int (years)
            - Income: float (annual income)
            - Credit History Length: int (years)
            - Number of Existing Loans: int
            - Existing Customer: str ('Yes' or 'No')
            - State: str
            - City: str
            - LTV Ratio: float (0-1)
            - Employment Profile: str
            - Occupation: str
        
        return_base_predictions : bool, default=False
            If True, also return predictions from individual base models
        
        Returns:
        --------
        dict : Prediction results
            {
                'prediction': float (ensemble prediction),
                'base_predictions': dict (if return_base_predictions=True)
            }
        
        Example:
        --------
        >>> predictor = CreditScorePredictor()
        >>> data = {'Age': 45, 'Income': 75000, ...}
        >>> result = predictor.predict(data)
        >>> print(f"Credit Score: {result['prediction']:.0f}")
        """
        # Validate input
        df = self._validate_input(data)
        
        # Get predictions
        if return_base_predictions:
            all_preds = self.ensemble.predict_with_base_models(df)
            return {
                'prediction': all_preds['ensemble'][0] if len(df) == 1 else all_preds['ensemble'],
                'base_predictions': {
                    'random_forest': all_preds['random_forest'][0] if len(df) == 1 else all_preds['random_forest'],
                    'lightgbm': all_preds['lightgbm'][0] if len(df) == 1 else all_preds['lightgbm'],
                    'tab_transformer': all_preds['tab_transformer'][0] if len(df) == 1 else all_preds['tab_transformer']
                }
            }
        else:
            predictions = self.ensemble.predict(df)
            return {
                'prediction': predictions[0] if len(df) == 1 else predictions
            }
    
    def predict_batch(self, data):
        """
        Predict credit scores for multiple records.
        
        Parameters:
        -----------
        data : pandas.DataFrame or list of dict
            Multiple records to predict
        
        Returns:
        --------
        numpy.ndarray : Array of predictions
        
        Example:
        --------
        >>> predictor = CreditScorePredictor()
        >>> data = pd.DataFrame([{...}, {...}, {...}])
        >>> predictions = predictor.predict_batch(data)
        """
        # Convert list of dicts to DataFrame if needed
        if isinstance(data, list):
            data = pd.DataFrame(data)
        
        # Validate input
        df = self._validate_input(data)
        
        # Get predictions
        predictions = self.ensemble.predict(df)
        
        return predictions
    
    def explain_prediction_shap(self, data, background_data=None, sample_size=100):
        """
        Get SHAP (SHapley Additive exPlanations) for predictions.
        Shows feature-level importance and contributions.
        
        Parameters:
        -----------
        data : dict or pandas.DataFrame
            Input data to explain
        background_data : pandas.DataFrame, optional
            Background dataset for SHAP. If None, uses a default background.
        sample_size : int, default=100
            Number of background samples to use for SHAP calculation
        
        Returns:
        --------
        dict : SHAP explanation results
            {
                'shap_values': numpy.ndarray (shape: n_samples x n_features),
                'feature_names': list,
                'feature_importance': pandas.DataFrame,
                'prediction': float or array
            }
        
        Example:
        --------
        >>> predictor = CreditScorePredictor()
        >>> data = {'Age': 45, 'Income': 75000, ...}
        >>> shap_exp = predictor.explain_prediction_shap(data)
        >>> print(shap_exp['feature_importance'])
        """
        # Validate input
        df = self._validate_input(data)
        
        # Prepare background data
        if background_data is None:
            if self._background_data is None:
                # Try to load a default background from the original dataset
                dataset_path = os.path.join(
                    os.path.dirname(self.models_dir),
                    'dataset',
                    'credit_data.csv'
                )
                if os.path.exists(dataset_path):
                    df_bg = pd.read_csv(dataset_path)
                    df_bg = df_bg[self.required_features]
                    if len(df_bg) > sample_size:
                        df_bg = df_bg.sample(n=sample_size, random_state=42)
                    self._background_data = self._validate_input(df_bg)
                    background_data = self._background_data
                else:
                    # Fallback to input data if dataset is unavailable
                    background_data = df
            else:
                background_data = self._background_data
        else:
            background_data = self._validate_input(background_data)
        
        # Get SHAP explanation
        print("\nCalculating SHAP explanations...")
        print("(This may take a moment...)")
        
        shap_values, explainer = self.ensemble.explain_with_shap(
            df, 
            background_data,
            sample_size=sample_size
        )
        
        # Get predictions
        predictions = self.ensemble.predict(df)
        
        # Create feature importance DataFrame
        feature_importance = pd.DataFrame({
            'Feature': df.columns,
            'SHAP_Importance': np.abs(shap_values).mean(axis=0)
        }).sort_values('SHAP_Importance', ascending=False)
        
        return {
            'shap_values': shap_values,
            'feature_names': df.columns.tolist(),
            'feature_importance': feature_importance,
            'prediction': predictions[0] if len(df) == 1 else predictions,
            'explainer': explainer
        }
    
    def explain_prediction_lime(self, data, training_data=None, num_features=10):
        """
        Get LIME (Local Interpretable Model-agnostic Explanations) for a prediction.
        Provides easy-to-understand local explanations.
        
        Parameters:
        -----------
        data : dict or pandas.DataFrame
            Single record to explain (if DataFrame, uses first row)
        training_data : pandas.DataFrame, optional
            Training data for LIME reference. If None, uses input data.
        num_features : int, default=10
            Number of top features to include in explanation
        
        Returns:
        --------
        dict : LIME explanation results
            {
                'explanation': lime.Explanation object,
                'feature_contributions': pandas.DataFrame,
                'prediction': float
            }
        
        Example:
        --------
        >>> predictor = CreditScorePredictor()
        >>> data = {'Age': 45, 'Income': 75000, ...}
        >>> lime_exp = predictor.explain_prediction_lime(data)
        >>> print(lime_exp['feature_contributions'])
        """
        # Validate input
        df = self._validate_input(data)
        
        # Prepare training data
        if training_data is None:
            if self._training_data is None:
                # Use the input data as training reference
                training_data = df
            else:
                training_data = self._training_data
        else:
            training_data = self._validate_input(training_data)
        
        # Get LIME explanation (only for first sample)
        print("\nCalculating LIME explanation...")
        
        lime_exp = self.ensemble.explain_with_lime(
            df,
            training_data,
            sample_idx=0,
            num_features=num_features
        )
        
        # Get prediction
        predictions = self.ensemble.predict(df.iloc[[0]])
        
        # Extract feature contributions
        lime_list = lime_exp.as_list()
        feature_contributions = pd.DataFrame(
            lime_list, 
            columns=['Feature_Rule', 'Contribution']
        )
        
        return {
            'explanation': lime_exp,
            'feature_contributions': feature_contributions,
            'prediction': predictions[0]
        }

    def get_credit_improvement_advice(self, data, shap_explanation=None, api_key=None,
                                      model_name='gemini-2.5-flash',
                                      score_threshold=650, top_k=5):
        """
        Send prediction data and explanations to Gemini and get advice for improving
        credit score when the prediction is below a threshold.

        Parameters:
        -----------
        data : dict or pandas.DataFrame
            Input data to explain
        shap_explanation : dict, optional
            Precomputed SHAP explanation dict from explain_prediction_shap
        api_key : str
            Google Generative AI API key
        model_name : str, default='gemini-1.5-flash'
            Gemini model name
        score_threshold : int, default=650
            Threshold below which advice is requested
        top_k : int, default=5
            Number of top SHAP contributors to include

        Returns:
        --------
        dict : Advice response
        """
        if not api_key:
            raise ValueError("api_key is required to call Gemini")

        df = self._validate_input(data)
        prediction = self.ensemble.predict(df)[0]

        if shap_explanation is None:
            shap_explanation = self.explain_prediction_shap(df, sample_size=100)

        shap_values = np.array(shap_explanation['shap_values'])
        feature_names = shap_explanation['feature_names']
        sample_shap = shap_values[0]

        contrib_df = pd.DataFrame({
            'feature': feature_names,
            'shap_value': sample_shap
        })
        top_negative = contrib_df.sort_values('shap_value').head(top_k)
        top_positive = contrib_df.sort_values('shap_value', ascending=False).head(top_k)

        payload = {
            'prediction': float(prediction),
            'score_threshold': int(score_threshold),
            'features': df.iloc[0].to_dict(),
            'top_negative_factors': top_negative.to_dict(orient='records'),
            'top_positive_factors': top_positive.to_dict(orient='records')
        }

        if prediction >= score_threshold:
            return {
                'prediction': float(prediction),
                'advice': 'Score is not poor. No improvement advice requested.',
                'payload_sent': payload
            }

        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        prompt = (
            "You are a credit risk advisor. Given the prediction and SHAP factors, "
            "suggest 3-7 practical actions to improve the credit score. "
            "Prioritize actionable steps and reference the negative SHAP factors. "
            "Keep the response concise and avoid legal or financial guarantees.\n\n"
            f"Input data: {payload['features']}\n"
            f"Predicted score: {payload['prediction']} (threshold {payload['score_threshold']})\n"
            f"Top negative factors: {payload['top_negative_factors']}\n"
            f"Top positive factors: {payload['top_positive_factors']}\n"
        )

        response = model.generate_content(prompt)
        return {
            'prediction': float(prediction),
            'advice': response.text if hasattr(response, 'text') else str(response),
            'payload_sent': payload
        }
    
    def explain_meta_learner(self, data):
        """
        Explain how the base models contribute to the ensemble prediction.
        
        Parameters:
        -----------
        data : dict or pandas.DataFrame
            Input data to explain
        
        Returns:
        --------
        dict : Meta-learner explanation
            {
                'contributions': pandas.DataFrame,
                'base_predictions': dict,
                'weights': dict,
                'prediction': float or array
            }
        
        Example:
        --------
        >>> predictor = CreditScorePredictor()
        >>> data = {'Age': 45, 'Income': 75000, ...}
        >>> meta_exp = predictor.explain_meta_learner(data)
        >>> print(meta_exp['contributions'])
        """
        # Validate input
        df = self._validate_input(data)
        
        # Get meta-learner explanation
        contributions_df = self.ensemble.explain_meta_learner(df)
        
        # Get base predictions
        all_preds = self.ensemble.predict_with_base_models(df)
        
        # Get weights
        weights = self.ensemble.get_model_weights()
        
        return {
            'contributions': contributions_df,
            'base_predictions': all_preds,
            'weights': weights,
            'prediction': all_preds['ensemble'][0] if len(df) == 1 else all_preds['ensemble']
        }
    
    def get_detailed_explanation(self, data):
        """
        Get a comprehensive explanation including base models, meta-learner, and features.
        
        Parameters:
        -----------
        data : dict or pandas.DataFrame
            Single record to explain (if DataFrame, uses first row)
        
        Returns:
        --------
        dict : Comprehensive explanation
        
        Example:
        --------
        >>> predictor = CreditScorePredictor()
        >>> data = {'Age': 45, 'Income': 75000, ...}
        >>> detailed = predictor.get_detailed_explanation(data)
        """
        # Validate input
        df = self._validate_input(data)
        
        # Get detailed explanation (only for first sample)
        explanation = self.ensemble.explain_sample_detailed(df, sample_idx=0)
        
        return explanation
    
    def set_background_data(self, data):
        """
        Set background data for SHAP explanations.
        
        Parameters:
        -----------
        data : pandas.DataFrame
            Background dataset to use for SHAP
        """
        self._background_data = self._validate_input(data)
        print(f"Background data set ({len(self._background_data)} samples)")
    
    def set_training_data(self, data):
        """
        Set training data for LIME explanations.
        
        Parameters:
        -----------
        data : pandas.DataFrame
            Training dataset to use for LIME
        """
        self._training_data = self._validate_input(data)
        print(f"Training data set ({len(self._training_data)} samples)")
    
    def get_model_info(self):
        """
        Get information about the loaded model.
        
        Returns:
        --------
        dict : Model information
        """
        weights = self.ensemble.get_model_weights()
        
        return {
            'model_type': 'Stacked Ensemble',
            'base_models': ['Random Forest', 'LightGBM', 'TabTransformer'],
            'meta_learner': 'Linear Regression',
            'weights': weights,
            'required_features': self.required_features,
            'models_directory': self.models_dir
        }
    
    def validate_data_format(self, data):
        """
        Validate data format without making predictions.
        Useful for checking data before batch processing.
        
        Parameters:
        -----------
        data : dict or pandas.DataFrame
            Data to validate
        
        Returns:
        --------
        dict : Validation result
            {
                'valid': bool,
                'message': str,
                'validated_data': pandas.DataFrame (if valid)
            }
        
        Example:
        --------
        >>> predictor = CreditScorePredictor()
        >>> result = predictor.validate_data_format(data)
        >>> if result['valid']:
        ...     print("Data is valid!")
        ... else:
        ...     print(f"Validation error: {result['message']}")
        """
        try:
            df = self._validate_input(data)
            return {
                'valid': True,
                'message': 'Data validation successful',
                'validated_data': df
            }
        except Exception as e:
            return {
                'valid': False,
                'message': str(e),
                'validated_data': None
            }


# Convenience function for quick predictions
def predict_credit_score(data, return_explanations=False):
    """
    Quick prediction function without creating predictor object.
    
    Parameters:
    -----------
    data : dict
        Input data with all required features
    return_explanations : bool, default=False
        If True, also returns SHAP and LIME explanations
    
    Returns:
    --------
    dict : Prediction result (and explanations if requested)
    
    Example:
    --------
    >>> from Utilities.prediction import predict_credit_score
    >>> 
    >>> data = {
    ...     'Age': 45, 'Income': 75000,
    ...     'Credit History Length': 15,
    ...     'Number of Existing Loans': 2,
    ...     'Existing Customer': 'Yes',
    ...     'State': 'Maharashtra', 'City': 'Mumbai',
    ...     'LTV Ratio': 0.7,
    ...     'Employment Profile': 'Salaried',
    ...     'Occupation': 'Engineer'
    ... }
    >>> 
    >>> result = predict_credit_score(data)
    >>> print(f"Predicted Credit Score: {result['prediction']:.0f}")
    """
    predictor = CreditScorePredictor()
    
    result = predictor.predict(data, return_base_predictions=True)
    
    if return_explanations:
        # Get SHAP explanation
        shap_exp = predictor.explain_prediction_shap(data, sample_size=50)
        
        # Get LIME explanation
        lime_exp = predictor.explain_prediction_lime(data, num_features=10)
        
        result['shap_explanation'] = shap_exp
        result['lime_explanation'] = lime_exp
    
    return result
