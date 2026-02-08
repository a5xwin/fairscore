from app.db.supabase import supabase
from datetime import date


# -----------------------------
# Helpers
# -----------------------------
def months_to_yr_mon(months: int):
    return months // 12, months % 12


def calculate_age(dob: date):
    today = date.today()
    return today.year - dob.year - (
        (today.month, today.day) < (dob.month, dob.day)
    )


# -----------------------------
# POST /lender/details
# -----------------------------
def create_lender(data):
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
# GET /lender/details
# -----------------------------
def get_lender_details(lender_id: str):
    lender = supabase.table("lender") \
        .select("type, capacity, loan_amount_from, loan_amount_to, interest") \
        .eq("id", lender_id).single().execute()

    user = supabase.table("users") \
        .select("name") \
        .eq("id", lender_id).single().execute()

    return {
        "name": user.data["name"],
        "type": lender.data["type"],
        "capacity": lender.data["capacity"],
        "loanAmountFrom": lender.data["loan_amount_from"],
        "loanAmountTo": lender.data["loan_amount_to"],
        "interest": lender.data["interest"]
    }


# -----------------------------
# PUT /lender/details
# -----------------------------
def update_lender_details(data):
    supabase.table("lender").update({
        "capacity": data.capacity,
        "loan_amount_from": data.loanAmountFrom,
        "loan_amount_to": data.loanAmountTo,
        "interest": data.interest
    }).eq("id", data.lenderId).execute()

    return {"status": "updated"}


# -----------------------------
# GET /lender/loan-requests
# -----------------------------
def get_loan_requests(lender_id: str):
    res = supabase.table("loan") \
        .select("""
            borrower_id,
            borrower(
                income,
                credit_history_length,
                loan_no
            ),
            borrower_credit_info(
                credit_score,
                risk
            ),
            borrower_loan_details(
                loan_amount,
                loan_tenure
            ),
            users!loan_borrower_id_fkey(name)
        """) \
        .eq("lender_id", lender_id) \
        .eq("status", "requested") \
        .execute()

    requests = []
    for r in res.data:
        yr, mon = months_to_yr_mon(
            r["borrower_loan_details"]["loan_tenure"]
        )
        requests.append({
            "userId": r["borrower_id"],
            "name": r["users"]["name"],
            "creditScore": r["borrower_credit_info"]["credit_score"],
            "risk": r["borrower_credit_info"]["risk"],
            "income": r["borrower"]["income"],
            "loanAmount": r["borrower_loan_details"]["loan_amount"],
            "loanTenureYr": yr,
            "loanTenureMon": mon
        })

    return requests


# -----------------------------
# POST /lender/approve
# -----------------------------
def approve_request(lender_id: str, user_id: str):
    # Approve selected request
    supabase.table("loan").update({
        "status": "approved"
    }).eq("lender_id", lender_id) \
     .eq("borrower_id", user_id) \
     .eq("status", "requested") \
     .execute()

    # Cancel all other requests of this borrower.
    supabase.table("loan").update({
        "status": "cancelled"
    }).eq("borrower_id", user_id) \
     .neq("lender_id", lender_id) \
     .eq("status", "requested") \
     .execute()

    return {"status": "approved"}


# -----------------------------
# POST /lender/skip
# -----------------------------
def skip_request(lender_id: str, user_id: str):
    supabase.table("loan").update({
        "status": "cancelled"
    }).eq("lender_id", lender_id) \
     .eq("borrower_id", user_id) \
     .eq("status", "requested") \
     .execute()

    return {"status": "cancelled"}


# -----------------------------
# GET /lender/approved-borrowers
# -----------------------------
def get_approved_borrowers(lender_id: str):
    res = supabase.table("loan") \
        .select("""
            borrower_id,
            borrower(
                dob,
                state,
                city,
                occupation,
                gender,
                income,
                loan_no,
                ltv_ratio
            ),
            borrower_credit_info(
                credit_score,
                risk
            ),
            borrower_loan_details(
                loan_amount,
                loan_tenure
            ),
            users!loan_borrower_id_fkey(name, email)
        """) \
        .eq("lender_id", lender_id) \
        .eq("status", "approved") \
        .execute()

    approved = []
    for r in res.data:
        yr, mon = months_to_yr_mon(
            r["borrower_loan_details"]["loan_tenure"]
        )
        approved.append({
            "userId": r["borrower_id"],
            "name": r["users"]["name"],
            "email": r["users"]["email"],
            "age": calculate_age(r["borrower"]["dob"]),
            "state": r["borrower"]["state"],
            "city": r["borrower"]["city"],
            "occupation": r["borrower"]["occupation"],
            "gender": r["borrower"]["gender"],
            "creditScore": r["borrower_credit_info"]["credit_score"],
            "risk": r["borrower_credit_info"]["risk"],
            "income": r["borrower"]["income"],
            "loanNo": r["borrower"]["loan_no"],
            "ltvRatio": r["borrower"]["ltv_ratio"],
            "loanAmount": r["borrower_loan_details"]["loan_amount"],
            "loanTenureYr": yr,
            "loanTenureMon": mon
        })

    return approved