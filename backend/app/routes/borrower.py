from fastapi import APIRouter
from app.schemas.borrower import BorrowerDetailsSchema
from app.services.borrower_service import create_borrower

router = APIRouter()

@router.post("/details")
def borrower_details(data: BorrowerDetailsSchema):
    return create_borrower(data)