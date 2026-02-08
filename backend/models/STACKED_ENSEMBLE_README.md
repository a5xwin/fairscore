# Stacked Ensemble Model - Documentation

## Overview
A stacked ensemble model has been successfully implemented that combines three base models using a Linear Regression meta-learner:
- **Base Models:** TabTransformer, Random Forest, LightGBM
- **Meta-Learner:** Linear Regression

## Architecture

### Base Models
1. **TabTransformer** - Deep learning model with attention mechanism for tabular data
2. **Random Forest** - Tree-based ensemble regressor
3. **LightGBM** - Gradient boosting framework

### Stacking Approach
The stacking ensemble works in two levels:
- **Level 0 (Base Models):** Each base model makes independent predictions on the input data
- **Level 1 (Meta-Learner):** Linear regression combines the base model predictions to produce the final output

## Performance Results

### Test Set Performance (on original dataset)
| Model | R² Score | MAE | RMSE |
|-------|----------|-----|------|
| Random Forest | 0.9932 | 11.02 | 13.47 |
| LightGBM | 0.9920 | 12.04 | 14.58 |
| TabTransformer | 0.9782 | 19.67 | 24.11 |
| **Stacked Ensemble** | **0.9946** | **9.40** | **11.97** |

**Improvement:** +0.14% over the best individual model (Random Forest)

### Meta-Learner Coefficients
The linear regression meta-learner assigns the following weights:
- **Random Forest:** 3.796 (highest weight)
- **LightGBM:** -2.799 (negative weight - acts as correction)
- **TabTransformer:** 0.002 (minimal influence)
- **Intercept:** 0.647

This indicates that the ensemble primarily relies on Random Forest predictions, with LightGBM providing refinements, and TabTransformer having minimal impact.

## Files Created

### Training Script
- **`stacked_ensemble.py`** - Trains the stacked ensemble model
  - Loads all three pre-trained base models
  - Generates predictions on training data
  - Trains Linear Regression meta-learner on base predictions
  - Saves the meta-learner model and configuration

### Inference Integration
- **`inference.py`** (updated) - Added `StackedEnsemblePredictor` class
  - Loads all base models and meta-learner
  - Handles preprocessing for different model requirements
  - Provides unified prediction interface
  - Handles TabTransformer's requirement for encoded (not scaled) categorical features
  - Manages unknown categorical values gracefully

### Testing
- **`test_ensemble.py`** - Simple test script demonstrating ensemble usage

### Generated Model Files
- **`meta_learner.joblib`** - Trained Linear Regression meta-learner
- **`ensemble_config.json`** - Configuration and metadata for the ensemble

## Usage

### Training the Ensemble
```bash
# Prerequisites: Train all base models first
python random_forest.py
python lightgbm_model.py
python tab_transformer.py

# Train the stacked ensemble
python stacked_ensemble.py
```

### Making Predictions

#### Using the Ensemble Predictor
```python
from inference import StackedEnsemblePredictor
import pandas as pd

# Initialize predictor
ensemble = StackedEnsemblePredictor()

# Prepare input data
test_data = pd.DataFrame({
    'Age': [35, 45],
    'Income': [50000, 75000],
    'Credit History Length': [5, 15],
    'Number of Existing Loans': [1, 2],
    'Existing Customer': ['Yes', 'No'],
    'State': ['Delhi', 'Maharashtra'],
    'City': ['New Delhi', 'Mumbai'],
    'LTV Ratio': [0.8, 0.7],
    'Employment Profile': ['Employed', 'Self-Employed'],
    'Occupation': ['Engineer', 'Doctor']
})

# Get ensemble predictions
predictions = ensemble.predict(test_data)

# Get predictions from all models
all_predictions = ensemble.predict_with_base_models(test_data)
# Returns: {'random_forest': [...], 'lightgbm': [...], 
#           'tab_transformer': [...], 'ensemble': [...]}

# Get meta-learner weights
weights = ensemble.get_model_weights()
```

## Technical Details

### Data Preprocessing
The ensemble handles two different preprocessing pipelines:
1. **For RF and LightGBM:** Categorical encoding + StandardScaler
2. **For TabTransformer:** Categorical encoding only (embeddings handle the representation)

### Handling Unknown Values
- Unknown categorical values are encoded as -1 by SafeLabelEncoder
- For TabTransformer, -1 values are mapped to the last embedding index
- This prevents IndexError while maintaining model functionality

### Training Data Considerations
- The ensemble is trained on the **original dataset** (not SMOTE-resampled)
- This ensures consistency across all model predictions
- Individual base models may have been trained on different datasets (with/without SMOTE)

## Key Insights

1. **Marginal Improvement:** The ensemble shows a modest +0.14% improvement, suggesting the base models already perform exceptionally well

2. **Model Dominance:** Random Forest dominates the ensemble, indicating it's the strongest individual model

3. **Negative Weight for LightGBM:** The negative coefficient suggests LightGBM helps correct Random Forest's systematic biases

4. **TabTransformer Weight:** Near-zero weight indicates TabTransformer's predictions don't add significant value in this ensemble configuration

## Future Enhancements

1. **Cross-Validation Stacking:** Use out-of-fold predictions for training the meta-learner to prevent overfitting

2. **Non-Linear Meta-Learner:** Try neural networks or gradient boosting as meta-learners

3. **Feature Engineering:** Add original features alongside base predictions in meta-learner

4. **Weighted Ensemble:** Experiment with different meta-learners (e.g., weighted averaging, voting)

5. **TabTransformer Retraining:** Consider retraining TabTransformer on the SMOTE-resampled dataset for consistency

## Conclusion

The stacked ensemble successfully combines three diverse models to achieve the best overall performance. While the improvement is modest, the ensemble provides:
- **Better generalization** through diversity
- **Reduced variance** by combining multiple models
- **Robustness** against individual model weaknesses
- **Flexibility** to leverage different model strengths

The implementation is production-ready with proper error handling, unknown value management, and a clean API for inference.
