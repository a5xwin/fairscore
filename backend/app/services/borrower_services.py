from app.db.supabase import supabase
from datetime import datetime
import sys
import os

# Add parent directory to path for Utilities import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
try:
    from models.Utilities.prediction import CreditScorePredictor
    ML_PREDICTOR_AVAILABLE = True
except Exception as e:
    print(f"Warning: CreditScorePredictor not available: {e}")
    ML_PREDICTOR_AVAILABLE = False

# Initialize the predictor once at module level
_credit_predictor = None
if ML_PREDICTOR_AVAILABLE:
    try:
        _credit_predictor = CreditScorePredictor()
    except Exception as e:
        print(f"Warning: Failed to initialize CreditScorePredictor: {e}")
        ML_PREDICTOR_AVAILABLE = False

# -----------------------------
# Helpers
# -----------------------------
def to_months(years: int, months: int) -> int:
    return years * 12 + months


def calculate_ltv(loan_amount: float, asset_value: float) -> float:
    if asset_value <= 0:
        return 0
    return (loan_amount / asset_value) * 100


# -----------------------------
# ML PREDICTION for Credit Score
# -----------------------------
def generate_credit_score(dob, income, credit_history_months, loan_no, state, city, 
                         employment_profile, occupation, asset_value, loan_amount, 
                         existing_customer="yes"):
    """
    Generate credit score using the ML model if available, otherwise use stub.
    
    Parameters:
    -----------
    dob : str or datetime - Date of birth in YYYY-MM-DD format
    income : float - Annual income
    credit_history_months : int - Credit history in months
    loan_no : int - Number of existing loans
    state : str - State of residence
    city : str - City of residence
    employment_profile : str - Employment profile (e.g., 'Salaried', 'Self-employed')
    occupation : str - Occupation
    asset_value : float - Asset value
    loan_amount : float - Loan amount
    existing_customer : str - 'yes' or 'no'
    
    Returns:
    --------
    int - Credit score between 300 and 900
    """
    if ML_PREDICTOR_AVAILABLE and _credit_predictor is not None:
        try:
            # Calculate age from DOB
            if isinstance(dob, str):
                dob_date = datetime.strptime(dob, '%Y-%m-%d')
            else:
                dob_date = dob
            
            today = datetime.now()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            
            # Calculate LTV ratio
            ltv_ratio = (loan_amount / asset_value) if asset_value > 0 else 0
            
            # Prepare data for prediction
            credit_history_years = credit_history_months / 12
            
            prediction_data = {
                'Age': age,
                'Income': income,
                'Credit History Length': credit_history_years,
                'Number of Existing Loans': loan_no,
                'Existing Customer': 'Yes' if existing_customer.lower() == 'yes' else 'No',
                'State': state,
                'City': city,
                'LTV Ratio': ltv_ratio,
                'Employment Profile': employment_profile,
                'Occupation': occupation
            }
            
            # Get prediction from ML model
            result = _credit_predictor.predict(prediction_data)
            score = int(result['prediction'])
            
            # Ensure score is within valid range
            return int(min(max(score, 300), 900))
        
        except Exception as e:
            print(f"Error in ML prediction: {e}, falling back to stub implementation")
            # Fall back to stub implementation
            pass
    
    # Stub implementation (fallback)
    score = 600
    score += min(income / 10000, 120)
    score += min(credit_history_months / 12, 50)
    score -= loan_no * 15
    return int(min(max(score, 300), 900))


def risk_bucket(score: int):
    if score >= 750:
        return "low"
    elif score >= 650:
        return "medium"
    return "high"


def estimated_credit_line(score, income, ltv):
    base = income * 12 * 0.35
    score_factor = 1.3 if score >= 750 else 1.0 if score >= 650 else 0.6
    ltv_penalty = 0.7 if ltv > 80 else 1.0
    return int(base * score_factor * ltv_penalty)


# -----------------------------
# POST /borrower/details
# -----------------------------
def create_borrower_details(data):
    credit_history_months = to_months(
        data.creditHistoryYr, data.creditHistoryMon
    )
    loan_tenure_months = to_months(
        data.loanTenureYr, data.loanTenureMon
    )
    ltv = calculate_ltv(data.loanAmount, data.assetValue)

    # Insert borrower
    supabase.table("borrower").insert({
        "id": data.userid,
        "dob": str(data.dob),
        "gender": data.gender,
        "state": data.state,
        "city": data.city,
        "phone_no": data.phone,
        "employment_profile": data.empProfile,
        "occupation": data.occupation,
        "income": data.income,
        "credit_history_length": credit_history_months,
        "loan_no": data.loanNo,
        "asset_value": data.assetValue,
        "ltv_ratio": ltv,
        "existing_customer": "yes"
    }).execute()

    # Insert loan details
    supabase.table("borrower_loan_details").insert({
        "borrower_id": data.userid,
        "loan_amount": data.loanAmount,
        "loan_tenure": loan_tenure_months,
        "purpose": data.purpose
    }).execute()

    # Credit score + risk + credit line
    score = generate_credit_score(
        dob=data.dob,
        income=data.income,
        credit_history_months=credit_history_months,
        loan_no=data.loanNo,
        state=data.state,
        city=data.city,
        employment_profile=data.empProfile,
        occupation=data.occupation,
        asset_value=data.assetValue,
        loan_amount=data.loanAmount,
        existing_customer="yes"
    )
    risk = risk_bucket(score)
    credit_line = estimated_credit_line(score, data.income, ltv)

    supabase.table("borrower_credit_info").insert({
        "id": data.userid,
        "credit_score": score,
        "risk": risk,
        "credit_line": credit_line
    }).execute()

    return {"status": "success"}


# -----------------------------
# GET /borrower/credit-info
# -----------------------------
def get_credit_info(user_id: str):
    res = supabase.table("borrower_credit_info") \
        .select("credit_score, risk, credit_line") \
        .eq("id", user_id).single().execute()

    return {
        "creditScore": res.data["credit_score"],
        "Risk": res.data["risk"],
        "creditLine": res.data["credit_line"]
    }


# -----------------------------
# GET /borrower/loan-info
# -----------------------------
def get_loan_info(user_id: str):
    res = supabase.table("borrower_loan_details") \
        .select("loan_amount, loan_tenure, purpose") \
        .eq("borrower_id", user_id).single().execute()

    return {
        "loanAmount": res.data["loan_amount"],
        "loanTenureYr": res.data["loan_tenure"] // 12,
        "loanTenureMon": res.data["loan_tenure"] % 12,
        "purpose": res.data["purpose"]
    }


# -----------------------------
# PUT /borrower/loan-update
# -----------------------------
def update_loan_info(data):
    tenure_months = to_months(
        data.loanTenureYr, data.loanTenureMon
    )

    supabase.table("borrower_loan_details") \
        .update({
            "loan_amount": data.loanAmount,
            "loan_tenure": tenure_months,
            "purpose": data.purpose
        }) \
        .eq("borrower_id", data.userid) \
        .execute()

    return {"status": "updated"}


# -----------------------------
# GET /borrower/lender-info
# -----------------------------
def get_lenders():
    res = supabase.table("lender") \
        .select("id, type, loan_amount_from, loan_amount_to, interest") \
        .execute()

    # Also fetch lender names from users table
    lender_ids = [l["id"] for l in res.data]
    if not lender_ids:
        return []
    users_res = supabase.table("users").select("id, name").in_("id", lender_ids).execute()
    name_map = {u["id"]: u["name"] for u in users_res.data}

    return [
        {
            "lenderid": l["id"],
            "name": name_map.get(l["id"], "Unknown"),
            "type": l["type"],
            "loanAmountFrom": l["loan_amount_from"],
            "loanAmountTo": l["loan_amount_to"],
            "Interest": l["interest"]
        }
        for l in res.data
    ]


# -----------------------------
# POST /borrower/apply
# -----------------------------
def apply_to_lender(user_id: str, lender_id: str):
    supabase.table("loan").insert({
        "borrower_id": user_id,
        "lender_id": lender_id,
        "status": "requested"
    }).execute()

    return {"status": "requested"}


# -----------------------------
# GET /borrower/approved-lenders
# -----------------------------
def get_approved_lenders(user_id: str):
    res = supabase.table("loan") \
        .select("lender_id") \
        .eq("borrower_id", user_id) \
        .eq("status", "approved") \
        .execute()

    if not res.data:
        return []

    lender_ids = [r["lender_id"] for r in res.data]
    lenders_res = supabase.table("lender") \
        .select("id, type, capacity, loan_amount_from, loan_amount_to, interest") \
        .in_("id", lender_ids) \
        .execute()

    # Fetch names
    users_res = supabase.table("users").select("id, name").in_("id", lender_ids).execute()
    name_map = {u["id"]: u["name"] for u in users_res.data}

    return [
        {
            "lenderId": r["id"],
            "Name": name_map.get(r["id"], "Unknown"),
            "type": r["type"],
            "capacity": r["capacity"],
            "loanAmountFrom": r["loan_amount_from"],
            "loanAmountTo": r["loan_amount_to"],
            "interest": r["interest"]
        }
        for r in lenders_res.data
    ]