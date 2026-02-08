from pydantic import BaseModel

class LenderDetailsSchema(BaseModel):
    lenderId: str
    type: str
    capacity: float
    loanAmountFrom: float
    loanAmountTo: float
    interest: float