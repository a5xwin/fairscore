import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import torch
import torch.nn as nn
import os
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("STACKED ENSEMBLE MODEL - BUILDING META-LEARNER")
print("=" * 60)
print("\nBase Models: TabTransformer, Random Forest, LightGBM")
print("Meta-Learner: Linear Regression")
print("=" * 60)

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)

# Check if all base models exist
print("\nChecking for trained base models...")
rf_model_path = os.path.join(script_dir, 'random_forest_model.joblib')
lgbm_model_path = os.path.join(script_dir, 'lightgbm_model.joblib')
transformer_model_path = os.path.join(script_dir, 'tab_transformer_model.pth')

missing_models = []
if not os.path.exists(rf_model_path):
    missing_models.append("Random Forest (random_forest_model.joblib)")
if not os.path.exists(lgbm_model_path):
    missing_models.append("LightGBM (lightgbm_model.joblib)")
if not os.path.exists(transformer_model_path):
    missing_models.append("TabTransformer (tab_transformer_model.pth)")

if missing_models:
    print("\nERROR: Missing trained models:")
    for model in missing_models:
        print(f"  - {model}")
    print("\nPlease train all base models first:")
    print("  1. python random_forest.py")
    print("  2. python lightgbm_model.py")
    print("  3. python tab_transformer.py")
    exit(1)

print("✓ All base models found!")

# Load the original dataset (to match TabTransformer training)
# The individual models were trained on different datasets, but for stacking
# we use the original dataset which is common ground for all models
original_path = os.path.join(project_dir, 'dataset', 'credit_data.csv')
if not os.path.exists(original_path):
    print("\nERROR: Original dataset not found!")
    print(f"Please ensure: {original_path} exists")
    exit(1)

df_original = pd.read_csv(original_path)
print(f"\nOriginal dataset loaded. Shape: {df_original.shape}")

# Select feature columns
feature_columns = ['Age', 'Income', 'Credit History Length', 'Number of Existing Loans', 
                    'Existing Customer', 'State', 'City', 'LTV Ratio', 
                    'Employment Profile', 'Occupation']

X_original = df_original[feature_columns]
y = df_original['Credit Score'].astype(int)

# Identify categorical and numerical columns
categorical_cols = X_original.select_dtypes(include=['object']).columns.tolist()
numerical_cols = X_original.select_dtypes(include=['int64', 'float64']).columns.tolist()

print(f"Categorical columns: {categorical_cols}")
print(f"Numerical columns: {numerical_cols}")

# Encode categorical columns
from sklearn.preprocessing import LabelEncoder, StandardScaler
label_encoders_temp = {}
X_encoded = X_original.copy()
for col in categorical_cols:
    le = LabelEncoder()
    X_encoded[col] = le.fit_transform(X_encoded[col].astype(str))
    label_encoders_temp[col] = le

# Scale features (for RF and LightGBM)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_encoded)
X_scaled_df = pd.DataFrame(X_scaled, columns=feature_columns)

# Split data (same random_state as used in individual models for consistency)
# X_encoded for TabTransformer (not scaled)
# X_scaled_df for RF and LightGBM (scaled)
X_train_encoded, X_test_encoded, y_train, y_test = train_test_split(
    X_encoded, y, test_size=0.2, random_state=42
)

X_train_scaled, X_test_scaled, _, _ = train_test_split(
    X_scaled_df, y, test_size=0.2, random_state=42
)

print(f"Training set size: {X_train_encoded.shape[0]}")
print(f"Test set size: {X_test_encoded.shape[0]}")

# ============================================================================
# LOAD BASE MODELS
# ============================================================================
print("\n" + "=" * 60)
print("LOADING BASE MODELS")
print("=" * 60)

# 1. Load Random Forest
print("\n1. Loading Random Forest model...")
rf_model = joblib.load(rf_model_path)
print("   ✓ Random Forest loaded successfully")

# 2. Load LightGBM
print("\n2. Loading LightGBM model...")
lgbm_model = joblib.load(lgbm_model_path)
print("   ✓ LightGBM loaded successfully")

# 3. Load TabTransformer
print("\n3. Loading TabTransformer model...")

# Load original dataset to get categorical information for TabTransformer
original_path = os.path.join(project_dir, 'dataset', 'credit_data.csv')
df_original = pd.read_csv(original_path)
X_original = df_original[feature_columns]

# Identify categorical columns
categorical_cols = X_original.select_dtypes(include=['object']).columns.tolist()
numerical_cols = X_original.select_dtypes(include=['int64', 'float64']).columns.tolist()

# Get dimensions for TabTransformer model
from sklearn.preprocessing import LabelEncoder
label_encoders_temp = {}
X_temp = X_original.copy()
for col in categorical_cols:
    le = LabelEncoder()
    X_temp[col] = le.fit_transform(X_temp[col].astype(str))
    label_encoders_temp[col] = le

cat_dims = [X_temp[col].nunique() for col in categorical_cols]
cat_idxs = [X_temp.columns.tolist().index(col) for col in categorical_cols]
num_idxs = [X_temp.columns.tolist().index(col) for col in numerical_cols]

# Define TabTransformer architecture (must match training)
class TabTransformer(nn.Module):
    def __init__(self, num_features, cat_dims, cat_idxs, num_idxs, embed_dim=32, num_heads=4, num_layers=2, mlp_hidden=128, dropout=0.1):
        super(TabTransformer, self).__init__()
        self.cat_idxs = cat_idxs
        self.num_idxs = num_idxs
        
        # Embeddings for categorical features
        self.cat_embeddings = nn.ModuleList([
            nn.Embedding(dim + 1, embed_dim) for dim in cat_dims
        ])
        
        # Transformer for categorical embeddings
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=embed_dim * 4,
            dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Calculate input dimension for MLP
        total_dim = len(cat_idxs) * embed_dim + len(num_idxs)
        
        self.mlp = nn.Sequential(
            nn.Linear(total_dim, mlp_hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_hidden, mlp_hidden // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_hidden // 2, 1)
        )
    
    def forward(self, x):
        # Process categorical features through Transformer
        if len(self.cat_idxs) > 0:
            cat_embeds = []
            for i, idx in enumerate(self.cat_idxs):
                cat_embeds.append(self.cat_embeddings[i](x[:, idx].long()))
            
            cat_embeds = torch.stack(cat_embeds, dim=1)
            cat_transformed = self.transformer(cat_embeds)
            cat_part = cat_transformed.flatten(start_dim=1)
        
        # Process numerical features
        if len(self.num_idxs) > 0:
            num_features = x[:, self.num_idxs]
        else:
            num_features = None
        
        # Combine
        if len(self.cat_idxs) > 0 and len(self.num_idxs) > 0:
            combined = torch.cat([cat_part, num_features], dim=1)
        elif len(self.cat_idxs) > 0:
            combined = cat_part
        else:
            combined = num_features
            
        output = self.mlp(combined)
        return output.squeeze()

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
transformer_model = TabTransformer(
    num_features=X_temp.shape[1],
    cat_dims=cat_dims,
    cat_idxs=cat_idxs,
    num_idxs=num_idxs,
    embed_dim=32,
    num_heads=4,
    num_layers=2,
    mlp_hidden=128,
    dropout=0.1
).to(device)

transformer_model.load_state_dict(torch.load(transformer_model_path, map_location=device))
transformer_model.eval()
print(f"   ✓ TabTransformer loaded successfully (device: {device})")

# ============================================================================
# GENERATE BASE MODEL PREDICTIONS
# ============================================================================
print("\n" + "=" * 60)
print("GENERATING BASE MODEL PREDICTIONS")
print("=" * 60)

print("\nGenerating predictions on training set...")

# Random Forest predictions (uses scaled data)
print("  - Random Forest...", end=" ")
rf_train_pred = rf_model.predict(X_train_scaled)
rf_test_pred = rf_model.predict(X_test_scaled)
print("✓")

# LightGBM predictions (uses scaled data)
print("  - LightGBM...", end=" ")
lgbm_train_pred = lgbm_model.predict(X_train_scaled)
lgbm_test_pred = lgbm_model.predict(X_test_scaled)
print("✓")

# TabTransformer predictions (uses encoded but not scaled data)
print("  - TabTransformer...", end=" ")
with torch.no_grad():
    X_train_tensor = torch.FloatTensor(X_train_encoded.values).to(device)
    X_test_tensor = torch.FloatTensor(X_test_encoded.values).to(device)
    transformer_train_pred = transformer_model(X_train_tensor).cpu().numpy()
    transformer_test_pred = transformer_model(X_test_tensor).cpu().numpy()
print("✓")

# ============================================================================
# BUILD STACKED FEATURES FOR META-LEARNER
# ============================================================================
print("\n" + "=" * 60)
print("BUILDING META-LEARNER FEATURES")
print("=" * 60)

# Stack predictions as features for meta-learner
train_meta_features = np.column_stack([
    rf_train_pred,
    lgbm_train_pred,
    transformer_train_pred
])

test_meta_features = np.column_stack([
    rf_test_pred,
    lgbm_test_pred,
    transformer_test_pred
])

print(f"\nMeta-features shape (train): {train_meta_features.shape}")
print(f"Meta-features shape (test): {test_meta_features.shape}")

print("\nMeta-features preview (first 5 samples):")
meta_df = pd.DataFrame(
    train_meta_features[:5],
    columns=['RF_Prediction', 'LightGBM_Prediction', 'Transformer_Prediction']
)
print(meta_df)

# ============================================================================
# TRAIN META-LEARNER (LINEAR REGRESSION)
# ============================================================================
print("\n" + "=" * 60)
print("TRAINING META-LEARNER")
print("=" * 60)

meta_learner = LinearRegression()
print("\nTraining Linear Regression on base model predictions...")
meta_learner.fit(train_meta_features, y_train)
print("✓ Meta-learner training completed!")

# Display meta-learner coefficients
print("\nMeta-Learner Coefficients:")
coef_df = pd.DataFrame({
    'Base Model': ['Random Forest', 'LightGBM', 'TabTransformer'],
    'Weight': meta_learner.coef_
})
print(coef_df.to_string(index=False))
print(f"\nIntercept: {meta_learner.intercept_:.4f}")

# ============================================================================
# GENERATE ENSEMBLE PREDICTIONS
# ============================================================================
print("\n" + "=" * 60)
print("GENERATING ENSEMBLE PREDICTIONS")
print("=" * 60)

ensemble_train_pred = meta_learner.predict(train_meta_features)
ensemble_test_pred = meta_learner.predict(test_meta_features)

# ============================================================================
# EVALUATE PERFORMANCE
# ============================================================================
print("\n" + "=" * 60)
print("PERFORMANCE EVALUATION")
print("=" * 60)

# Individual model performance on test set
print("\n--- INDIVIDUAL MODEL PERFORMANCE (Test Set) ---")
print("\nRandom Forest:")
print(f"  R² Score: {r2_score(y_test, rf_test_pred):.4f}")
print(f"  MAE: {mean_absolute_error(y_test, rf_test_pred):.2f}")
print(f"  RMSE: {np.sqrt(mean_squared_error(y_test, rf_test_pred)):.2f}")

print("\nLightGBM:")
print(f"  R² Score: {r2_score(y_test, lgbm_test_pred):.4f}")
print(f"  MAE: {mean_absolute_error(y_test, lgbm_test_pred):.2f}")
print(f"  RMSE: {np.sqrt(mean_squared_error(y_test, lgbm_test_pred)):.2f}")

print("\nTabTransformer:")
print(f"  R² Score: {r2_score(y_test, transformer_test_pred):.4f}")
print(f"  MAE: {mean_absolute_error(y_test, transformer_test_pred):.2f}")
print(f"  RMSE: {np.sqrt(mean_squared_error(y_test, transformer_test_pred)):.2f}")

# Ensemble performance
print("\n" + "=" * 60)
print("--- STACKED ENSEMBLE PERFORMANCE ---")
print("=" * 60)

print("\nTraining Set:")
print(f"  R² Score: {r2_score(y_train, ensemble_train_pred):.4f}")
print(f"  MAE: {mean_absolute_error(y_train, ensemble_train_pred):.2f}")
print(f"  RMSE: {np.sqrt(mean_squared_error(y_train, ensemble_train_pred)):.2f}")

print("\nTest Set:")
test_r2 = r2_score(y_test, ensemble_test_pred)
test_mae = mean_absolute_error(y_test, ensemble_test_pred)
test_rmse = np.sqrt(mean_squared_error(y_test, ensemble_test_pred))

print(f"  R² Score: {test_r2:.4f}")
print(f"  MAE: {test_mae:.2f}")
print(f"  RMSE: {test_rmse:.2f}")

# Calculate improvement
best_individual_r2 = max(
    r2_score(y_test, rf_test_pred),
    r2_score(y_test, lgbm_test_pred),
    r2_score(y_test, transformer_test_pred)
)
improvement = ((test_r2 - best_individual_r2) / best_individual_r2) * 100

print("\n" + "=" * 60)
print(f"Improvement over best individual model: {improvement:+.2f}%")
print("=" * 60)

# ============================================================================
# SAVE META-LEARNER
# ============================================================================
print("\n" + "=" * 60)
print("SAVING META-LEARNER")
print("=" * 60)

meta_learner_path = os.path.join(script_dir, 'meta_learner.joblib')
joblib.dump(meta_learner, meta_learner_path)
print(f"\n✓ Meta-learner saved to: {meta_learner_path}")

# Save ensemble configuration for easy loading
ensemble_config = {
    'base_models': {
        'random_forest': rf_model_path,
        'lightgbm': lgbm_model_path,
        'tab_transformer': transformer_model_path
    },
    'meta_learner': meta_learner_path,
    'feature_columns': feature_columns,
    'coefficients': {
        'random_forest': float(meta_learner.coef_[0]),
        'lightgbm': float(meta_learner.coef_[1]),
        'tab_transformer': float(meta_learner.coef_[2]),
        'intercept': float(meta_learner.intercept_)
    },
    'test_performance': {
        'r2_score': float(test_r2),
        'mae': float(test_mae),
        'rmse': float(test_rmse)
    }
}

import json
config_path = os.path.join(script_dir, 'ensemble_config.json')
with open(config_path, 'w') as f:
    json.dump(ensemble_config, f, indent=2)
print(f"✓ Ensemble configuration saved to: {config_path}")

print("\n" + "=" * 60)
print("STACKED ENSEMBLE MODEL TRAINING COMPLETE!")
print("=" * 60)
print("\nTo use the ensemble for predictions, load:")
print("  1. All three base models")
print("  2. meta_learner.joblib")
print("  3. Get predictions from each base model")
print("  4. Feed predictions to meta-learner for final output")
print("=" * 60)
