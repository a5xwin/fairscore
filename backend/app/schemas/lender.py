from pydantic import BaseModel


# -----------------------------
# POST /lender/details
# -----------------------------
class LenderCreateSchema(BaseModel):
    lenderId: str
    type: str
    capacity: float
    loanAmountFrom: float
    loanAmountTo: float
    interest: float


# -----------------------------
# PUT /lender/details
# -----------------------------
class LenderUpdateSchema(BaseModel):
    lenderId: str
    capacity: float
    loanAmountFrom: float
    loanAmountTo: float
    interest: float


# -----------------------------
# POST /lender/approve
# POST /lender/skip
# -----------------------------
class LenderActionSchema(BaseModel):
    lenderId: str
    userId: str
