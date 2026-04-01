from app.db.supabase import supabase
from datetime import date
import json
import logging
import os
import re

from app.services.borrower_services import get_shap_explanation, get_score_reasons


logger = logging.getLogger(__name__)


def _extract_json_object(text: str):
    if not isinstance(text, str):
        return {}

    cleaned = text.strip()
    if not cleaned:
        return {}

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    try:
        parsed = json.loads(cleaned[start:end + 1])
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _fallback_lender_review_advice(borrower_name: str, score: float, risk: str, reasons_payload):
    top_hurts = [
        reason.get("feature")
        for reason in (reasons_payload.get("combinedReasons") or [])
        if reason.get("direction") == "hurts"
    ][:3]

    decision = "Proceed with caution"
    if risk == "low" and score >= 700:
        decision = "Suitable for approval"
    elif risk == "high" or score < 600:
        decision = "High caution; consider tighter terms"

    reasons_text = ", ".join(top_hurts) if top_hurts else "overall profile volatility"
    advice = (
        f"Borrower {borrower_name} is assessed as {risk.upper()} risk with score {int(score)}. "
        f"Primary concerns: {reasons_text}. Recommendation: {decision}."
    )

    tips = [
        "If approving, cap the loan amount within your lender range and affordability checks.",
        "Apply risk-based pricing or stronger collateral/guarantor terms for high-risk profiles.",
        "Request latest income proof and repayment records before final underwriting.",
    ]

    return {
        "prediction": float(score),
        "advice": advice,
        "source": "fallback",
        "improvementTips": tips,
    }


def _normalize_currency_to_inr(text: str):
    if not isinstance(text, str):
        return ""

    normalized = text
    # Convert patterns like $300,000 -> ₹300,000
    normalized = re.sub(r"\$\s*([\d,]+(?:\.\d+)?)", r"₹\1", normalized)
    # Convert USD words to INR/Rupees wording.
    normalized = re.sub(r"\bUSD\b", "INR", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bdollars?\b", "rupees", normalized, flags=re.IGNORECASE)
    return normalized


def _generate_lender_review_advice_with_gemini(lender_context, borrower_context, reasons_payload, api_key: str):
    if not api_key:
        return None

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = (
            "You are a lending risk assistant. Generate a concise review note for a lender evaluating a borrower loan request. "
            "Use borrower risk context and reasons, then provide practical decision guidance. "
            "Use Indian currency style only (INR, rupees, ₹). Never use USD or $. "
            "The output should be lender-oriented underwriting guidance, not borrower coaching. "
            "Return ONLY a JSON object with keys: advice (string), improvementTips (array of 3 short strings). "
            "No markdown, no extra keys.\n\n"
            f"Lender context: {lender_context}\n"
            f"Borrower context: {borrower_context}\n"
            f"Score reasons: {reasons_payload}"
        )

        response = model.generate_content(prompt)
        response_text = response.text if hasattr(response, "text") else str(response)
        parsed = _extract_json_object(response_text)
        if not parsed:
            return None

        advice = _normalize_currency_to_inr(str(parsed.get("advice") or "").strip())
        tips = parsed.get("improvementTips") or []
        if not advice:
            return None

        normalized_tips = [_normalize_currency_to_inr(str(t).strip()) for t in tips if str(t).strip()][:4]
        return {
            "advice": advice,
            "improvementTips": normalized_tips,
        }
    except Exception as exc:
        logger.warning("Gemini lender review generation failed: %s", exc)
        return None


# -----------------------------
# POST /lender/details
# -----------------------------
def validate_lending_limits(capacity: float, loan_amount_from: float, loan_amount_to: float, interest: float) -> None:
    if capacity <= 0:
        raise ValueError("Lending capacity must be greater than 0.")
    if loan_amount_from <= 0 or loan_amount_to <= 0:
        raise ValueError("Loan amount range must be greater than 0.")
    if loan_amount_from >= loan_amount_to:
        raise ValueError('Loan range "From" must be less than "To".')
    if loan_amount_to > capacity:
        raise ValueError("Maximum loan amount cannot exceed lending capacity.")
    if interest <= 0 or interest > 100:
        raise ValueError("Interest rate must be greater than 0 and at most 100.")


def create_lender_details(data):
    validate_lending_limits(data.capacity, data.loanAmountFrom, data.loanAmountTo, data.interest)

    supabase.table("lender").insert({
        "id": data.lenderId,
        "type": data.type,
        "capacity": data.capacity,
        "loan_amount_from": data.loanAmountFrom,
        "loan_amount_to": data.loanAmountTo,
        "interest": data.interest
    }).execute()

    return {"status": "success"}


# -----------------------------
# GET /lender/details?lenderId=X
# -----------------------------
def get_lender_details(lender_id: str):
    # Fetch lender row
    res = supabase.table("lender") \
        .select("type, capacity, loan_amount_from, loan_amount_to, interest") \
        .eq("id", lender_id).single().execute()

    # Fetch name from users table
    user_res = supabase.table("users") \
        .select("name") \
        .eq("id", lender_id).single().execute()

    return {
        "name": user_res.data["name"],
        "type": res.data["type"],
        "capacity": res.data["capacity"],
        "loanAmountFrom": res.data["loan_amount_from"],
        "loanAmountTo": res.data["loan_amount_to"],
        "interest": res.data["interest"]
    }


# -----------------------------
# PUT /lender/details
# -----------------------------
def update_lender_details(data):
    validate_lending_limits(data.capacity, data.loanAmountFrom, data.loanAmountTo, data.interest)

    supabase.table("lender") \
        .update({
            "capacity": data.capacity,
            "loan_amount_from": data.loanAmountFrom,
            "loan_amount_to": data.loanAmountTo,
            "interest": data.interest
        }) \
        .eq("id", data.lenderID) \
        .execute()

    return {"status": "updated"}


# -----------------------------
# GET /lender/onboarding-status
# Check if lender has completed onboarding
# Returns True if lender record exists, False otherwise
# -----------------------------
def check_lender_onboarding(lender_id: str):
    try:
        res = supabase.table("lender") \
            .select("id") \
            .eq("id", lender_id).single().execute()
        return bool(res.data)
    except Exception:
        return False


# -----------------------------
# GET /lender/loan-requests?lenderID=X
# -----------------------------
def get_loan_requests(lender_id: str):
    # Get all loans with status "requested" for this lender
    res = supabase.table("loan") \
        .select("borrower_id") \
        .eq("lender_id", lender_id) \
        .eq("status", "requested") \
        .execute()

    if not res.data:
        return []

    borrower_ids = [r["borrower_id"] for r in res.data]

    # Fetch borrower names from users
    users_res = supabase.table("users").select("id, name").in_("id", borrower_ids).execute()
    name_map = {u["id"]: u["name"] for u in users_res.data}

    # Fetch borrower info
    borrowers_res = supabase.table("borrower") \
        .select("id, income") \
        .in_("id", borrower_ids).execute()
    borrower_map = {b["id"]: b for b in borrowers_res.data}

    # Fetch credit info
    credit_res = supabase.table("borrower_credit_info") \
        .select("id, credit_score, risk") \
        .in_("id", borrower_ids).execute()
    credit_map = {c["id"]: c for c in credit_res.data}

    # Fetch loan details
    loan_res = supabase.table("borrower_loan_details") \
        .select("borrower_id, loan_amount, loan_tenure") \
        .in_("borrower_id", borrower_ids).execute()
    loan_map = {l["borrower_id"]: l for l in loan_res.data}

    result = []
    for bid in borrower_ids:
        b = borrower_map.get(bid, {})
        c = credit_map.get(bid, {})
        l = loan_map.get(bid, {})
        tenure = l.get("loan_tenure", 0)
        result.append({
            "userid": bid,
            "name": name_map.get(bid, "Unknown"),
            "creditScore": c.get("credit_score", 0),
            "risk": c.get("risk", "unknown"),
            "income": b.get("income", 0),
            "loanAmount": l.get("loan_amount", 0),
            "loanTenureYr": tenure // 12,
            "loanTenureMon": tenure % 12,
        })

    return result


# -----------------------------
# POST /lender/approve
# -----------------------------
def approve_borrower(lender_id: str, borrower_id: str):
    # Approve this lender's request
    supabase.table("loan") \
        .update({"status": "approved"}) \
        .eq("lender_id", lender_id) \
        .eq("borrower_id", borrower_id) \
        .eq("status", "requested") \
        .execute()

    # Cancel ALL other lender requests of this borrower
    supabase.table("loan") \
        .update({"status": "cancelled"}) \
        .eq("borrower_id", borrower_id) \
        .neq("lender_id", lender_id) \
        .eq("status", "requested") \
        .execute()

    return {"status": "approved"}

# -----------------------------
# POST /lender/skip
# -----------------------------
def skip_borrower(lender_id: str, borrower_id: str):
    supabase.table("loan") \
        .update({"status": "cancelled"}) \
        .eq("lender_id", lender_id) \
        .eq("borrower_id", borrower_id) \
        .eq("status", "requested") \
        .execute()

    return {"status": "cancelled"}


# -----------------------------
# GET /lender/approved-borrowers?lenderId=X
# -----------------------------
def get_approved_borrowers(lender_id: str):
    # Get approved loans
    res = supabase.table("loan") \
        .select("borrower_id") \
        .eq("lender_id", lender_id) \
        .eq("status", "approved") \
        .execute()

    if not res.data:
        return []

    borrower_ids = [r["borrower_id"] for r in res.data]

    # Fetch user info (name, email)
    users_res = supabase.table("users").select("id, name, email").in_("id", borrower_ids).execute()
    user_map = {u["id"]: u for u in users_res.data}

    # Fetch borrower details
    borrowers_res = supabase.table("borrower") \
        .select("id, dob, gender, state, city, occupation, income, loan_no, ltv_ratio") \
        .in_("id", borrower_ids).execute()
    borrower_map = {b["id"]: b for b in borrowers_res.data}

    # Fetch credit info
    credit_res = supabase.table("borrower_credit_info") \
        .select("id, credit_score, risk") \
        .in_("id", borrower_ids).execute()
    credit_map = {c["id"]: c for c in credit_res.data}

    # Fetch loan details
    loan_res = supabase.table("borrower_loan_details") \
        .select("borrower_id, loan_amount, loan_tenure") \
        .in_("borrower_id", borrower_ids).execute()
    loan_map = {l["borrower_id"]: l for l in loan_res.data}

    result = []
    for bid in borrower_ids:
        u = user_map.get(bid, {})
        b = borrower_map.get(bid, {})
        c = credit_map.get(bid, {})
        l = loan_map.get(bid, {})
        tenure = l.get("loan_tenure", 0)

        # Calculate age from dob
        age = 0
        dob_str = b.get("dob")
        if dob_str:
            try:
                dob = date.fromisoformat(str(dob_str))
                today = date.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except Exception:
                age = 0

        result.append({
            "userid": bid,
            "name": u.get("name", "Unknown"),
            "email": u.get("email", ""),
            "age": age,
            "state": b.get("state", ""),
            "city": b.get("city", ""),
            "occupation": b.get("occupation", ""),
            "gender": b.get("gender", ""),
            "creditScore": c.get("credit_score", 0),
            "risk": c.get("risk", "unknown"),
            "income": b.get("income", 0),
            "loanNo": b.get("loan_no", 0),
            "ltvRatio": b.get("ltv_ratio", 0),
            "loanAmount": l.get("loan_amount", 0),
            "loanTenureYr": tenure // 12,
            "loanTenureMon": tenure % 12,
        })

    return result


def get_borrower_review_insights(lender_id: str, borrower_id: str):
    # Lender snapshot
    lender_row = supabase.table("lender") \
        .select("id, type, capacity, loan_amount_from, loan_amount_to, interest") \
        .eq("id", lender_id).limit(1).execute()
    lender_context = (lender_row.data or [{}])[0]

    # Borrower snapshot for review context
    user_row = supabase.table("users").select("name").eq("id", borrower_id).limit(1).execute()
    borrower_name = ((user_row.data or [{}])[0]).get("name", "Borrower")

    credit_row = supabase.table("borrower_credit_info") \
        .select("credit_score, risk") \
        .eq("id", borrower_id).limit(1).execute()
    credit_context = (credit_row.data or [{}])[0]

    loan_row = supabase.table("borrower_loan_details") \
        .select("loan_amount, loan_tenure, purpose") \
        .eq("borrower_id", borrower_id).limit(1).execute()
    loan_context = (loan_row.data or [{}])[0]

    shap = get_shap_explanation(borrower_id)
    reasons = get_score_reasons(borrower_id)

    score = float(credit_context.get("credit_score") or reasons.get("prediction") or 0.0)
    risk = str(credit_context.get("risk") or "unknown")

    borrower_context = {
        "name": borrower_name,
        "score": score,
        "risk": risk,
        "loanRequest": loan_context,
    }

    api_key = os.getenv("GEMINI_API_KEY", "")
    gemini_payload = _generate_lender_review_advice_with_gemini(
        lender_context=lender_context,
        borrower_context=borrower_context,
        reasons_payload=reasons,
        api_key=api_key,
    )

    if gemini_payload:
        advice = {
            "prediction": score,
            "advice": gemini_payload["advice"],
            "source": "gemini",
            "improvementTips": gemini_payload["improvementTips"],
        }
    else:
        advice = _fallback_lender_review_advice(borrower_name, score, risk, reasons)

    return {
        "shap": shap,
        "advice": advice,
    }
