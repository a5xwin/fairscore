# Data Preprocessing Pipeline

## Overview
This pipeline uses SMOTE-ENN (Synthetic Minority Over-sampling Technique + Edited Nearest Neighbors) to handle imbalanced data in the credit scoring dataset.

## Files

### preprocessing.py
This script performs the following steps:
1. Loads the original dataset (`credit_data.csv`)
2. Encodes categorical variables (Gender, State, City, Employment Profile, Occupation)
3. Standardizes features using StandardScaler
4. Applies SMOTE-ENN to balance the target variable
5. Saves the preprocessed data to `credit_data_preprocessed.csv`

**Dependencies:**
- pandas
- numpy
- scikit-learn
- imbalanced-learn

**Usage:**
```bash
python preprocessing.py
```

This will generate: `backend/dataset/credit_data_preprocessed.csv`

### random_forest.py (Modified)
The modified script now:
1. Loads the preprocessed dataset instead of the raw dataset
2. Uses the already-encoded and scaled features
3. Trains the RandomForestRegressor model
4. Performs evaluation and explainability analysis (SHAP, LIME)

**Note:** The script requires `credit_data_preprocessed.csv` to exist. Run `preprocessing.py` first if the file is missing.

## Workflow

1. **First Time Setup:**
   ```bash
   python preprocessing.py
   ```
   This generates the preprocessed dataset.

2. **Train the Model:**
   ```bash
   python random_forest.py
   ```
   This trains the model using the preprocessed data.

## Benefits of SMOTE-ENN

- **SMOTE:** Generates synthetic samples of the minority class to balance the dataset
- **ENN (Edited Nearest Neighbors):** Removes noisy samples that don't fit well with their neighbors
- **Combined:** Provides better balance while reducing noise, leading to improved model generalization

## Data Characteristics

### Original Dataset
- Total samples: ~280K
- Features: 15 (6 categorical, 9 numerical)

### Preprocessed Dataset
- Balanced target variable distribution
- All categorical features encoded
- All features standardized
- Ready for model training

## Output Files

- `backend/dataset/credit_data_preprocessed.csv` - Preprocessed dataset
- `backend/models/random_forest_model.joblib` - Trained model
