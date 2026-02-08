"""
Demonstration of SHAP and LIME explanations for the Stacked Ensemble model.
"""
import pandas as pd
import sys
import os

# Add the models directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inference import StackedEnsemblePredictor

print("="*70)
print("STACKED ENSEMBLE MODEL - EXPLAINABILITY DEMONSTRATION")
print("="*70)

# Create test data
test_data = pd.DataFrame({
    'Age': [35, 45, 50, 28, 55],
    'Income': [50000, 75000, 100000, 40000, 90000],
    'Credit History Length': [5, 15, 20, 2, 18],
    'Number of Existing Loans': [1, 2, 3, 0, 2],
    'Existing Customer': ['Yes', 'No', 'Yes', 'No', 'Yes'],
    'State': ['Delhi', 'Maharashtra', 'Karnataka', 'Tamil Nadu', 'West Bengal'],
    'City': ['New Delhi', 'Mumbai', 'Bengaluru', 'Chennai', 'Kolkata'],
    'LTV Ratio': [0.8, 0.7, 0.75, 0.85, 0.65],
    'Employment Profile': ['Salaried', 'Self Employed', 'Salaried', 'Salaried', 'Self Employed'],
    'Occupation': ['Engineer', 'Business', 'Manager', 'Teacher', 'Architect']
})

print("\nTest Data (5 samples):")
print(test_data)

try:
    # Initialize ensemble predictor
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ensemble = StackedEnsemblePredictor(script_dir)
    
    # ========================================================================
    # 1. META-LEARNER EXPLANATION
    # ========================================================================
    print("\n\n" + "="*70)
    print("EXPLANATION TYPE 1: META-LEARNER LEVEL")
    print("="*70)
    print("Shows how each base model contributes to the final prediction")
    
    meta_explanation = ensemble.explain_meta_learner(test_data)
    
    # ========================================================================
    # 2. DETAILED SAMPLE EXPLANATION
    # ========================================================================
    print("\n\n" + "="*70)
    print("EXPLANATION TYPE 2: DETAILED SINGLE SAMPLE")
    print("="*70)
    print("Complete breakdown of how a prediction is formed")
    
    detailed_exp = ensemble.explain_sample_detailed(test_data, sample_idx=1)
    
    # ========================================================================
    # 3. SHAP EXPLANATIONS
    # ========================================================================
    print("\n\n" + "="*70)
    print("EXPLANATION TYPE 3: SHAP ANALYSIS")
    print("="*70)
    print("Feature-level explanations showing which features drive predictions")
    print("Note: This may take a minute...")
    
    # Use smaller sample for demo
    samples_to_explain = test_data.head(3)
    background_samples = test_data
    
    shap_values, shap_explainer = ensemble.explain_with_shap(
        samples_to_explain, 
        background_samples,
        sample_size=50  # Smaller for faster computation
    )
    
    print("\nSHAP values calculated successfully!")
    print(f"Shape: {shap_values.shape}")
    
    # Show SHAP values for first sample
    print("\nSHAP Values for Sample 1:")
    shap_df = pd.DataFrame({
        'Feature': samples_to_explain.columns,
        'SHAP Value': shap_values[0]
    }).sort_values('SHAP Value', key=abs, ascending=False)
    print(shap_df.head(10).to_string(index=False))
    
    # ========================================================================
    # 4. LIME EXPLANATIONS
    # ========================================================================
    print("\n\n" + "="*70)
    print("EXPLANATION TYPE 4: LIME ANALYSIS")
    print("="*70)
    print("Local interpretable explanations for individual predictions")
    
    lime_exp = ensemble.explain_with_lime(
        test_data.head(3), 
        test_data,
        sample_idx=0,
        num_features=10
    )
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n\n" + "="*70)
    print("SUMMARY - EXPLANATION METHODS AVAILABLE")
    print("="*70)
    print("""
1. META-LEARNER EXPLANATION
   - Shows which base model predictions are most influential
   - Reveals how the linear regression combines base models
   - Use: ensemble.explain_meta_learner(data)

2. DETAILED SAMPLE EXPLANATION  
   - Complete breakdown for a single prediction
   - Shows base predictions, contributions, and features
   - Use: ensemble.explain_sample_detailed(data, sample_idx=0)

3. SHAP EXPLANATIONS
   - Feature-level importance for ensemble predictions
   - Shows how each input feature affects the final output
   - Accounts for feature interactions
   - Use: ensemble.explain_with_shap(samples, background)

4. LIME EXPLANATIONS
   - Local linear approximation of model behavior
   - Easy to interpret feature contributions
   - Works well for individual predictions
   - Use: ensemble.explain_with_lime(sample, training_data, sample_idx=0)

All methods are production-ready and handle unknown categorical values.
    """)
    
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETED SUCCESSFULLY!")
    print("="*70)
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
