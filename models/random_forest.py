import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import shap
import lime
import lime.lime_tabular
import warnings
warnings.filterwarnings('ignore')

print("Libraries imported successfully!")

df = pd.read_csv('../dataset/credit_data.csv')

print(f"Dataset shape: {df.shape}")
print(f"\nColumn names:\n{df.columns.tolist()}")
print(df.head())

print("\nData Types:")
print(df.dtypes)
print(f"\nMissing values:\n{df.isnull().sum()}")

print("\nCredit Score Statistics:")
print(df['Credit Score'].describe())

print(f"\nUsing full dataset with {len(df)} samples for training")

X = df.drop('Credit Score', axis=1)
y = df['Credit Score']

categorical_cols = X.select_dtypes(include=['object']).columns.tolist()
print(f"Categorical columns: {categorical_cols}")

label_encoders = {}
X_encoded = X.copy()

for col in categorical_cols:
    le = LabelEncoder()
    X_encoded[col] = le.fit_transform(X_encoded[col].astype(str))
    label_encoders[col] = le

print("Categorical variables encoded successfully!")
print(X_encoded.head())

X_train, X_test, y_train, y_test = train_test_split(
    X_encoded, y, test_size=0.2, random_state=42
)

print(f"\nTraining set size: {X_train.shape[0]}")
print(f"Testing set size: {X_test.shape[0]}")

rf_model = RandomForestRegressor(
    n_estimators=100,
    max_depth=15,
    min_samples_split=10,
    min_samples_leaf=5,
    n_jobs=-1,
    random_state=42
)

print("\nTraining Random Forest model...")
rf_model.fit(X_train, y_train)
print("Model training completed!")

y_pred_train = rf_model.predict(X_train)
y_pred_test = rf_model.predict(X_test)

print("\n" + "=" * 50)
print("MODEL PERFORMANCE METRICS")
print("=" * 50)

print("\n--- Training Set ---")
print(f"R² Score: {r2_score(y_train, y_pred_train):.4f}")
print(f"MAE: {mean_absolute_error(y_train, y_pred_train):.2f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y_train, y_pred_train)):.2f}")

print("\n--- Test Set ---")
print(f"R² Score: {r2_score(y_test, y_pred_test):.4f}")
print(f"MAE: {mean_absolute_error(y_test, y_pred_test):.2f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_test)):.2f}")

feature_importance = pd.DataFrame({
    'Feature': X_encoded.columns,
    'Importance': rf_model.feature_importances_
}).sort_values('Importance', ascending=False)

print("\nFeature Importance (Top 10):")
print(feature_importance.head(10).to_string(index=False))

results_df = pd.DataFrame({
    'Actual': y_test.values[:10],
    'Predicted': y_pred_test[:10].round(0).astype(int),
    'Difference': (y_test.values[:10] - y_pred_test[:10]).round(0).astype(int)
})

print("\nSample Predictions (First 10):")
print(results_df.to_string(index=False))

print("\n" + "=" * 50)
print("SHAP ANALYSIS")
print("=" * 50)

X_sample = X_test.iloc[:100]

print("\nCalculating SHAP values...")
explainer = shap.TreeExplainer(rf_model)
shap_values = explainer.shap_values(X_sample)

shap_importance = pd.DataFrame({
    'Feature': X_encoded.columns,
    'SHAP Importance': np.abs(shap_values).mean(axis=0)
}).sort_values('SHAP Importance', ascending=False)

print("\nSHAP Feature Importance (Top 10):")
print(shap_importance.head(10).to_string(index=False))

print("\n--- SHAP Explanation for Sample Prediction ---")
sample_idx = 0
sample_prediction = rf_model.predict(X_sample.iloc[[sample_idx]])[0]
actual_value = y_test.iloc[sample_idx]

print(f"Actual Credit Score: {actual_value}")
print(f"Predicted Credit Score: {sample_prediction:.0f}")
base_value = explainer.expected_value
if hasattr(base_value, '__len__'):
    base_value = base_value[0]
print(f"Base Value (avg prediction): {base_value:.2f}")
print("\nFeature Contributions:")

shap_contrib = pd.DataFrame({
    'Feature': X_encoded.columns,
    'Value': X_sample.iloc[sample_idx].values,
    'SHAP Value': shap_values[sample_idx]
}).sort_values('SHAP Value', key=abs, ascending=False)

print(shap_contrib.head(10).to_string(index=False))

print("\n" + "=" * 50)
print("LIME ANALYSIS")
print("=" * 50)

lime_explainer = lime.lime_tabular.LimeTabularExplainer(
    training_data=X_train.values,
    feature_names=X_encoded.columns.tolist(),
    mode='regression',
    random_state=42
)

print("\n--- LIME Explanation for Sample Prediction ---")
lime_exp = lime_explainer.explain_instance(
    data_row=X_sample.iloc[sample_idx].values,
    predict_fn=rf_model.predict,
    num_features=10
)

print(f"Actual Credit Score: {actual_value}")
print(f"Predicted Credit Score: {sample_prediction:.0f}")
print("\nLIME Feature Contributions (Top 10):")

lime_list = lime_exp.as_list()
lime_df = pd.DataFrame(lime_list, columns=['Feature Rule', 'Contribution'])
print(lime_df.to_string(index=False))

print("\n--- LIME Analysis for Multiple Samples ---")
for i in range(3):
    exp = lime_explainer.explain_instance(
        data_row=X_sample.iloc[i].values,
        predict_fn=rf_model.predict,
        num_features=5
    )
    print(f"\nSample {i+1}: Actual={y_test.iloc[i]}, Predicted={rf_model.predict(X_sample.iloc[[i]])[0]:.0f}")
    print("Top 5 contributing features:")
    for feat, contrib in exp.as_list()[:5]:
        print(f"  {feat}: {contrib:+.2f}")
