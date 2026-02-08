import bcrypt
from app.db.supabase import supabase


def hash_password(password: str) -> str:
    pw = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    pw = password.encode("utf-8")[:72]
    return bcrypt.checkpw(pw, hashed.encode("utf-8"))

def register_user(data):
    hashed = hash_password(data.password)

    res = supabase.table("users").insert({
        "name": data.name,
        "email": data.email,
        "password": hashed,
        "role": data.role
    }).execute()

    user = res.data[0]
    return {
        "userid": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
    }

def login_user(data):
    res = supabase.table("users").select("*").eq("email", data.email).execute()
    if not res.data:
        raise Exception("Invalid credentials")
    user = res.data[0]

    if not verify_password(data.password, user["password"]):
        raise Exception("Invalid credentials")

    return {
        "userid": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
    }