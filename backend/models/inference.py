"""
Prediction utilities that safely handle new data with unknown categorical values.
Use these functions for inference with production data.
"""

import pandas as pd
import numpy as np
import joblib
import os
from pathlib import Path


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
            known_values = set(encoder.classes_)
            unknown_mask = ~df_encoded[col].astype(str).isin(known_values)
            
            # Transform known values
            encoded_values = encoder.transform(df_encoded[col].astype(str))
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
            'Employment Profile': ['Employed', 'Self-Employed', 'Employed'],
            'Occupation': ['Engineer', 'Doctor', 'Manager']
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
        
    else:
        print("❌ Missing model files. Please run preprocessing.py and model training scripts first.")
        print(f"   Looking for:")
        print(f"   - {model_path}")
        print(f"   - {encoders_path}")
        print(f"   - {scaler_path}")
