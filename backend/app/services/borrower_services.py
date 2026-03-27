from app.db.supabase import supabase
from datetime import datetime
import sys
import os
import logging
from uuid import UUID


logger = logging.getLogger(__name__)


class ExplanationServiceError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)

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


def _ensure_predictor_available():
    if not ML_PREDICTOR_AVAILABLE or _credit_predictor is None:
        raise ExplanationServiceError(503, "ML explanation service is unavailable")


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _extract_table_records(table):
    if table is None:
        return []
    if hasattr(table, "to_dict"):
        try:
            return table.to_dict(orient="records")
        except TypeError:
            pass
    if isinstance(table, list):
        return table
    return []


def _format_feature_label(raw_feature: str) -> str:
    if not isinstance(raw_feature, str):
        return "Unknown"
    if "<=" in raw_feature or ">=" in raw_feature or "<" in raw_feature or ">" in raw_feature:
        return raw_feature
    return raw_feature.replace("_", " ")


def _build_tip_from_feature(feature_name: str):
    tips_map = {
        "Number of Existing Loans": "Reducing the number of active loans can improve your score over time.",
        "LTV Ratio": "Lowering the loan-to-value ratio by increasing down payment can reduce risk.",
        "Income": "A higher and stable income generally helps creditworthiness.",
        "Credit History Length": "Maintaining older active credit accounts can improve history length.",
        "Existing Customer": "Keeping a healthy repayment track record with your bank helps trust.",
    }
    return tips_map.get(feature_name)


def _format_shap_response(raw_shap):
    feature_names = raw_shap.get("feature_names") or []
    shap_values = raw_shap.get("shap_values")
    sample_shap_values = []

    if shap_values is not None:
        try:
            sample_shap_values = [float(v) for v in shap_values[0]]
        except Exception:
            sample_shap_values = []

    shap_by_feature = {}
    for idx, feature_name in enumerate(feature_names):
        if idx < len(sample_shap_values):
            shap_by_feature[feature_name] = sample_shap_values[idx]

    feature_rows = _extract_table_records(raw_shap.get("feature_importance"))
    top_factors = []

    for row in feature_rows[:8]:
        feature_name = row.get("Feature")
        if not feature_name:
            continue
        raw_contribution = shap_by_feature.get(feature_name)
        if raw_contribution is None:
            raw_contribution = _to_float(row.get("SHAP_Importance"), 0.0)

        direction = "helps" if raw_contribution >= 0 else "hurts"
        impact = abs(_to_float(raw_contribution))
        top_factors.append({
            "feature": _format_feature_label(feature_name),
            "direction": direction,
            "impact": round(impact, 4),
            "summary": f"{_format_feature_label(feature_name)} {direction} your score.",
        })

    prediction = _to_float(raw_shap.get("prediction"))
    return {
        "prediction": prediction,
        "topFactors": top_factors,
        "model": "shap",
    }


def _format_lime_response(raw_lime):
    feature_rows = _extract_table_records(raw_lime.get("feature_contributions"))
    rules = []

    for row in feature_rows[:8]:
        rule = row.get("Feature_Rule")
        contribution = _to_float(row.get("Contribution"), 0.0)
        if not rule:
            continue
        rules.append({
            "rule": _format_feature_label(rule),
            "effect": "helps" if contribution >= 0 else "hurts",
            "impact": round(abs(contribution), 4),
            "summary": f"{_format_feature_label(rule)} {'improves' if contribution >= 0 else 'reduces'} your score.",
        })

    prediction = _to_float(raw_lime.get("prediction"))
    return {
        "prediction": prediction,
        "rules": rules,
        "model": "lime",
    }


def _build_fallback_advice(prediction_data, shap_response, lime_response):
    tips = []

    for factor in shap_response.get("topFactors", []):
        if factor.get("direction") != "hurts":
            continue
        tip = _build_tip_from_feature(factor.get("feature"))
        if tip and tip not in tips:
            tips.append(tip)
        if len(tips) >= 4:
            break

    if len(tips) < 4:
        for rule in lime_response.get("rules", []):
            if rule.get("effect") == "hurts":
                tip = f"Work on improving the condition: {rule.get('rule')}"
                if tip not in tips:
                    tips.append(tip)
            if len(tips) >= 4:
                break

    if not tips:
        income = _to_float(prediction_data.get("Income"))
        loan_count = int(_to_float(prediction_data.get("Number of Existing Loans")))
        if income > 0:
            tips.append("Maintaining steady and higher income can improve score outcomes.")
        if loan_count > 0:
            tips.append("Reducing simultaneous active loans can lower perceived credit risk.")
        tips.append("Pay all EMIs and credit dues on time to build a positive repayment history.")

    return tips[:4]


def _get_user_prediction_data(user_id: str):
    """
    Helper function to build prediction data dictionary for a given user
    from the database.
    """
    _ensure_predictor_available()

    if not user_id:
        raise ExplanationServiceError(400, "userid is required")

    try:
        UUID(str(user_id))
    except (TypeError, ValueError) as exc:
        raise ExplanationServiceError(400, "userid must be a valid UUID") from exc

    try:
        borrower_res = supabase.table("borrower").select("*").eq("id", user_id).limit(1).execute()
    except Exception as exc:
        logger.exception("Failed to fetch borrower record for explanation")
        raise ExplanationServiceError(500, "Failed to fetch borrower details") from exc

    records = borrower_res.data or []
    if not records:
        raise ExplanationServiceError(404, "Borrower not found")

    b_data = records[0]
    
    # Calculate age from DOB
    dob = b_data.get("dob")
    if not dob:
        raise ExplanationServiceError(400, "Borrower date of birth is missing")

    try:
        if isinstance(dob, str):
            dob_date = datetime.strptime(dob, '%Y-%m-%d')
        else:
            dob_date = dob
    except Exception as exc:
        raise ExplanationServiceError(400, "Borrower date of birth is invalid") from exc
    today = datetime.now()
    age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
    
    credit_history_years = b_data.get("credit_history_length", 0) / 12
    
    prediction_data = {
        'Age': age,
        'Income': b_data.get("income"),
        'Credit History Length': credit_history_years,
        'Number of Existing Loans': b_data.get("loan_no"),
        'Existing Customer': 'Yes' if b_data.get("existing_customer", "yes").lower() == 'yes' else 'No',
        'State': b_data.get("state"),
        'City': b_data.get("city"),
        'LTV Ratio': b_data.get("ltv_ratio", 0),
        'Employment Profile': b_data.get("employment_profile"),
        'Occupation': b_data.get("occupation")
    }
    
    required_fields = [
        'Income',
        'Number of Existing Loans',
        'State',
        'City',
        'Employment Profile',
        'Occupation',
    ]
    missing = [field for field in required_fields if prediction_data.get(field) in [None, ""]]
    if missing:
        raise ExplanationServiceError(400, f"Borrower profile is incomplete: {', '.join(missing)}")

    return prediction_data


def get_shap_explanation(user_id: str):
    try:
        data = _get_user_prediction_data(user_id)
        raw_shap = _credit_predictor.explain_prediction_shap(data)
        return _format_shap_response(raw_shap)
    except ExplanationServiceError:
        raise
    except Exception as exc:
        logger.exception("Failed to generate SHAP explanation")
        raise ExplanationServiceError(500, "Failed to generate SHAP explanation") from exc


def get_lime_explanation(user_id: str):
    try:
        data = _get_user_prediction_data(user_id)
        raw_lime = _credit_predictor.explain_prediction_lime(data)
        return _format_lime_response(raw_lime)
    except ExplanationServiceError:
        raise
    except Exception as exc:
        logger.exception("Failed to generate LIME explanation")
        raise ExplanationServiceError(500, "Failed to generate LIME explanation") from exc


def get_gemini_advice(user_id: str):
    try:
        data = _get_user_prediction_data(user_id)

        try:
            shap_raw = _credit_predictor.explain_prediction_shap(data)
            shap_response = _format_shap_response(shap_raw)
        except Exception as exc:
            logger.warning("Could not generate SHAP data for Gemini advice: %s", exc)
            shap_raw = None
            shap_response = {"prediction": 0.0, "topFactors": []}

        try:
            lime_raw = _credit_predictor.explain_prediction_lime(data)
            lime_response = _format_lime_response(lime_raw)
        except Exception as exc:
            logger.warning("Could not generate LIME data for Gemini fallback advice: %s", exc)
            lime_response = {"prediction": 0.0, "rules": []}

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            tips = _build_fallback_advice(data, shap_response, lime_response)
            return {
                "prediction": shap_response.get("prediction") or lime_response.get("prediction") or 0.0,
                "advice": "AI advice is temporarily unavailable. Showing practical recommendations based on your profile.",
                "source": "fallback",
                "improvementTips": tips,
            }

        try:
            gemini_result = _credit_predictor.get_credit_improvement_advice(
                data,
                shap_explanation=shap_raw,
                api_key=api_key,
            )
            return {
                "prediction": _to_float(gemini_result.get("prediction")),
                "advice": gemini_result.get("advice", ""),
                "source": "gemini",
                "improvementTips": _build_fallback_advice(data, shap_response, lime_response),
            }
        except Exception as exc:
            logger.warning("Gemini advice generation failed: %s", exc)
            return {
                "prediction": shap_response.get("prediction") or lime_response.get("prediction") or 0.0,
                "advice": "AI advice is temporarily unavailable. Showing practical recommendations based on your profile.",
                "source": "fallback",
                "improvementTips": _build_fallback_advice(data, shap_response, lime_response),
            }
    except ExplanationServiceError:
        raise
    except Exception as exc:
        logger.exception("Failed to generate Gemini advice")
        raise ExplanationServiceError(500, "Failed to generate Gemini advice") from exc


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
# GET /borrower/profile-details
# -----------------------------
def get_profile_details(user_id: str):
    res = supabase.table("borrower") \
        .select("id, dob, gender, state, city, phone_no, employment_profile, occupation, income, credit_history_length, loan_no, asset_value") \
        .eq("id", user_id).single().execute()

    credit_history_length = res.data.get("credit_history_length") or 0

    return {
        "id": res.data.get("id"),
        "dob": str(res.data.get("dob")) if res.data.get("dob") else "",
        "gender": res.data.get("gender") or "",
        "state": res.data.get("state") or "",
        "city": res.data.get("city") or "",
        "phone": res.data.get("phone_no") or "",
        "empProfile": res.data.get("employment_profile") or "",
        "occupation": res.data.get("occupation") or "",
        "income": res.data.get("income") or 0,
        "creditHistoryYr": credit_history_length // 12,
        "creditHistoryMon": credit_history_length % 12,
        "loanNo": res.data.get("loan_no") or 0,
        "assetValue": res.data.get("asset_value") or 0,
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


# PUT /borrower/personal-update
# -----------------------------
def update_personal_info(data):
    ltv = calculate_ltv(
        supabase.table("borrower_loan_details") \
            .select("loan_amount") \
            .eq("borrower_id", data.userid).single().execute().data["loan_amount"],
        data.assetValue if hasattr(data, 'assetValue') else 0
    )
    
    supabase.table("borrower") \
        .update({
            "dob": str(data.dob),
            "gender": data.gender,
            "state": data.state,
            "city": data.city,
            "phone_no": data.phone
        }) \
        .eq("id", data.userid) \
        .execute()

    return {"status": "updated"}


# PUT /borrower/employment-update
# --------------------------------
def update_employment_info(data):
    supabase.table("borrower") \
        .update({
            "employment_profile": data.empProfile,
            "occupation": data.occupation,
            "income": data.income
        }) \
        .eq("id", data.userid) \
        .execute()

    return {"status": "updated"}


# PUT /borrower/credit-update
# ----------------------------
def update_credit_info(data):
    credit_history_months = to_months(data.creditHistoryYr, data.creditHistoryMon)
    
    supabase.table("borrower") \
        .update({
            "credit_history_length": credit_history_months,
            "loan_no": data.loanNo,
            "asset_value": data.assetValue
        }) \
        .eq("id", data.userid) \
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