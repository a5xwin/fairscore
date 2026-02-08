from passlib.context import CryptContext
from app.db.supabase import supabase

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password, hashed):
    return pwd_context.verify(password, hashed)

def register_user(data):
    hashed = hash_password(data.password)

    res = supabase.table("users").insert({
        "name": data.name,
        "email": data.email,
        "password": hashed,
        "role": data.role
    }).execute()

    return {"userId": res.data[0]["id"], "role": data.role}

def login_user(data):
    res = supabase.table("users").select("*").eq("email", data.email).execute()
    user = res.data[0]

    if not verify_password(data.password, user["password"]):
        raise Exception("Invalid credentials")

    return {"userId": user["id"], "role": user["role"]}