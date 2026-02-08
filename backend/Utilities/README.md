# Credit Score Prediction Utility

## Overview
This module provides a clean, user-friendly interface for predicting credit scores using the stacked ensemble model. It includes built-in support for SHAP and LIME explanations with automatic data validation and preprocessing.

## Features

✅ **Simple Prediction Interface** - Easy-to-use methods for single and batch predictions  
✅ **Automatic Data Validation** - Validates input format and required features  
✅ **Preprocessing Built-in** - Handles encoding and scaling automatically  
✅ **SHAP Explanations** - Feature-level importance and contributions  
✅ **LIME Explanations** - Local interpretable explanations  
✅ **Meta-Learner Insights** - Understand base model contributions  
✅ **Production-Ready** - Comprehensive error handling and validation  

---

## Quick Start

### Installation
```python
from Utilities import CreditScorePredictor
```

### Basic Usage
```python
# Initialize predictor
predictor = CreditScorePredictor()

# Prepare data
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

# Make prediction
result = predictor.predict(applicant)
print(f"Predicted Credit Score: {result['prediction']:.0f}")
```

---

## Class: `CreditScorePredictor`

### Initialization
```python
predictor = CreditScorePredictor(models_dir=None)
```

**Parameters:**
- `models_dir` (str, optional): Directory containing trained models. Default: auto-detected

---

## Methods

### 1. `predict(data, return_base_predictions=False)`

Predict credit score for given input data.

**Parameters:**
- `data` (dict or DataFrame): Input data with all required features
- `return_base_predictions` (bool): If True, also returns individual base model predictions

**Returns:**
- `dict`: Prediction results
  ```python
  {
      'prediction': 439.80,  # Ensemble prediction
      'base_predictions': {  # Only if return_base_predictions=True
          'random_forest': 436.69,
          'lightgbm': 435.65,
          'tab_transformer': 438.63
      }
  }
  ```

**Example:**
```python
result = predictor.predict(applicant)
print(result['prediction'])  # 439.80

# With base predictions
result = predictor.predict(applicant, return_base_predictions=True)
print(result['base_predictions']['random_forest'])  # 436.69
```

---

### 2. `predict_batch(data)`

Predict credit scores for multiple records.

**Parameters:**
- `data` (DataFrame or list of dict): Multiple records to predict

**Returns:**
- `numpy.ndarray`: Array of predictions

**Example:**
```python
import pandas as pd

applicants = pd.DataFrame([
    {...},  # Applicant 1
    {...},  # Applicant 2
    {...}   # Applicant 3
])

predictions = predictor.predict_batch(applicants)
# array([385.17, 439.80, 500.64])
```

---

### 3. `explain_prediction_shap(data, background_data=None, sample_size=100)`

Get SHAP explanations showing feature-level importance.

**Parameters:**
- `data` (dict or DataFrame): Input data to explain
- `background_data` (DataFrame, optional): Background dataset for SHAP
- `sample_size` (int): Number of background samples to use

**Returns:**
- `dict`: SHAP explanation results
  ```python
  {
      'shap_values': array(...),           # SHAP values
      'feature_names': [...],              # Feature names
      'feature_importance': DataFrame,     # Importance ranking
      'prediction': 439.80,                # Prediction
      'explainer': KernelExplainer         # SHAP explainer object
  }
  ```

**Example:**
```python
shap_result = predictor.explain_prediction_shap(applicant, sample_size=50)

print(f"Prediction: {shap_result['prediction']:.0f}")
print("\nFeature Importance:")
print(shap_result['feature_importance'])

# Output:
#                   Feature  SHAP_Importance
# Number of Existing Loans            48.31
#                   Income             2.17
#                    State             1.92
```

---

### 4. `explain_prediction_lime(data, training_data=None, num_features=10)`

Get LIME explanations for a single prediction.

**Parameters:**
- `data` (dict or DataFrame): Single record to explain
- `training_data` (DataFrame, optional): Training data for LIME reference
- `num_features` (int): Number of top features to include

**Returns:**
- `dict`: LIME explanation results
  ```python
  {
      'explanation': Explanation,          # LIME explanation object
      'feature_contributions': DataFrame,  # Feature contribution rules
      'prediction': 439.80                 # Prediction
  }
  ```

**Example:**
```python
lime_result = predictor.explain_prediction_lime(applicant, num_features=10)

print(f"Prediction: {lime_result['prediction']:.0f}")
print("\nFeature Contributions:")
print(lime_result['feature_contributions'])

# Output:
#              Feature_Rule  Contribution
# Number of Existing Loans  -106.56
#                   Income   +4.05
```

---

### 5. `explain_meta_learner(data)`

Explain how base models contribute to the ensemble prediction.

**Parameters:**
- `data` (dict or DataFrame): Input data to explain

**Returns:**
- `dict`: Meta-learner explanation
  ```python
  {
      'contributions': DataFrame,      # Base model contributions
      'base_predictions': dict,        # Predictions from each model
      'weights': dict,                 # Meta-learner weights
      'prediction': 439.80             # Final prediction
  }
  ```

**Example:**
```python
meta_result = predictor.explain_meta_learner(applicant)

print("Weights:")
print(meta_result['weights'])

# Output:
# {
#     'random_forest': 3.796,
#     'lightgbm': -2.799,
#     'tab_transformer': 0.002,
#     'intercept': 0.647
# }
```

---

### 6. `get_detailed_explanation(data)`

Get comprehensive explanation including all aspects.

**Parameters:**
- `data` (dict or DataFrame): Single record to explain

**Returns:**
- `dict`: Comprehensive explanation with base predictions, contributions, and features

**Example:**
```python
detailed = predictor.get_detailed_explanation(applicant)

print(detailed['base_predictions'])
print(detailed['contributions'])
print(detailed['features'])
```

---

### 7. `validate_data_format(data)`

Validate data format without making predictions.

**Parameters:**
- `data` (dict or DataFrame): Data to validate

**Returns:**
- `dict`: Validation result
  ```python
  {
      'valid': True,
      'message': 'Data validation successful',
      'validated_data': DataFrame  # If valid
  }
  ```

**Example:**
```python
validation = predictor.validate_data_format(applicant)
if validation['valid']:
    print("Data is valid!")
else:
    print(f"Error: {validation['message']}")
```

---

### 8. `get_model_info()`

Get information about the loaded model.

**Returns:**
- `dict`: Model information

**Example:**
```python
info = predictor.get_model_info()
print(f"Model: {info['model_type']}")
print(f"Base Models: {info['base_models']}")
print(f"Required Features: {info['required_features']}")
```

---

### 9. `set_background_data(data)` / `set_training_data(data)`

Set reference datasets for better explanations.

**Example:**
```python
# Load reference data
reference_data = pd.read_csv('reference_dataset.csv')

# Set for SHAP
predictor.set_background_data(reference_data)

# Set for LIME
predictor.set_training_data(reference_data)
```

---

## Convenience Function

### `predict_credit_score(data, return_explanations=False)`

Quick prediction without creating predictor object.

**Example:**
```python
from Utilities.prediction import predict_credit_score

result = predict_credit_score(applicant)
print(result['prediction'])

# With explanations
result = predict_credit_score(applicant, return_explanations=True)
print(result['shap_explanation'])
print(result['lime_explanation'])
```

---

## Required Input Features

All 10 features must be provided:

| Feature | Type | Description | Example |
|---------|------|-------------|---------|
| Age | int | Age in years | 45 |
| Income | float | Annual income | 75000 |
| Credit History Length | int | Years of credit history | 15 |
| Number of Existing Loans | int | Number of active loans | 2 |
| Existing Customer | str | 'Yes' or 'No' | 'No' |
| State | str | State name | 'Maharashtra' |
| City | str | City name | 'Mumbai' |
| LTV Ratio | float | Loan-to-Value ratio (0-1) | 0.7 |
| Employment Profile | str | Employment type | 'Salaried' |
| Occupation | str | Occupation | 'Engineer' |

---

## Error Handling

The utility provides comprehensive error messages:

```python
try:
    result = predictor.predict(data)
except ValueError as e:
    print(f"Validation error: {e}")
except RuntimeError as e:
    print(f"Model error: {e}")
```

Common errors:
- `ValueError`: Missing or invalid required features
- `RuntimeError`: Failed to load models

---

## Complete Example

```python
from Utilities import CreditScorePredictor
import pandas as pd

# Initialize
predictor = CreditScorePredictor()

# Prepare data
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

# 1. Make prediction
result = predictor.predict(applicant, return_base_predictions=True)
print(f"Credit Score: {result['prediction']:.0f}")

# 2. Get SHAP explanation
shap_exp = predictor.explain_prediction_shap(applicant, sample_size=50)
print("\nTop Features:")
print(shap_exp['feature_importance'].head(5))

# 3. Get LIME explanation
lime_exp = predictor.explain_prediction_lime(applicant)
print("\nLocal Explanation:")
print(lime_exp['feature_contributions'])

# 4. Get meta-learner insights
meta_exp = predictor.explain_meta_learner(applicant)
print("\nBase Model Weights:")
print(meta_exp['weights'])
```

---

## Testing

Run the demonstration script:
```bash
python test_prediction_utility.py
```

This will show all features in action with multiple examples.

---

## Notes

- **Preprocessing**: All preprocessing (encoding, scaling) is handled automatically
- **Unknown Values**: The utility gracefully handles unknown categorical values
- **Performance**: SHAP explanations may take a few seconds; use smaller `sample_size` for faster results
- **Thread Safety**: Create separate `CreditScorePredictor` instances for multi-threaded use

---

## Dependencies

- pandas
- numpy
- scikit-learn
- lightgbm
- torch
- shap
- lime

All dependencies are included in the project's requirements.txt.
