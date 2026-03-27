from pydantic import BaseModel
from datetime import date

class BorrowerDetailsSchema(BaseModel):
    userid: str
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
    userid: str
    loanAmount: float
    loanTenureYr: int
    loanTenureMon: int
    purpose: str

class ApplyLoanSchema(BaseModel):
    userid: str
    lenderid: str

class BorrowerPersonalUpdateSchema(BaseModel):
    userid: str
    dob: date
    gender: str
    state: str
    city: str
    phone: str

class BorrowerEmploymentUpdateSchema(BaseModel):
    userid: str
    empProfile: str
    occupation: str
    income: float

class BorrowerCreditUpdateSchema(BaseModel):
    userid: str
    creditHistoryYr: int
    creditHistoryMon: int
    loanNo: int
    assetValue: float