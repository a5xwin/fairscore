# Handling Unknown Categorical Values in Machine Learning

## Problem Statement

When training machine learning models, categorical variables are encoded into numerical values. However, during inference (prediction on new data), you may encounter categorical values that weren't present in the training dataset.

**Without proper handling:**
```python
encoder.transform(['Nevada'])  # ❌ ValueError if 'Nevada' wasn't in training data
```

---

## Solutions Implemented

### **Solution 1: SafeLabelEncoder (RECOMMENDED)**

A custom wrapper around sklearn's LabelEncoder that handles unseen values gracefully.

**Features:**
- ✅ Unknown values encoded as `-1` instead of crashing
- ✅ Fully backward compatible with sklearn's LabelEncoder API
- ✅ Minimal code changes needed
- ✅ Works with all downstream models

**How it works:**
```python
from safe_encoders import SafeLabelEncoder

# Training
encoder = SafeLabelEncoder(unknown_value=-1)
encoder.fit(['California', 'Texas', 'Florida'])

# Inference (works with new values!)
encoder.transform(['California'])  # → [0]
encoder.transform(['Nevada'])      # → [-1] ✓ No error!
```

**Updated workflow:**
```python
# In preprocessing.py (already updated)
from safe_encoders import SafeLabelEncoder

for col in categorical_cols:
    le = SafeLabelEncoder(unknown_value=-1)
    X_encoded[col] = le.fit_transform(X_encoded[col].astype(str))
```

---

### **Solution 2: SafePredictorWrapper (for Inference)**

Centralized class that handles end-to-end prediction with unknown values.

**Use this in your API/Flask server:**
```python
from inference import SafePredictorWrapper

# Initialize once
predictor = SafePredictorWrapper(
    model_path='models/random_forest_model.joblib',
    label_encoders_path='models/label_encoders.joblib',
    scaler_path='models/scaler.joblib'
)

# Make predictions on new data (even with unknown values)
new_data = pd.DataFrame({
    'Age': [45],
    'State': ['UnknownState'],  # Unknown value ✓
    'City': ['UnknownCity'],     # Unknown value ✓
    ...
})

predictions = predictor.predict(new_data)
```

---

### **Solution 3: Alternative - OrdinalEncoder (Advanced)**

If you need more control, use sklearn's OrdinalEncoder:

```python
from sklearn.preprocessing import OrdinalEncoder

encoder = OrdinalEncoder(
    handle_unknown='use_encoded_value',
    unknown_value=-1
)

encoder.fit(X_train[['State']])
encoder.transform([['Nevada']])  # → [[-1]]
```

---

## Migration Guide

### **Step 1: Update preprocessing.py** ✓ DONE
The file has been updated to use `SafeLabelEncoder` instead of `LabelEncoder`.

### **Step 2: Update Model Training Scripts**

For `random_forest.py` and `lightgbm_model.py`, no changes needed! They work with the safe encoders automatically.

### **Step 3: Update Inference/Prediction Code**

Replace this:
```python
# Old way (unsafe)
le = joblib.load('label_encoders.joblib')
df['State'] = le['State'].transform(df['State'])  # ❌ Crashes on unknown
```

With this:
```python
# New way (safe)
from inference import SafePredictorWrapper

predictor = SafePredictorWrapper(
    'models/random_forest_model.joblib',
    'models/label_encoders.joblib',
    'models/scaler.joblib'
)
predictions = predictor.predict(df)  # ✓ Handles unknown values
```

---

## Comparison of Approaches

| Feature | SafeLabelEncoder | SafePredictorWrapper | OrdinalEncoder |
|---------|------------------|----------------------|-----------------|
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Code Changes** | Minimal | Moderate | Moderate |
| **Unknown Handling** | Custom encode as -1 | Automatic | Encode as specified |
| **Scaling Support** | No | Yes ✓ | No |
| **Encoding Support** | Yes ✓ | Yes ✓ | Yes ✓ |
| **Model Agnostic** | Yes ✓ | Yes ✓ | Yes ✓ |
| **Production Ready** | Yes ✓ | Yes ✓ | Yes ✓ |

---

## Best Practices

### ✅ DO

1. **Always store unknown_value information** in metadata or logs
   ```python
   encoder_info = {
       'State': {
           'known_classes': encoder.classes_.tolist(),
           'unknown_value': -1
       }
   }
   ```

2. **Log unknown values for monitoring**
   ```python
   if unknown_mask.any():
       logger.warning(f"Found {unknown_mask.sum()} unknown values in State column")
   ```

3. **Version your encoders with your data**
   ```
   encoders_v1.0.joblib  # From 2024-01-01 dataset
   encoders_v1.1.joblib  # From 2024-06-01 dataset
   ```

4. **Handle unknown at prediction time, not training time**
   - Training data should be clean
   - Inference code should be defensive

### ❌ DON'T

1. **Don't remove unknown values silently**
   ```python
   # ❌ Bad: Missing data!
   df = df[df['State'].isin(encoder.classes_)]
   ```

2. **Don't use arbitrary large values for unknown**
   ```python
   # ❌ Bad: Can skew model
   encoder_value = 999999  # Too large!
   ```

3. **Don't re-fit encoders on new data**
   ```python
   # ❌ Bad: Changes learned patterns
   encoder.fit(new_data)
   ```

---

## Testing Unknown Values

```python
# test_unknown_handling.py
import pandas as pd
from inference import SafePredictorWrapper

# Test data with known and unknown values
test_df = pd.DataFrame({
    'Age': [35, 45, 55],
    'Income': [50000, 75000, 100000],
    'State': ['California', 'Texas', 'UNKNOWN_STATE_XYZ'],  # Last is unknown
    'City': ['LA', 'Houston', 'UNKNOWN_CITY_ABC'],      # Last is unknown
    # ... other required features ...
})

predictor = SafePredictorWrapper(
    'models/random_forest_model.joblib',
    'models/label_encoders.joblib',
    'models/scaler.joblib'
)

predictions = predictor.predict(test_df)
print(f"Predictions: {predictions}")
# Should work without error! ✓
```

---

## Files Created/Modified

1. **safe_encoders.py** - SafeLabelEncoder and utilities
2. **inference.py** - SafePredictorWrapper for API usage
3. **preprocessing.py** - Updated to use SafeLabelEncoder ✓

---

## Quick Start

```bash
# 1. Run updated preprocessing with safe encoders
python preprocessing.py

# 2. Train models (no changes needed)
python random_forest.py
python lightgbm_model.py

# 3. Test inference with unknown values
python inference.py
```

---

## For API Integration

If using Flask/FastAPI:

```python
from flask import Flask, request, jsonify
from inference import SafePredictorWrapper
import pandas as pd

app = Flask(__name__)
predictor = SafePredictorWrapper(...)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    df = pd.DataFrame([data])
    
    try:
        prediction = predictor.predict(df)[0]
        return jsonify({'prediction': float(prediction)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
```

---

## Monitoring & Analytics

Track unknown value patterns:

```python
from inference import handle_unknown_values_report

report = handle_unknown_values_report(new_data, label_encoders)
print(report)
# {
#     'State': {
#         'unknown_values': ['NewState1', 'NewState2'],
#         'count': 2,
#         'known_values': 50
#     },
#     ...
# }
```

---

## FAQ

**Q: Will using -1 for unknown values hurt model performance?**
A: No. Models interpret -1 as just another value. The model learns that -1 means "something different" from all known states, which is reasonable for rare/new values.

**Q: Should I retrain with new categories?**
A: Yes, periodically. When you accumulate enough data with new categories, retrain to improve predictions for those categories. Don't retrain immediately — batch updates help.

**Q: What if -1 was already used in my data?**
A: Use a different value: `SafeLabelEncoder(unknown_value=-999)` or any unused integer.

**Q: How do I know which values are unknown?**
A: The logging output in SafePredictorWrapper shows this, or use `handle_unknown_values_report()`.

---

## Summary

| Step | Action | File |
|------|--------|------|
| 1️⃣ | Use SafeLabelEncoder in preprocessing | `preprocessing.py` ✓ |
| 2️⃣ | Use SafePredictorWrapper for predictions | `inference.py` |
| 3️⃣ | Monitor unknown values in logs | API code |
| 4️⃣ | Retrain periodically with new data | Schedule task |

Your credit scoring model can now handle new states, cities, and occupations gracefully! 🎉
