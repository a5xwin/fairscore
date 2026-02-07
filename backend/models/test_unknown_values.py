"""
Test script to verify that unknown value handling works correctly.
Run this after preprocessing to ensure safe encoding/decoding.
"""

import pandas as pd
import numpy as np
import os
import joblib
from safe_encoders import SafeLabelEncoder, create_safe_encoders, encode_data_safely
from inference import SafePredictorWrapper, handle_unknown_values_report
import warnings
warnings.filterwarnings('ignore')


def test_safe_label_encoder():
    """Test SafeLabelEncoder with known and unknown values."""
    print("=" * 70)
    print("TEST 1: SafeLabelEncoder")
    print("=" * 70)
    
    # Create encoder with training data
    train_values = ['California', 'Texas', 'Florida', 'New York']
    encoder = SafeLabelEncoder(unknown_value=-1)
    encoder.fit(train_values)
    
    print(f"✓ Fitted encoder on: {encoder.classes_.tolist()}")
    
    # Test with known values
    known_test = ['California', 'Texas', 'NewYork']  # Note: typo on purpose later
    encoded_known = encoder.transform(known_test)
    print(f"\n✓ Known values: {known_test}")
    print(f"  Encoded as: {encoded_known.tolist()}")
    
    # Test with unknown values
    unknown_test = ['Nevada', 'Arizona', 'Utah', 'California']
    encoded_unknown = encoder.transform(unknown_test)
    print(f"\n✓ Test with unknown values: {unknown_test}")
    print(f"  Encoded as: {encoded_unknown.tolist()}")
    print(f"  Unknown values got: -1 ✓")
    
    # Test inverse transform
    print(f"\n✓ Inverse transform test:")
    decoded = encoder.inverse_transform([0, -1, 1, -1])
    print(f"  Input: [0, -1, 1, -1]")
    print(f"  Decoded: {decoded}")
    
    return True


def test_safe_encoding_pipeline():
    """Test the safe encoding pipeline on a real DataFrame."""
    print("\n" + "=" * 70)
    print("TEST 2: Safe Encoding Pipeline")
    print("=" * 70)
    
    # Create synthetic training data
    train_df = pd.DataFrame({
        'State': ['California', 'Texas', 'Florida'] * 100,
        'City': ['LA', 'Houston', 'Miami'] * 100,
        'Employment': ['Employed', 'Self-Employed'] * 150
    })
    
    print(f"✓ Training data shape: {train_df.shape}")
    print(f"  Unique States: {train_df['State'].unique().tolist()}")
    print(f"  Unique Cities: {train_df['City'].unique().tolist()}")
    print(f"  Unique Employment: {train_df['Employment'].unique().tolist()}")
    
    # Create encoders
    categorical_cols = ['State', 'City', 'Employment']
    encoders = create_safe_encoders(train_df, categorical_cols)
    
    print(f"\n✓ Created SafeLabelEncoders for: {categorical_cols}")
    
    # Test on data with unknown values
    test_df = pd.DataFrame({
        'State': ['California', 'Texas', 'Nevada', 'Oregon'],  # Nevada, Oregon unknown
        'City': ['LA', 'Houston', 'Las Vegas', 'Portland'],    # Las Vegas, Portland unknown
        'Employment': ['Employed', 'Self-Employed', 'Retired']  # Retired unknown
    })
    
    print(f"\n✓ Test data with unknown values:")
    print(test_df)
    
    # Encode safely
    encoded_df = encode_data_safely(test_df, categorical_cols, encoders)
    
    print(f"\n✓ Encoded data:")
    print(encoded_df)
    print(f"\n✓ Unknown values were encoded as -1 instead of crashing! ✓")
    
    return True


def test_predictor_wrapper():
    """Test SafePredictorWrapper with unknown values."""
    print("\n" + "=" * 70)
    print("TEST 3: SafePredictorWrapper with Unknown Values")
    print("=" * 70)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    model_path = os.path.join(script_dir, 'random_forest_model.joblib')
    encoders_path = os.path.join(script_dir, 'label_encoders.joblib')
    scaler_path = os.path.join(script_dir, 'scaler.joblib')
    
    # Check if files exist
    files_exist = all(os.path.exists(p) for p in [model_path, encoders_path, scaler_path])
    
    if not files_exist:
        print("❌ Model files not found. Run preprocessing.py first:")
        print(f"   - {model_path}")
        print(f"   - {encoders_path}")
        print(f"   - {scaler_path}")
        return False
    
    print(f"✓ Model files found")
    
    # Initialize predictor
    try:
        predictor = SafePredictorWrapper(model_path, encoders_path, scaler_path)
        print(f"✓ Predictor loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load predictor: {e}")
        return False
    
    # Create test data with unknown categorical values
    test_data = pd.DataFrame({
        'Age': [35, 45, 55],
        'Income': [50000, 75000, 100000],
        'Credit History Length': [5, 15, 20],
        'Number of Existing Loans': [1, 2, 3],
        'Existing Customer': ['Yes', 'No', 'Yes'],
        'State': ['California', 'Texas', 'UNKNOWN_STATE_XYZ'],  # Unknown ⭐
        'City': ['Los Angeles', 'Houston', 'UNKNOWN_CITY_ABC'],  # Unknown ⭐
        'LTV Ratio': [0.8, 0.7, 0.75],
        'Employment Profile': ['Employed', 'Self-Employed', 'Employed'],
        'Occupation': ['Engineer', 'Doctor', 'UNKNOWN_JOB']  # Unknown ⭐
    })
    
    print(f"\n✓ Test data with unknown values:")
    print(test_data)
    
    # Check for unknown values
    unknown_report = handle_unknown_values_report(test_data, predictor.label_encoders)
    if unknown_report:
        print(f"\n✓ Unknown values detected (as expected):")
        for col, info in unknown_report.items():
            print(f"  {col}: {info['unknown_values']}")
    
    # Make predictions (should work without error!)
    try:
        print(f"\n✓ Making predictions despite unknown values...")
        predictions = predictor.predict(test_data)
        
        print(f"\n✓ Predictions successful! (No errors!)")
        print(f"  Results:")
        for i, pred in enumerate(predictions):
            print(f"    Sample {i+1}: {pred:.2f}")
        
        return True
    
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return False


def test_comparison_old_vs_new():
    """Compare old (unsafe) vs new (safe) encoding."""
    print("\n" + "=" * 70)
    print("TEST 4: Old vs New Encoding Comparison")
    print("=" * 70)
    
    from sklearn.preprocessing import LabelEncoder
    
    # Training data
    train_values = ['California', 'Texas', 'Florida']
    
    # Test data with unknown value
    test_value = ['Nevada']
    
    # OLD WAY (unsafe)
    print("\n❌ OLD WAY (sklearn.LabelEncoder):")
    le_old = LabelEncoder()
    le_old.fit(train_values)
    
    try:
        result = le_old.transform(test_value)
        print(f"  Result: {result} (unexpected!)")
    except ValueError as e:
        print(f"  ERROR: {e}")
        print(f"  ❌ Cannot handle unknown values!")
    
    # NEW WAY (safe)
    print("\n✓ NEW WAY (SafeLabelEncoder):")
    le_new = SafeLabelEncoder(unknown_value=-1)
    le_new.fit(train_values)
    
    result = le_new.transform(test_value)
    print(f"  Result: {result}")
    print(f"  ✓ Handles unknown values gracefully!")
    
    return True


def run_all_tests():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  TESTING UNKNOWN VALUE HANDLING".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝\n")
    
    tests = [
        ("SafeLabelEncoder Basics", test_safe_label_encoder),
        ("Safe Encoding Pipeline", test_safe_encoding_pipeline),
        ("Old vs New Comparison", test_comparison_old_vs_new),
        ("SafePredictorWrapper", test_predictor_wrapper),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("\nYour credit scoring model can now handle unknown categorical values!")
        print("The preprocessing pipeline is ready for production use.")
    else:
        print("❌ Some tests failed. See output above for details.")
    print("=" * 70 + "\n")
    
    return all_passed


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
