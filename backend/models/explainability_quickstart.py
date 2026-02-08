"""
Quick Reference: Using Explainability Features
===============================================
This script provides quick examples of all explanation methods.
"""

import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inference import StackedEnsemblePredictor

# Sample data
sample_data = pd.DataFrame({
    'Age': [45],
    'Income': [75000],
    'Credit History Length': [15],
    'Number of Existing Loans': [2],
    'Existing Customer': ['No'],
    'State': ['Maharashtra'],
    'City': ['Mumbai'],
    'LTV Ratio': [0.7],
    'Employment Profile': ['Self Employed'],
    'Occupation': ['Business']
})

print("="*70)
print("STACKED ENSEMBLE - EXPLAINABILITY QUICK REFERENCE")
print("="*70)
print("\nInput:")
print(sample_data.T)

# Initialize
ensemble = StackedEnsemblePredictor()

# ==================================================
# METHOD 1: Quick prediction with all models
# ==================================================
print("\n" + "="*70)
print("METHOD 1: Predictions from All Models")
print("="*70)

preds = ensemble.predict_with_base_models(sample_data)
print(f"""
Random Forest:  {preds['random_forest'][0]:.2f}
LightGBM:       {preds['lightgbm'][0]:.2f}
TabTransformer: {preds['tab_transformer'][0]:.2f}
----------------
ENSEMBLE:       {preds['ensemble'][0]:.2f}
""")

# ==================================================
# METHOD 2: Understanding the ensemble combination
# ==================================================
print("="*70)
print("METHOD 2: Meta-Learner Weights")
print("="*70)

weights = ensemble.get_model_weights()
print(f"""
How the ensemble combines predictions:

Ensemble = (RF × {weights['random_forest']:.2f}) + 
           (LGBM × {weights['lightgbm']:.2f}) + 
           (Transformer × {weights['tab_transformer']:.4f}) + 
           {weights['intercept']:.2f}

Actual calculation:
= ({preds['random_forest'][0]:.2f} × {weights['random_forest']:.2f}) + 
  ({preds['lightgbm'][0]:.2f} × {weights['lightgbm']:.2f}) + 
  ({preds['tab_transformer'][0]:.2f} × {weights['tab_transformer']:.4f}) + 
  {weights['intercept']:.2f}
= {preds['ensemble'][0]:.2f}
""")

# ==================================================
# METHOD 3: Feature importance (SHAP)
# ==================================================
print("="*70)
print("METHOD 3: SHAP Feature Importance")
print("="*70)
print("Calculating... (this may take 30 seconds)")

shap_values, _ = ensemble.explain_with_shap(
    sample_data, 
    sample_data,
    sample_size=20  # Small sample for quick demo
)

print("\nFeature contributions to this prediction:")
for i, (feat, val) in enumerate(zip(sample_data.columns, shap_values[0])):
    direction = "↑" if val > 0 else "↓"
    print(f"  {feat:.<30} {val:>8.2f} {direction}")

# ==================================================
# SUMMARY
# ==================================================
print("\n" + "="*70)
print("USAGE SUMMARY")
print("="*70)
print("""
# Get predictions from all models
preds = ensemble.predict_with_base_models(data)

# See meta-learner weights
weights = ensemble.get_model_weights()

# Get detailed explanation for one sample
detailed = ensemble.explain_sample_detailed(data, sample_idx=0)

# SHAP feature importance
shap_vals, explainer = ensemble.explain_with_shap(data, background)

# LIME local explanation
lime_exp = ensemble.explain_with_lime(data, training_data, sample_idx=0)

See EXPLAINABILITY_GUIDE.md for complete documentation.
""")

print("="*70)
print("Quick reference completed!")
print("="*70)
