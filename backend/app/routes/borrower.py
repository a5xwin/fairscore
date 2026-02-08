from fastapi import APIRouter, HTTPException, status
from app.schemas.borrower import (
    BorrowerDetailsSchema,
    LoanUpdateSchema,
    ApplyLoanSchema
)
from app.services.borrower_services import (
    create_borrower_details,
    get_credit_info,
    get_loan_info,
    update_loan_info,
    get_lenders,
    apply_to_lender,
    get_approved_lenders
)

router = APIRouter(prefix="/borrower", tags=["Borrower"])


@router.post("/details", status_code=status.HTTP_201_CREATED)
def borrower_details(data: BorrowerDetailsSchema):
    try:
        return create_borrower_details(data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create borrower details: {str(e)}"
        )


@router.get("/credit-info")
def credit_info(userId: str):
    try:
        return get_credit_info(userId)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit information not found"
        )


@router.get("/loan-info")
def loan_info(userId: str):
    try:
        return get_loan_info(userId)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan information not found"
        )


@router.put("/loan-update")
def loan_update(data: LoanUpdateSchema):
    try:
        return update_loan_info(data)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update loan details"
        )


@router.get("/lender-info")
def lender_info():
    try:
        lenders = get_lenders()
        if not lenders:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="No lenders available"
            )
        return lenders
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch lenders"
        )


@router.post("/apply", status_code=status.HTTP_201_CREATED)
def apply(data: ApplyLoanSchema):
    try:
        return apply_to_lender(data.userId, data.lenderId)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to apply to lender"
        )

@router.get("/approved-lenders")
def approved_lenders(userId: str):
    try:
        lenders = get_approved_lenders(userId)
        if not lenders:
            return []
        return lenders
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch approved lenders"
        )
