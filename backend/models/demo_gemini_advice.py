"""
Demo: Gemini credit score improvement advice.

Usage (PowerShell):
  $env:GEMINI_API_KEY = "YOUR_KEY"
  python demo_gemini_advice.py
"""

import os
import sys

# Allow imports from the models folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Utilities import CreditScorePredictor


def main():
    api_key = "YOUR API KEY HERE"
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    predictor = CreditScorePredictor()

    applicant = {
        'Age': 26,
        'Income': 32000,
        'Credit History Length': 1,
        'Number of Existing Loans': 3,
        'Existing Customer': 'No',
        'State': 'Bihar',
        'City': 'Patna',
        'LTV Ratio': 0.92,
        'Employment Profile': 'Self Employed',
        'Occupation': 'Driver'
    }

    result = predictor.predict(applicant)
    print(f"Predicted score: {result['prediction']:.0f}")

    advice = predictor.get_credit_improvement_advice(
        data=applicant,
        api_key=api_key,
        score_threshold=650,
        top_k=5
    )

    print("\nGemini advice:")
    print(advice["advice"])


if __name__ == "__main__":
    main()
