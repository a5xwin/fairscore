"""
Simple test script for the Stacked Ensemble model.
"""
import pandas as pd
import sys
import os

# Add the models directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inference import StackedEnsemblePredictor

print("="*60)
print("TESTING STACKED ENSEMBLE PREDICTOR")
print("="*60)

# Create test data
test_data = pd.DataFrame({
    'Age': [35, 45, 50],
    'Income': [50000, 75000, 100000],
    'Credit History Length': [5, 15, 20],
    'Number of Existing Loans': [1, 2, 3],
    'Existing Customer': ['Yes', 'No', 'Yes'],
    'State': ['Delhi', 'Maharashtra', 'Karnataka'],
    'City': ['New Delhi', 'Mumbai', 'Bengaluru'],
    'LTV Ratio': [0.8, 0.7, 0.75],
    'Employment Profile': ['Employed', 'Self-Employed', 'Employed'],
    'Occupation': ['Engineer', 'Doctor', 'Manager']
})

print("\nTest Data:")
print(test_data)
print("\n" + "="*60)

try:
    # Initialize ensemble predictor
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ensemble_predictor = StackedEnsemblePredictor(script_dir)
    
    # Get predictions from all models
    print("\nGetting predictions from all models...")
    all_predictions = ensemble_predictor.predict_with_base_models(test_data)
    
    print("\n" + "="*60)
    print("PREDICTIONS FROM ALL MODELS")
    print("="*60)
    
    comparison_df = pd.DataFrame({
        'Sample': range(1, len(test_data) + 1),
        'Random Forest': all_predictions['random_forest'],
        'LightGBM': all_predictions['lightgbm'],
        'TabTransformer': all_predictions['tab_transformer'],
        'Ensemble': all_predictions['ensemble']
    })
    print("\n" + comparison_df.to_string(index=False))
    
    # Show model weights
    print("\n" + "="*60)
    print("META-LEARNER MODEL WEIGHTS")
    print("="*60)
    weights = ensemble_predictor.get_model_weights()
    weights_df = pd.DataFrame({
        'Model': ['Random Forest', 'LightGBM', 'TabTransformer', 'Intercept'],
        'Weight': [weights['random_forest'], weights['lightgbm'], 
                  weights['tab_transformer'], weights['intercept']]
    })
    print("\n" + weights_df.to_string(index=False))
    
    print("\n" + "="*60)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("="*60)
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
