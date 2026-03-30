from pydantic import BaseModel, Field, StringConstraints, model_validator
from typing import Annotated, Literal


UserIdStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
LenderTypeStr = Literal["individual", "financial_institution"]


# -----------------------------
# POST /lender/details
# -----------------------------
class LenderDetailsSchema(BaseModel):
    lenderId: UserIdStr
    type: LenderTypeStr
    capacity: float = Field(gt=0)
    loanAmountFrom: float = Field(gt=0)
    loanAmountTo: float = Field(gt=0)
    interest: float = Field(gt=0, le=100)

    @model_validator(mode="after")
    def validate_limits(self):
        if self.loanAmountFrom >= self.loanAmountTo:
            raise ValueError('Loan range "From" must be less than "To".')
        if self.loanAmountTo > self.capacity:
            raise ValueError("Maximum loan amount cannot exceed lending capacity.")
        return self


class LenderCreateSchema(BaseModel):
    lenderId: UserIdStr
    type: LenderTypeStr
    capacity: float = Field(gt=0)
    loanAmountFrom: float = Field(gt=0)
    loanAmountTo: float = Field(gt=0)
    interest: float = Field(gt=0, le=100)

    @model_validator(mode="after")
    def validate_limits(self):
        if self.loanAmountFrom >= self.loanAmountTo:
            raise ValueError('Loan range "From" must be less than "To".')
        if self.loanAmountTo > self.capacity:
            raise ValueError("Maximum loan amount cannot exceed lending capacity.")
        return self

class LenderDetailsUpdateSchema(BaseModel):
    lenderID: UserIdStr
    capacity: float = Field(gt=0)
    loanAmountFrom: float = Field(gt=0)
    loanAmountTo: float = Field(gt=0)
    interest: float = Field(gt=0, le=100)

    @model_validator(mode="after")
    def validate_limits(self):
        if self.loanAmountFrom >= self.loanAmountTo:
            raise ValueError('Loan range "From" must be less than "To".')
        if self.loanAmountTo > self.capacity:
            raise ValueError("Maximum loan amount cannot exceed lending capacity.")
        return self 

class ApproveBorrowerSchema(BaseModel):
    lenderId: UserIdStr
    userId: UserIdStr

class SkipBorrowerSchema(BaseModel):
    lenderId: UserIdStr
    userid: UserIdStr
