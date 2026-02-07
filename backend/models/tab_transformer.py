import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import shap
import lime
import lime.lime_tabular
import os
import joblib
import warnings
warnings.filterwarnings('ignore')

print("Libraries imported successfully!")

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)

# Load the original dataset
original_path = os.path.join(project_dir, 'dataset', 'credit_data.csv')
if not os.path.exists(original_path):
    print("ERROR: Original dataset not found!")
    print(f"Please ensure: {original_path} exists")
    exit(1)

df = pd.read_csv(original_path)
print(f"Original dataset loaded. Shape: {df.shape}")

# Select feature columns
feature_columns = ['Age', 'Income', 'Credit History Length', 'Number of Existing Loans', 
                    'Existing Customer', 'State', 'City', 'LTV Ratio', 
                    'Employment Profile', 'Occupation']

X = df[feature_columns]
y = df['Credit Score'].astype(int)

print(f"\nFeatures shape: {X.shape}")
print(f"Target shape: {y.shape}")

# Preprocessing Step 1: Identify and encode categorical variables
categorical_cols = X.select_dtypes(include=['object']).columns.tolist()
numerical_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
print(f"Categorical columns: {categorical_cols}")
print(f"Numerical columns: {numerical_cols}")

label_encoders = {}
X_encoded = X.copy()

for col in categorical_cols:
    le = LabelEncoder()
    X_encoded[col] = le.fit_transform(X_encoded[col].astype(str))
    label_encoders[col] = le

print("Categorical variables encoded successfully!")

# Preprocessing Step 2: Standardize the features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_encoded)
X_scaled_df = pd.DataFrame(X_scaled, columns=feature_columns)

print("Features standardized successfully!")

print(f"\nColumn names:\n{X_scaled_df.columns.tolist()}")

X_train, X_test, y_train, y_test = train_test_split(
    X_encoded, y, test_size=0.2, random_state=42
)

print(f"\nTraining set size: {X_train.shape[0]}")
print(f"Testing set size: {X_test.shape[0]}")

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Prepare dimensions for model
cat_dims = [X_encoded[col].nunique() for col in categorical_cols]
cat_idxs = [X_encoded.columns.tolist().index(col) for col in categorical_cols]
num_idxs = [X_encoded.columns.tolist().index(col) for col in numerical_cols]

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
        # If no categorical features, transformer part contributes 0
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

model = TabTransformer(
    num_features=X_encoded.shape[1],
    cat_dims=cat_dims,
    cat_idxs=cat_idxs,
    num_idxs=num_idxs,
    embed_dim=32,
    num_heads=4,
    num_layers=2,
    mlp_hidden=128,
    dropout=0.1
).to(device)

print(f"\nModel architecture:\n{model}")

X_train_tensor = torch.FloatTensor(X_train.values).to(device)
y_train_tensor = torch.FloatTensor(y_train.values).to(device)
X_test_tensor = torch.FloatTensor(X_test.values).to(device)
y_test_tensor = torch.FloatTensor(y_test.values).to(device)

train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
train_loader = DataLoader(train_dataset, batch_size=512, shuffle=True)

criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)

print("\nTraining TabTransformer model...")
epochs = 30
for epoch in range(epochs):
    model.train()
    total_loss = 0
    for batch_X, batch_y in train_loader:
        optimizer.zero_grad()
        predictions = model(batch_X)
        loss = criterion(predictions, batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    
    avg_loss = total_loss / len(train_loader)
    scheduler.step(avg_loss)
    
    if (epoch + 1) % 5 == 0:
        print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

print("Model training completed!")

# Save model
model_path = os.path.join(script_dir, 'tab_transformer_model.pth')
torch.save(model.state_dict(), model_path)
print(f"PyTorch model saved to: {model_path}")

# Evaluation
model.eval()
with torch.no_grad():
    y_pred_train = model(X_train_tensor).cpu().numpy()
    y_pred_test = model(X_test_tensor).cpu().numpy()

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

# Prediction wrapper for SHAP/LIME
def predict_fn(X):
    model.eval()
    with torch.no_grad():
        if isinstance(X, np.ndarray):
            X_tensor = torch.FloatTensor(X).to(device)
        else:
            X_tensor = X
            
        if X_tensor.ndim == 1:
            X_tensor = X_tensor.reshape(1, -1)
            
        result = model(X_tensor).cpu().numpy()
        return result if result.ndim > 0 else np.array([result])

print("\n" + "=" * 50)
print("SHAP ANALYSIS")
print("=" * 50)

# Using a smaller sample for SHAP to avoid long computation times
sample_size = 100
X_sample = X_test.iloc[:sample_size]
X_background = X_train.iloc[:sample_size]

print("\nCalculating SHAP values (using KernelExplainer for neural network)...")
try:
    explainer = shap.KernelExplainer(predict_fn, X_background.values)
    shap_values = explainer.shap_values(X_sample.values, nsamples=100)
    
    # Check if shap_values is a list (common with some shap versions/model types)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    shap_importance = pd.DataFrame({
        'Feature': X_encoded.columns,
        'SHAP Importance': np.abs(shap_values).mean(axis=0)
    }).sort_values('SHAP Importance', ascending=False)

    print("\nSHAP Feature Importance (Top 10):")
    print(shap_importance.head(10).to_string(index=False))
except Exception as e:
    print(f"Could not complete SHAP analysis: {e}")

print("\n" + "=" * 50)
print("LIME ANALYSIS")
print("=" * 50)

try:
    lime_explainer = lime.lime_tabular.LimeTabularExplainer(
        training_data=X_train.values,
        feature_names=X_encoded.columns.tolist(),
        mode='regression',
        random_state=42
    )

    print("\n--- LIME Explanation for Sample Prediction ---")
    sample_idx = 0
    actual_value = y_test.iloc[sample_idx]
    sample_prediction = predict_fn(X_sample.iloc[[sample_idx]].values)[0]
    
    lime_exp = lime_explainer.explain_instance(
        data_row=X_sample.iloc[sample_idx].values,
        predict_fn=predict_fn,
        num_features=10
    )

    print(f"Actual Credit Score: {actual_value}")
    print(f"Predicted Credit Score: {sample_prediction:.0f}")
    print("\nLIME Feature Contributions (Top 10):")

    lime_list = lime_exp.as_list()
    lime_df = pd.DataFrame(lime_list, columns=['Feature Rule', 'Contribution'])
    print(lime_df.to_string(index=False))
except Exception as e:
    print(f"Could not complete LIME analysis: {e}")
