from app.db.supabase import supabase

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
# ML STUB (replace later)
# -----------------------------
def generate_credit_score(income, credit_history_months, loan_no):
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
        "id": data.userId,
        "dob": data.dob,
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
        "borrower_id": data.userId,
        "loan_amount": data.loanAmount,
        "loan_tenure": loan_tenure_months,
        "purpose": data.purpose
    }).execute()

    # Credit score + risk + credit line
    score = generate_credit_score(
        data.income, credit_history_months, data.loanNo
    )
    risk = risk_bucket(score)
    credit_line = estimated_credit_line(score, data.income, ltv)

    supabase.table("borrower_credit_info").insert({
        "id": data.userId,
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
        "risk": res.data["risk"],
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
        .eq("borrower_id", data.userId) \
        .execute()

    return {"status": "updated"}


# -----------------------------
# GET /borrower/lender-info
# -----------------------------
def get_lenders():
    res = supabase.table("lender") \
        .select("id, type, loan_amount_from, loan_amount_to, interest") \
        .execute()

    return [
        {
            "lenderId": l["id"],
            "type": l["type"],
            "loanAmountFrom": l["loan_amount_from"],
            "loanAmountTo": l["loan_amount_to"],
            "interest": l["interest"]
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
        .select("lender(id, type, capacity, loan_amount_from, loan_amount_to, interest)") \
        .eq("borrower_id", user_id) \
        .eq("status", "approved") \
        .execute()

    return [
        {
            "lenderId": r["lender"]["id"],
            "type": r["lender"]["type"],
            "capacity": r["lender"]["capacity"],
            "loanAmountFrom": r["lender"]["loan_amount_from"],
            "loanAmountTo": r["lender"]["loan_amount_to"],
            "interest": r["lender"]["interest"]
        }
        for r in res.data
    ]