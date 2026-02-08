from fastapi import APIRouter, HTTPException, status
from app.schemas.lender import (
    LenderCreateSchema,
    LenderUpdateSchema,
    LenderActionSchema
)
from app.services.lender_services import (
    create_lender,
    get_lender_details,
    update_lender_details,
    get_loan_requests,
    approve_request,
    skip_request,
    get_approved_borrowers
)

router = APIRouter(prefix="/lender", tags=["Lender"])


@router.post("/details", status_code=status.HTTP_201_CREATED)
def create_details(data: LenderCreateSchema):
    try:
        return create_lender(data)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/details")
def details(lenderId: str):
    try:
        return get_lender_details(lenderId)
    except Exception:
        raise HTTPException(404, "Lender not found")


@router.put("/details")
def update_details(data: LenderUpdateSchema):
    try:
        return update_lender_details(data)
    except Exception:
        raise HTTPException(400, "Failed to update lender details")


@router.get("/loan-requests")
def loan_requests(lenderId: str):
    return get_loan_requests(lenderId)


@router.post("/approve")
def approve(data: LenderActionSchema):
    try:
        return approve_request(data.lenderId, data.userId)
    except Exception:
        raise HTTPException(400, "Approval failed")


@router.post("/skip")
def skip(data: LenderActionSchema):
    try:
        return skip_request(data.lenderId, data.userId)
    except Exception:
        raise HTTPException(400, "Skip failed")


@router.get("/approved-borrowers")
def approved(lenderId: str):
    return get_approved_borrowers(lenderId)
