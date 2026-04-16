from fastapi import APIRouter, HTTPException, status
from app.schemas.lender import (
    LenderDetailsSchema,
    LenderDetailsUpdateSchema,
    ApproveBorrowerSchema,
    SkipBorrowerSchema
)
from app.services.lender_services import (
    create_lender_details,
    get_lender_details,
    update_lender_details,
    get_loan_requests,
    approve_borrower,
    skip_borrower,
    get_approved_borrowers,
    get_borrower_review_insights,
    check_lender_onboarding,
)

router = APIRouter(prefix="/lender", tags=["Lender"])


@router.post("/details", status_code=status.HTTP_201_CREATED)
def lender_details_create(data: LenderDetailsSchema):
    try:
        return create_lender_details(data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create lender details: {str(e)}"
        )


@router.get("/details")
def lender_details_get(lenderId: str):
    try:
        return get_lender_details(lenderId)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lender details not found"
        )


@router.put("/details")
def lender_details_update(data: LenderDetailsUpdateSchema):
    try:
        return update_lender_details(data)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update lender details"
        )


@router.get("/loan-requests")
def loan_requests(lenderID: str):
    try:
        requests = get_loan_requests(lenderID)
        if not requests:
            return []
        return requests
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch loan requests"
        )


@router.post("/approve")
def approve(data: ApproveBorrowerSchema):
    try:
        return approve_borrower(data.lenderId, data.userId)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to approve borrower"
        )


@router.post("/skip")
def skip(data: SkipBorrowerSchema):
    try:
        return skip_borrower(data.lenderId, data.userid)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to skip borrower"
        )


@router.get("/approved-borrowers")
def approved_borrowers(lenderId: str):
    try:
        borrowers = get_approved_borrowers(lenderId)
        if not borrowers:
            return []
        return borrowers
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch approved borrowers"
        )


@router.get("/review-insights")
def review_insights(lenderId: str, borrowerId: str):
    try:
        return get_borrower_review_insights(lenderId, borrowerId)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch borrower review insights"
        )


@router.get("/onboarding-status")
def onboarding_status(userid: str = "", lenderid: str = ""):
    try:
        user_id = userid or lenderid
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="userid is required"
            )

        onboarded = check_lender_onboarding(user_id)
        return {"onboarded": onboarded}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check onboarding status"
        )
