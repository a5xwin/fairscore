# Stacked Ensemble Model - Explainability Guide

## Overview
The stacked ensemble model now includes comprehensive explainability features through both **SHAP** and **LIME** analysis. These methods help understand:
- Which base models are most influential
- Which input features drive predictions
- How individual predictions are formed

## Available Explanation Methods

### 1. Meta-Learner Explanation
**Purpose:** Understand which base model predictions are most influential in the ensemble.

**Method:** `explain_meta_learner(data)`

**What it shows:**
- Individual predictions from each base model
- Weighted contributions based on meta-learner coefficients
- Average importance of each base model

**Example Output:**
```
Base Model Contributions:
Sample  RF_Prediction  RF_Contribution  LightGBM_Contribution  Ensemble
1       386.05         1465.29          -1081.67              385.17
2       436.69         1657.49          -1219.24              439.80

Average Base Model Importance:
Random Forest:  57.56%
LightGBM:       42.40%
TabTransformer: 0.03%
```

**Interpretation:**
- Random Forest dominates the ensemble (~58% importance)
- LightGBM provides refinement corrections (~42% importance)
- TabTransformer has minimal impact (<0.1% importance)

---

### 2. Detailed Sample Explanation
**Purpose:** Complete breakdown of how a single prediction is formed.

**Method:** `explain_sample_detailed(data, sample_idx=0)`

**What it shows:**
- Base model predictions
- Meta-learner weighted contributions
- Input feature values
- Final ensemble prediction

**Example Output:**
```
[1] BASE MODEL PREDICTIONS
Random Forest:  436.69
LightGBM:       435.65
TabTransformer: 438.63
Ensemble:       439.80

[2] META-LEARNER CONTRIBUTIONS
RF:          1657.49 (weight: 3.80)
LightGBM:   -1219.24 (weight: -2.80)
Transformer:    0.91 (weight: 0.00)
Intercept:      0.65

Sum = 439.80

[3] INPUT FEATURES
Age: 45, Income: 75000, Credit History: 15...
```

**Interpretation:**
- Shows the complete decision-making pipeline
- Reveals how base models disagree/agree
- Demonstrates meta-learner's combination strategy

---

### 3. SHAP Explanations
**Purpose:** Feature-level importance showing which input features affect the ensemble prediction.

**Method:** `explain_with_shap(samples, background, sample_size=100)`

**What it shows:**
- SHAP importance values for each feature
- How each feature contributes to predictions
- Accounts for feature interactions

**Example Output:**
```
SHAP Feature Importance (Top 10):
Feature                    SHAP Importance
Number of Existing Loans   48.31
Income                     2.17
State                      1.92
Credit History Length      0.90
Occupation                 0.71
```

**Example - Individual SHAP Values:**
```
Sample 1:
Number of Existing Loans:  -37.70 (negative impact)
Income:                    +5.55 (positive impact)
State:                     +2.26 (positive impact)
```

**Interpretation:**
- **Number of Existing Loans** is by far the most important feature
- Income and State have moderate influence
- Negative SHAP value → decreases predicted credit score
- Positive SHAP value → increases predicted credit score

**Advantages:**
- Theoretically grounded (based on Shapley values from game theory)
- Considers feature interactions
- Model-agnostic
- Consistent and locally accurate

**Usage Example:**
```python
from inference import StackedEnsemblePredictor

ensemble = StackedEnsemblePredictor()

# Prepare data
test_samples = data.head(5)
background = data.sample(100)

# Get SHAP explanations
shap_values, explainer = ensemble.explain_with_shap(
    test_samples, 
    background,
    sample_size=50
)

# SHAP values shape: (n_samples, n_features)
print(f"SHAP values shape: {shap_values.shape}")
```

---

### 4. LIME Explanations
**Purpose:** Local linear approximation of model behavior for individual predictions.

**Method:** `explain_with_lime(sample, training_data, sample_idx=0, num_features=10)`

**What it shows:**
- Local feature contributions (linear approximation)
- Most influential features for a specific prediction
- Easy-to-interpret rules

**Example Output:**
```
LIME Feature Contributions (Top 10):
Feature Rule                      Contribution
Number of Existing Loans <= 1.24  -106.56
State=Maharashtra                 +4.33
Income <= 75000                   +4.05
Age <= 45                         -3.48
LTV Ratio = 0.70                  +1.45
```

**Interpretation:**
- Feature rules show ranges/values being explained
- Negative contribution → decreases prediction
- Positive contribution → increases prediction
- LIME builds a local linear model around the prediction point

**Advantages:**
- Easy to understand (linear model)
- Fast computation
- Provides interpretable rules
- Works well for explaining individual predictions

**Usage Example:**
```python
from inference import StackedEnsemblePredictor

ensemble = StackedEnsemblePredictor()

# Prepare data
test_sample = data.head(3)
training_reference = data

# Get LIME explanation for first sample
lime_exp = ensemble.explain_with_lime(
    test_sample,
    training_reference,
    sample_idx=0,
    num_features=10
)

# Access explanation details
lime_exp.as_list()  # Returns list of (feature, contribution) tuples
```

---

## Comparison: SHAP vs LIME

| Aspect | SHAP | LIME |
|--------|------|------|
| **Theoretical Foundation** | Shapley values (game theory) | Local linear approximation |
| **Consistency** | Guaranteed | Not guaranteed |
| **Computational Cost** | Higher (slower) | Lower (faster) |
| **Global Interpretability** | Yes (aggregate SHAP values) | No (local only) |
| **Feature Interactions** | Accounts for interactions | Ignores interactions |
| **Output Format** | Importance values | Linear rules |
| **Best For** | Overall feature importance | Individual prediction explanations |

---

## Complete Usage Example

```python
import pandas as pd
from inference import StackedEnsemblePredictor

# Initialize ensemble
ensemble = StackedEnsemblePredictor()

# Prepare test data
test_data = pd.DataFrame({
    'Age': [35, 45, 50],
    'Income': [50000, 75000, 100000],
    'Credit History Length': [5, 15, 20],
    'Number of Existing Loans': [1, 2, 3],
    'Existing Customer': ['Yes', 'No', 'Yes'],
    'State': ['Delhi', 'Maharashtra', 'Karnataka'],
    'City': ['New Delhi', 'Mumbai', 'Bengaluru'],
    'LTV Ratio': [0.8, 0.7, 0.75],
    'Employment Profile': ['Salaried', 'Self Employed', 'Salaried'],
    'Occupation': ['Engineer', 'Business', 'Manager']
})

# 1. Meta-Learner Explanation
print("1. META-LEARNER EXPLANATION")
meta_exp = ensemble.explain_meta_learner(test_data)

# 2. Detailed Single Sample
print("\n2. DETAILED SAMPLE EXPLANATION")
detailed = ensemble.explain_sample_detailed(test_data, sample_idx=1)

# 3. SHAP Analysis
print("\n3. SHAP ANALYSIS")
shap_values, shap_exp = ensemble.explain_with_shap(
    test_data, 
    background=test_data,
    sample_size=50
)

# 4. LIME Analysis
print("\n4. LIME ANALYSIS")
lime_exp = ensemble.explain_with_lime(
    test_data,
    test_data,
    sample_idx=0,
    num_features=10
)
```

---

## Key Insights from Explanations

### 1. Most Important Features
Based on SHAP analysis across multiple samples:
1. **Number of Existing Loans** (48.3 importance) - Dominant factor
2. **Income** (2.2 importance) - Moderate influence
3. **State** (1.9 importance) - Geographic factor
4. **Credit History Length** (0.9 importance) - Minor influence
5. **Occupation** (0.7 importance) - Slight effect

### 2. Base Model Behavior
- **Random Forest**: Primary predictor with 57.6% influence
- **LightGBM**: Provides corrections with 42.4% influence (negative weight suggests it corrects RF's biases)
- **TabTransformer**: Negligible impact (0.03%) - may need re-evaluation

### 3. Model Recommendations
Based on explainability analysis:

**Consider:**
- Re-training TabTransformer on the same dataset as RF/LightGBM
- Investigating why TabTransformer has minimal impact
- Exploring feature engineering for location-based features (State/City)
- Using SHAP values to identify potential fairness issues

**Avoid:**
- Over-relying on a single explanation method
- Ignoring the context of feature interactions
- Making decisions based solely on feature importance without domain knowledge

---

## Practical Applications

### 1. Model Debugging
- Identify when base models strongly disagree
- Find samples where ensemble performs poorly
- Understand feature importance shifts across samples

### 2. Regulatory Compliance
- Provide explanations for credit decisions
- Demonstrate fairness in predictions
- Document decision-making process

### 3. Feature Engineering
- Identify underperforming features
- Discover important feature interactions
- Guide data collection priorities

### 4. Model Monitoring
- Track feature importance drift over time
- Detect when explanations become inconsistent
- Identify when retraining is needed

---

## Technical Notes

### Handling Unknown Categorical Values
All explanation methods properly handle unknown categorical values:
- Encoded as -1 during preprocessing
- TabTransformer maps to special "unknown" embedding
- Warnings are displayed but don't prevent explanation

### Performance Considerations
- **SHAP**: Computationally expensive for large datasets (use sample_size parameter)
- **LIME**: Fast, suitable for real-time explanations
- **Meta-learner**: Instant, no additional computation

### Limitations
1. **SHAP**: Slow for complex models, requires background dataset
2. **LIME**: Local approximation may not capture global behavior
3. **Meta-learner**: Only explains model combination, not feature impact
4. **All methods**: Cannot explain what the model *should* predict, only what it *does* predict

---

## References

- **SHAP**: Lundberg & Lee (2017) - "A Unified Approach to Interpreting Model Predictions"
- **LIME**: Ribeiro et al. (2016) - "Why Should I Trust You?"
- **Ensemble Stacking**: Wolpert (1992) - "Stacked Generalization"

---

## Related Files

- `inference.py` - Main implementation of all explanation methods
- `test_ensemble_explanations.py` - Demonstration script
- `stacked_ensemble.py` - Ensemble training
- `STACKED_ENSEMBLE_README.md` - General ensemble documentation
