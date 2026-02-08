import bcrypt
from fastapi import HTTPException, status
from app.db.supabase import supabase


# -----------------------------
# Password utils
# -----------------------------
def hash_password(password: str) -> str:
    pw = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    pw = password.encode("utf-8")[:72]
    return bcrypt.checkpw(pw, hashed.encode("utf-8"))


# -----------------------------
# Register
# -----------------------------
def register_user(data):
    email = data.email.lower().strip()

    # Check if user exists
    existing = supabase.table("users") \
        .select("id") \
        .eq("email", email) \
        .execute()

    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    hashed = hash_password(data.password)

    res = supabase.table("users").insert({
        "name": data.name,
        "email": email,
        "password": hashed,
        "role": data.role
    }).execute()

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration failed"
        )

    user = res.data[0]
    return {
        "userid": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"]
    }


# -----------------------------
# Login
# -----------------------------
def login_user(data):
    email = data.email.lower().strip()

    res = supabase.table("users") \
        .select("*") \
        .eq("email", email) \
        .single() \
        .execute()

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    user = res.data

    if not verify_password(data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    return {
        "userid": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"]
    }