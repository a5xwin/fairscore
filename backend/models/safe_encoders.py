"""
Safe encoders that handle unseen categorical values during inference.
These encoders gracefully handle new/unknown values that weren't in the training data.
"""

import numpy as np
from sklearn.preprocessing import LabelEncoder
import warnings


class SafeLabelEncoder(LabelEncoder):
    """
    A modified LabelEncoder that handles unseen values instead of raising an error.
    Unknown values are assigned to a reserved class index.
    """
    
    def __init__(self, unknown_value=-1):
        """
        Parameters:
        -----------
        unknown_value : int, default=-1
            The numerical value to assign to unseen categories.
            For most models, -1 works well. Alternatives: use max_class + 1
        """
        super().__init__()
        self.unknown_value = unknown_value
        self._is_fitted = False
    
    def fit(self, y):
        """Fit the encoder and track the unknown value."""
        super().fit(y)
        self._is_fitted = True
        return self
    
    def fit_transform(self, y):
        """Fit and transform in one step."""
        self.fit(y)
        return self.transform(y)
    
    def transform(self, y):
        """
        Transform values, replacing unknown categories with unknown_value.
        
        Parameters:
        -----------
        y : array-like
            Values to transform
        
        Returns:
        --------
        array of encoded values (known: 0...n-1, unknown: unknown_value)
        """
        if not self._is_fitted:
            raise ValueError("Encoder must be fitted before transform. Use fit() or fit_transform() first.")
        
        y = np.asarray(y, dtype=object)
        
        # Create output array
        transformed = np.full(len(y), self.unknown_value, dtype=int)
        
        # Find indices of known classes
        mask = np.isin(y, self.classes_)
        
        # Transform known values using parent's method
        known_indices = np.where(mask)[0]
        if len(known_indices) > 0:
            transformed[known_indices] = super().transform(y[mask])
        
        # Unknown values remain as unknown_value
        return transformed
    
    def inverse_transform(self, y):
        """
        Inverse transform with support for unknown_value.
        Unknown values are returned as a special string.
        """
        y = np.asarray(y, dtype=int)
        
        # Handle unknown values
        if self.unknown_value in y:
            result = np.empty(len(y), dtype=object)
            known_mask = y != self.unknown_value
            
            if np.any(known_mask):
                result[known_mask] = super().inverse_transform(y[known_mask])
            
            result[~known_mask] = '[UNKNOWN]'
            return result
        else:
            return super().inverse_transform(y)
    
    def get_classes(self):
        """Get the list of known classes."""
        return self.classes_.tolist()
    
    def get_unknown_value(self):
        """Get the value assigned to unknown categories."""
        return self.unknown_value


class SafeOneHotEncoder:
    """
    A custom one-hot encoder that handles unseen categories.
    Unseen categories are either dropped or converted to an 'unknown' column.
    """
    
    def __init__(self, handle_unknown='create_column'):
        """
        Parameters:
        -----------
        handle_unknown : str, default='create_column'
            - 'create_column': Create an extra column for unknown categories
            - 'drop': Drop samples with unknown categories
            - 'value': Assign all unknown to a single encoded value
        """
        if handle_unknown not in ['create_column', 'drop', 'value']:
            raise ValueError(f"Unknown value for handle_unknown: {handle_unknown}")
        
        self.handle_unknown = handle_unknown
        self.category_mappings = {}
        self._is_fitted = False
    
    def fit(self, df, categorical_cols):
        """
        Fit the encoder on training data.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Training data
        categorical_cols : list
            List of categorical column names
        """
        for col in categorical_cols:
            unique_values = df[col].astype(str).unique()
            self.category_mappings[col] = set(unique_values)
        
        self._is_fitted = True
        return self
    
    def transform(self, df, categorical_cols):
        """
        Transform data with support for unseen categories.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Data to transform
        categorical_cols : list
            List of categorical column names
        
        Returns:
        --------
        Encoded data as dictionary or DataFrame
        """
        if not self._is_fitted:
            raise ValueError("Encoder must be fitted before transform.")
        
        df = df.copy()
        encoded = {}
        
        for col in categorical_cols:
            known_categories = self.category_mappings.get(col, set())
            
            # Create one-hot encoding for known categories
            for cat in known_categories:
                encoded[f'{col}_{cat}'] = (df[col].astype(str) == cat).astype(int)
            
            # Handle unknown categories
            is_unknown = ~df[col].astype(str).isin(known_categories)
            
            if self.handle_unknown == 'create_column':
                encoded[f'{col}_UNKNOWN'] = is_unknown.astype(int)
            elif self.handle_unknown == 'drop':
                if is_unknown.any():
                    print(f"Warning: Dropping {is_unknown.sum()} rows with unknown values in {col}")
            elif self.handle_unknown == 'value':
                # If unseen, set all known categories to 0 (or could assign to a default)
                for cat in known_categories:
                    encoded[f'{col}_{cat}'] = encoded[f'{col}_{cat}'] & ~is_unknown
        
        return encoded


# ============================================================================
# Integration Example with Preprocessing
# ============================================================================

def create_safe_encoders(df, categorical_cols, unknown_handling='SafeLabelEncoder'):
    """
    Factory function to create safe encoders for all categorical columns.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Training data
    categorical_cols : list
        List of categorical column names
    unknown_handling : str, default='SafeLabelEncoder'
        Type of encoder to use
    
    Returns:
    --------
    dict : Mapping of column name -> encoder instance
    """
    if unknown_handling == 'SafeLabelEncoder':
        encoders = {col: SafeLabelEncoder(unknown_value=-1) for col in categorical_cols}
    else:
        raise ValueError(f"Unknown encoder type: {unknown_handling}")
    
    for col in categorical_cols:
        encoders[col].fit(df[col].astype(str))
    
    return encoders


def encode_data_safely(df, categorical_cols, encoders):
    """
    Safely encode new data that might contain unseen categories.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Data to encode (can contain unknown categories)
    categorical_cols : list
        List of categorical column names
    encoders : dict
        Dictionary of fitted encoders
    
    Returns:
    --------
    pandas.DataFrame : DataFrame with encoded columns
    """
    df_encoded = df.copy()
    
    for col in categorical_cols:
        if col not in encoders:
            raise ValueError(f"No encoder found for column: {col}")
        
        # This will handle unknown values gracefully
        df_encoded[col] = encoders[col].transform(df_encoded[col].astype(str))
    
    return df_encoded
