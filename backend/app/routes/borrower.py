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
    get_approved_lenders,
    get_shap_explanation,
    get_lime_explanation,
    get_gemini_advice
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
def credit_info(userid: str):
    try:
        return get_credit_info(userid)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit information not found"
        )


@router.get("/loan-info")
def loan_info(userid: str):
    try:
        return get_loan_info(userid)
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
def lender_info(userid: str):
    try:
        lenders = get_lenders()
        if not lenders:
            return []
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
        return apply_to_lender(data.userid, data.lenderid)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to apply to lender"
        )

@router.get("/approved-lenders")
def approved_lenders(userid: str):
    try:
        lenders = get_approved_lenders(userid)
        if not lenders:
            return []
        return lenders
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch approved lenders"
        )


@router.get("/explain/shap")
def shap_explanation(userid: str):
    try:
        return get_shap_explanation(userid)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SHAP explanation: {str(e)}"
        )


@router.get("/explain/lime")
def lime_explanation(userid: str):
    try:
        return get_lime_explanation(userid)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate LIME explanation: {str(e)}"
        )


@router.get("/advice/gemini")
def gemini_advice(userid: str):
    try:
        return get_gemini_advice(userid)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Gemini advice: {str(e)}"
        )
