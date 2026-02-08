from app.db.supabase import supabase
from datetime import date


# -----------------------------
# POST /lender/details
# -----------------------------
def create_lender_details(data):
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
