from app.db.supabase import supabase

def months(years, months):
    return years * 12 + months

def calculate_ltv(loan, asset):
    return (loan / asset) * 100 if asset > 0 else 0

def credit_score_ml_stub(data):
    # TEMP ML
    score = 650 + min(data["income"] / 10000, 100)
    score = int(min(score, 900))
    return score

def risk_bucket(score):
    if score >= 750:
        return "low"
    if score >= 650:
        return "medium"
    return "high"

def estimated_credit_line(score, income, ltv):
    base = income * 12 * 0.3
    multiplier = 1.2 if score > 750 else 1.0 if score > 650 else 0.6
    penalty = 0.7 if ltv > 80 else 1
    return int(base * multiplier * penalty)

def create_borrower(data):
    credit_history = months(data.creditHistoryYr, data.creditHistoryMon)
    loan_tenure = months(data.loanTenureYr, data.loanTenureMon)
    ltv = calculate_ltv(data.loanAmount, data.assetValue)

    supabase.table("borrower").insert({
        "id": data.userId,
        "dob": data.dob,
        "state": data.state,
        "city": data.city,
        "phone_no": data.phone,
        "employment_profile": data.empProfile,
        "occupation": data.occupation,
        "income": data.income,
        "credit_history_length": credit_history,
        "loan_no": data.loanNo,
        "asset_value": data.assetValue,
        "ltv_ratio": ltv,
        "existing_customer": "yes"
    }).execute()

    supabase.table("borrower_loan_details").insert({
        "borrower_id": data.userId,
        "loan_amount": data.loanAmount,
        "loan_tenure": loan_tenure,
        "purpose": data.purpose
    }).execute()

    score = credit_score_ml_stub(data.dict())
    risk = risk_bucket(score)
    credit_line = estimated_credit_line(score, data.income, ltv)

    supabase.table("borrower_credit_info").insert({
        "id": data.userId,
        "credit_score": score,
        "risk": risk,
        "credit_line": credit_line
    }).execute()

    return {"status": "success"}