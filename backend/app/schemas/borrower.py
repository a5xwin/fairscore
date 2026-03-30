from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator
from typing import Annotated, Literal
from datetime import date


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
UserIdStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
PhoneStr = Annotated[str, StringConstraints(pattern=r"^\d{10}$")]
GenderStr = Literal["Male", "Female", "Other"]
EmploymentProfileStr = Literal["Salaried", "Self-Employed", "Freelancer", "Student", "Unemployed"]

class BorrowerDetailsSchema(BaseModel):
    userid: UserIdStr
    dob: date
    gender: GenderStr
    state: NonEmptyStr
    city: NonEmptyStr
    phone: PhoneStr
    empProfile: EmploymentProfileStr
    occupation: NonEmptyStr
    income: float = Field(gt=0)
    creditHistoryYr: int = Field(ge=0, le=80)
    creditHistoryMon: int = Field(ge=0, le=11)
    loanNo: int = Field(ge=0, le=50)
    assetValue: float = Field(gt=0)
    loanAmount: float = Field(gt=0)
    loanTenureYr: int = Field(ge=0, le=30)
    loanTenureMon: int = Field(ge=0, le=11)
    purpose: NonEmptyStr

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, value: date) -> date:
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise ValueError("Applicant must be at least 18 years old.")
        if age > 100:
            raise ValueError("Date of birth is not valid.")
        return value

    @field_validator("occupation")
    @classmethod
    def validate_occupation(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Occupation must contain at least 2 characters.")
        if len(cleaned) > 80:
            raise ValueError("Occupation cannot exceed 80 characters.")
        return cleaned

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) > 120:
            raise ValueError("Purpose cannot exceed 120 characters.")
        return cleaned

    @model_validator(mode="after")
    def validate_cross_fields(self):
        if self.loanAmount > self.assetValue:
            raise ValueError("Loan amount cannot exceed asset value.")
        if self.loanTenureYr == 0 and self.loanTenureMon == 0:
            raise ValueError("Loan tenure must be at least 1 month.")
        return self

class LoanUpdateSchema(BaseModel):
    userid: UserIdStr
    loanAmount: float = Field(gt=0)
    loanTenureYr: int = Field(ge=0, le=30)
    loanTenureMon: int = Field(ge=0, le=11)
    purpose: NonEmptyStr

    @model_validator(mode="after")
    def validate_tenure(self):
        if self.loanTenureYr == 0 and self.loanTenureMon == 0:
            raise ValueError("Loan tenure must be at least 1 month.")
        return self

class ApplyLoanSchema(BaseModel):
    userid: UserIdStr
    lenderid: UserIdStr

class BorrowerPersonalUpdateSchema(BaseModel):
    userid: UserIdStr
    dob: date
    gender: GenderStr
    state: NonEmptyStr
    city: NonEmptyStr
    phone: PhoneStr

    @field_validator("dob")
    @classmethod
    def validate_personal_dob(cls, value: date) -> date:
        return BorrowerDetailsSchema.validate_dob(value)

class BorrowerEmploymentUpdateSchema(BaseModel):
    userid: UserIdStr
    empProfile: EmploymentProfileStr
    occupation: NonEmptyStr
    income: float = Field(gt=0)

    @field_validator("occupation")
    @classmethod
    def validate_employment_occupation(cls, value: str) -> str:
        return BorrowerDetailsSchema.validate_occupation(value)

class BorrowerCreditUpdateSchema(BaseModel):
    userid: UserIdStr
    creditHistoryYr: int = Field(ge=0, le=80)
    creditHistoryMon: int = Field(ge=0, le=11)
    loanNo: int = Field(ge=0, le=50)
    assetValue: float = Field(gt=0)