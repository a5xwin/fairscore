from pydantic import BaseModel
from datetime import date

class BorrowerDetailsSchema(BaseModel):
    userId: str
    dob: date
    gender: str
    state: str
    city: str
    phone: str
    empProfile: str
    occupation: str
    income: float
    creditHistoryYr: int
    creditHistoryMon: int
    loanNo: int
    assetValue: float
    loanAmount: float
    loanTenureYr: int
    loanTenureMon: int
    purpose: str

class LoanUpdateSchema(BaseModel):
    userId: str
    loanAmount: float
    loanTenureYr: int
    loanTenureMon: int
    purpose: str

class ApplyLoanSchema(BaseModel):
    userId: str
    lenderId: str