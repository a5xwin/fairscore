from fastapi import APIRouter, HTTPException, status
from app.schemas.borrower import (
    BorrowerDetailsSchema,
    LoanUpdateSchema,
    ApplyLoanSchema,
    BorrowerPersonalUpdateSchema,
    BorrowerEmploymentUpdateSchema,
    BorrowerCreditUpdateSchema,
)
from app.services.borrower_services import (
    create_borrower_details,
    get_credit_info,
    get_profile_details,
    get_loan_info,
    update_loan_info,
    get_lenders,
    apply_to_lender,
    get_approved_lenders,
    get_score_reasons,
    get_score_advice,
    get_credit_score_insights,
    update_personal_info,
    update_employment_info,
    update_credit_info,
    check_borrower_onboarding,
    ExplanationServiceError,
)

router = APIRouter(prefix="/borrower", tags=["Borrower"])



@router.post("/details", status_code=status.HTTP_201_CREATED)
def borrower_details(data: BorrowerDetailsSchema):
    try:
        return create_borrower_details(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
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


@router.get("/profile-details")
def profile_details(userid: str):
    try:
        return get_profile_details(userid)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile information not found"
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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update loan details"
        )


@router.put("/personal-update")
def personal_update(data: BorrowerPersonalUpdateSchema):
    try:
        return update_personal_info(data)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update personal information"
        )


@router.put("/employment-update")
def employment_update(data: BorrowerEmploymentUpdateSchema):
    try:
        return update_employment_info(data)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update employment information"
        )


@router.put("/credit-update")
def credit_update(data: BorrowerCreditUpdateSchema):
    try:
        return update_credit_info(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update credit information"
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


@router.get("/score-reasons")
def score_reasons(userid: str):
    try:
        return get_score_reasons(userid)
    except ExplanationServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate score reasons"
        )


@router.get("/score-advice")
def score_advice(userid: str):
    try:
        return get_score_advice(userid)
    except ExplanationServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate score advice"
        )


@router.get("/score-insights")
def score_insights(userid: str):
    try:
        return get_credit_score_insights(userid)
    except ExplanationServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate score insights"
        )


@router.get("/onboarding-status")
def onboarding_status(userid: str):
    try:
        onboarded = check_borrower_onboarding(userid)
        return {"onboarded": onboarded}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check onboarding status"
        )
