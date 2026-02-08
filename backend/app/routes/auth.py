from fastapi import APIRouter, HTTPException, status
from app.schemas.auth import RegisterSchema, LoginSchema
from app.services.auth_services import register_user, login_user

router = APIRouter()

@router.post("/register")
def register(data: RegisterSchema):
    try:
        result = register_user(data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login")
def login(data: LoginSchema):
    try:
        result = login_user(data)
        return result
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
