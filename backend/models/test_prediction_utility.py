"""
Demonstration of the CreditScorePredictor Utility
==================================================
Shows how to use the prediction utility for credit score predictions
and explanations.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Utilities import CreditScorePredictor
import pandas as pd

print("="*70)
print("CREDIT SCORE PREDICTION UTILITY - DEMONSTRATION")
print("="*70)

# ============================================================================
# EXAMPLE 1: Single Prediction
# ============================================================================
print("\n[1] SINGLE PREDICTION")
print("-" * 70)

# Create a single applicant's data
applicant = {
    'Age': 45,
    'Income': 75000,
    'Credit History Length': 15,
    'Number of Existing Loans': 2,
    'Existing Customer': 'No',
    'State': 'Maharashtra',
    'City': 'Mumbai',
    'LTV Ratio': 0.7,
    'Employment Profile': 'Salaried',
    'Occupation': 'Engineer'
}

# Initialize predictor
predictor = CreditScorePredictor()

# Make prediction
result = predictor.predict(applicant)
print(f"\nApplicant: 45 years old, Income: ₹75,000, Location: Mumbai")
print(f"Predicted Credit Score: {result['prediction']:.0f}")

# Get predictions from all models
result_detailed = predictor.predict(applicant, return_base_predictions=True)
print(f"\nBase Model Predictions:")
print(f"  Random Forest:  {result_detailed['base_predictions']['random_forest']:.0f}")
print(f"  LightGBM:       {result_detailed['base_predictions']['lightgbm']:.0f}")
print(f"  TabTransformer: {result_detailed['base_predictions']['tab_transformer']:.0f}")
print(f"  ----------------")
print(f"  Ensemble:       {result_detailed['prediction']:.0f}")

# ============================================================================
# EXAMPLE 2: Batch Predictions
# ============================================================================
print("\n\n[2] BATCH PREDICTIONS")
print("-" * 70)

# Create multiple applicants
applicants = pd.DataFrame([
    {
        'Age': 35, 'Income': 50000, 'Credit History Length': 5,
        'Number of Existing Loans': 1, 'Existing Customer': 'Yes',
        'State': 'Delhi', 'City': 'New Delhi', 'LTV Ratio': 0.8,
        'Employment Profile': 'Salaried', 'Occupation': 'Teacher'
    },
    {
        'Age': 50, 'Income': 100000, 'Credit History Length': 20,
        'Number of Existing Loans': 3, 'Existing Customer': 'Yes',
        'State': 'Karnataka', 'City': 'Bengaluru', 'LTV Ratio': 0.75,
        'Employment Profile': 'Self Employed', 'Occupation': 'Business'
    },
    {
        'Age': 28, 'Income': 40000, 'Credit History Length': 2,
        'Number of Existing Loans': 0, 'Existing Customer': 'No',
        'State': 'Tamil Nadu', 'City': 'Chennai', 'LTV Ratio': 0.85,
        'Employment Profile': 'Salaried', 'Occupation': 'Engineer'
    }
])

predictions = predictor.predict_batch(applicants)

print("\nBatch Prediction Results:")
for i, pred in enumerate(predictions):
    print(f"  Applicant {i+1}: {pred:.0f}")

# ============================================================================
# EXAMPLE 3: SHAP Explanations
# ============================================================================
print("\n\n[3] SHAP EXPLANATIONS")
print("-" * 70)
print("Understanding which features drive the prediction...")

# Use the first applicant
shap_result = predictor.explain_prediction_shap(applicant, sample_size=50)

print(f"\nPredicted Score: {shap_result['prediction']:.0f}")
print("\nFeature Importance (SHAP):")
print(shap_result['feature_importance'].head(10).to_string(index=False))

print("\nFeature Contributions (SHAP values for this prediction):")
for i, (feat, val) in enumerate(zip(shap_result['feature_names'], 
                                    shap_result['shap_values'][0])):
    direction = "↑" if val > 0 else "↓"
    print(f"  {feat:.<35} {val:>8.2f} {direction}")

# ============================================================================
# EXAMPLE 4: LIME Explanations
# ============================================================================
print("\n\n[4] LIME EXPLANATIONS")
print("-" * 70)
print("Local interpretable explanation for the prediction...")

# Set training data for better LIME explanations
predictor.set_training_data(applicants)

lime_result = predictor.explain_prediction_lime(applicant, num_features=10)

print(f"\nPredicted Score: {lime_result['prediction']:.0f}")
print("\nFeature Contributions (LIME):")
print(lime_result['feature_contributions'].to_string(index=False))

# ============================================================================
# EXAMPLE 5: Meta-Learner Explanation
# ============================================================================
print("\n\n[5] META-LEARNER EXPLANATION")
print("-" * 70)
print("Understanding how base models contribute to the ensemble...")

meta_result = predictor.explain_meta_learner(applicant)

print("\nBase Model Weights:")
weights = meta_result['weights']
print(f"  Random Forest:  {weights['random_forest']:>8.3f}")
print(f"  LightGBM:       {weights['lightgbm']:>8.3f}")
print(f"  TabTransformer: {weights['tab_transformer']:>8.6f}")
print(f"  Intercept:      {weights['intercept']:>8.3f}")

print("\nContributions to Final Prediction:")
print(meta_result['contributions'].to_string(index=False))

# ============================================================================
# EXAMPLE 6: Detailed Comprehensive Explanation
# ============================================================================
print("\n\n[6] COMPREHENSIVE DETAILED EXPLANATION")
print("-" * 70)

detailed = predictor.get_detailed_explanation(applicant)

print(f"\nSample Features:")
for key, value in detailed['features'].items():
    print(f"  {key:.<35} {value}")

print(f"\nEnsemble Prediction: {detailed['base_predictions']['ensemble'][0]:.0f}")

# ============================================================================
# EXAMPLE 7: Data Validation
# ============================================================================
print("\n\n[7] DATA VALIDATION")
print("-" * 70)

# Valid data
valid_data = {'Age': 30, 'Income': 60000, 'Credit History Length': 10,
              'Number of Existing Loans': 1, 'Existing Customer': 'Yes',
              'State': 'Delhi', 'City': 'New Delhi', 'LTV Ratio': 0.75,
              'Employment Profile': 'Salaried', 'Occupation': 'Doctor'}

validation = predictor.validate_data_format(valid_data)
print(f"Valid data check: {validation['valid']}")
print(f"Message: {validation['message']}")

# Invalid data (missing required field)
invalid_data = {'Age': 30, 'Income': 60000}  # Missing other fields

validation = predictor.validate_data_format(invalid_data)
print(f"\nInvalid data check: {validation['valid']}")
print(f"Message: {validation['message']}")

# ============================================================================
# EXAMPLE 8: Model Information
# ============================================================================
print("\n\n[8] MODEL INFORMATION")
print("-" * 70)

info = predictor.get_model_info()
print(f"\nModel Type: {info['model_type']}")
print(f"Base Models: {', '.join(info['base_models'])}")
print(f"Meta-Learner: {info['meta_learner']}")
print(f"\nRequired Features ({len(info['required_features'])}):")
for i, feat in enumerate(info['required_features'], 1):
    print(f"  {i:>2}. {feat}")

# ============================================================================
# EXAMPLE 9: Quick Prediction Function
# ============================================================================
print("\n\n[9] QUICK PREDICTION FUNCTION")
print("-" * 70)

from Utilities.prediction import predict_credit_score

quick_applicant = {
    'Age': 40, 'Income': 85000, 'Credit History Length': 12,
    'Number of Existing Loans': 2, 'Existing Customer': 'Yes',
    'State': 'West Bengal', 'City': 'Kolkata', 'LTV Ratio': 0.65,
    'Employment Profile': 'Salaried', 'Occupation': 'Manager'
}

quick_result = predict_credit_score(quick_applicant)
print(f"\nQuick Prediction: {quick_result['prediction']:.0f}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n\n" + "="*70)
print("SUMMARY - AVAILABLE METHODS")
print("="*70)
print("""
# Initialize predictor
predictor = CreditScorePredictor()

# 1. Simple prediction
result = predictor.predict(data)

# 2. Prediction with base models
result = predictor.predict(data, return_base_predictions=True)

# 3. Batch predictions
predictions = predictor.predict_batch(dataframe)

# 4. SHAP explanations
shap_exp = predictor.explain_prediction_shap(data)

# 5. LIME explanations
lime_exp = predictor.explain_prediction_lime(data)

# 6. Meta-learner explanation
meta_exp = predictor.explain_meta_learner(data)

# 7. Detailed comprehensive explanation
detailed = predictor.get_detailed_explanation(data)

# 8. Validate data format
validation = predictor.validate_data_format(data)

# 9. Get model information
info = predictor.get_model_info()

# 10. Quick prediction without object
from Utilities.prediction import predict_credit_score
result = predict_credit_score(data)
""")

print("="*70)
print("DEMONSTRATION COMPLETED!")
print("="*70)
