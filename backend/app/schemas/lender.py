from pydantic import BaseModel

class LenderDetailsSchema(BaseModel):
    lenderId: str
    type: str
    capacity: float
    loanAmountFrom: float
    loanAmountTo: float
    interest: float

class LenderDetailsUpdateSchema(BaseModel):
    lenderID: str
    capacity: float
    loanAmountFrom: float
    loanAmountTo: float
    interest: float

class ApproveBorrowerSchema(BaseModel):
    lenderId: str
    userId: str

class SkipBorrowerSchema(BaseModel):
    lenderId: str
    userid: str