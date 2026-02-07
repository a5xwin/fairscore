import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from imblearn.combine import SMOTEENN
import os
import joblib
import warnings
warnings.filterwarnings('ignore')

print("Starting data preprocessing with SMOTE-ENN...")

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)

# Load the dataset
df = pd.read_csv(os.path.join(project_dir, 'dataset', 'credit_data.csv'))
print(f"Original dataset shape: {df.shape}")
print(f"Original class distribution:\n{df['Credit Score'].describe()}\n")

# Select only the specified columns for prediction
feature_columns = ['Age', 'Income', 'Credit History Length', 'Number of Existing Loans', 
                    'Existing Customer', 'State', 'City', 'LTV Ratio', 
                    'Employment Profile', 'Occupation']

X = df[feature_columns]
y = df['Credit Score']

# Store original column names for later
original_columns = X.columns.tolist()

# Encode categorical variables
categorical_cols = X.select_dtypes(include=['object']).columns.tolist()
print(f"Categorical columns: {categorical_cols}")

label_encoders = {}
X_encoded = X.copy()

for col in categorical_cols:
    le = LabelEncoder()
    X_encoded[col] = le.fit_transform(X_encoded[col].astype(str))
    label_encoders[col] = le

# Save label encoders
joblib.dump(label_encoders, os.path.join(script_dir, 'label_encoders.joblib'))
print(f"Label encoders saved to: {os.path.join(script_dir, 'label_encoders.joblib')}")

print("Categorical variables encoded successfully!")

# Standardize the features for SMOTE-ENN
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_encoded)
X_scaled_df = pd.DataFrame(X_scaled, columns=original_columns)

print(f"\nApplying SMOTE-ENN for imbalanced learning...")

# Apply SMOTE-ENN
smote_enn = SMOTEENN(random_state=42)
X_resampled, y_resampled = smote_enn.fit_resample(X_scaled_df, y)

print(f"Resampled dataset shape: {X_resampled.shape}")
print(f"Resampled class distribution:")
print(f"  Mean: {y_resampled.mean():.2f}")
print(f"  Std: {y_resampled.std():.2f}")
print(f"  Min: {y_resampled.min():.2f}")
print(f"  Max: {y_resampled.max():.2f}\n")

# Combine X and y into a single dataframe and save
preprocessed_df = pd.concat([X_resampled.reset_index(drop=True), 
                             pd.Series(y_resampled, name='Credit Score').reset_index(drop=True)], 
                            axis=1)

# Save preprocessed data
output_path = os.path.join(project_dir, 'dataset', 'credit_data_preprocessed.csv')
preprocessed_df.to_csv(output_path, index=False)
print(f"Preprocessed dataset saved to: {output_path}")

print("\nPreprocessing completed successfully!")
