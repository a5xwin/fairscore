import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import lightgbm as lgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

print("Libraries imported successfully!")

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)

# Load the preprocessed dataset
preprocessed_path = os.path.join(project_dir, 'dataset', 'credit_data_preprocessed.csv')
if not os.path.exists(preprocessed_path):
    print("ERROR: Preprocessed dataset not found!")
    print(f"Please run preprocessing.py first to generate: {preprocessed_path}")
    exit(1)

df = pd.read_csv(preprocessed_path)

print(f"Dataset shape: {df.shape}")
print(f"\nColumn names:\n{df.columns.tolist()}")

# Select only the specified feature columns (same as random forest)
feature_columns = ['Age', 'Income', 'Credit History Length', 'Number of Existing Loans', 
                    'Existing Customer', 'State', 'City', 'LTV Ratio', 
                    'Employment Profile', 'Occupation']

X = df[feature_columns]
y = df['Credit Score']

# Note: Data is already encoded and scaled from preprocessing.py
X_encoded = X.copy()

print("Dataset is already preprocessed with encoded categorical variables and SMOTE-ENN applied!")

X_train, X_test, y_train, y_test = train_test_split(
    X_encoded, y, test_size=0.2, random_state=42
)

print(f"\nTraining set size: {X_train.shape[0]}")
print(f"Testing set size: {X_test.shape[0]}")

# Initialize LightGBM Regressor
lgbm_model = lgb.LGBMRegressor(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=15,
    num_leaves=31,  # Default is 31, typically < 2^max_depth
    random_state=42,
    n_jobs=-1
)

print("\nTraining LightGBM model...")
lgbm_model.fit(X_train, y_train)
print("Model training completed!")

# Save the model
model_path = os.path.join(script_dir, 'lightgbm_model.joblib')
joblib.dump(lgbm_model, model_path)
print(f"Model saved to '{model_path}'")

y_pred_train = lgbm_model.predict(X_train)
y_pred_test = lgbm_model.predict(X_test)

print("\n" + "=" * 50)
print("LIGHTGBM MODEL PERFORMANCE METRICS")
print("=" * 50)

print("\n--- Training Set ---")
print(f"R² Score: {r2_score(y_train, y_pred_train):.4f}")
print(f"MAE: {mean_absolute_error(y_train, y_pred_train):.2f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y_train, y_pred_train)):.2f}")

print("\n--- Test Set ---")
print(f"R² Score: {r2_score(y_test, y_pred_test):.4f}")
print(f"MAE: {mean_absolute_error(y_test, y_pred_test):.2f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_test)):.2f}")

# Feature Importance
feature_importance = pd.DataFrame({
    'Feature': feature_columns,
    'Importance': lgbm_model.feature_importances_
})
feature_importance = feature_importance.sort_values(by='Importance', ascending=False)

print("\nFeature Importance:")
print(feature_importance)
