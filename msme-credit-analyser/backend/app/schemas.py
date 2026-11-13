from pydantic import BaseModel, Field, field_validator
from typing import Literal

class ApplicationInput(BaseModel):
    company_name: str = Field(min_length=2, max_length=160)
    industry: str
    business_age: float = Field(ge=0, le=150)
    location: str = "India"
    employees: int = Field(default=1, ge=1, le=1000000)
    ownership_type: str = "Private Limited"
    business_type: str = "B2B"
    revenue: float = Field(ge=0)
    ebitda: float = 0
    net_profit: float = 0
    total_assets: float = Field(ge=0)
    current_assets: float = Field(ge=0)
    current_liabilities: float = Field(ge=0)
    total_liabilities: float = Field(ge=0)
    net_worth: float = Field(ge=0)
    existing_debt: float = Field(ge=0)
    annual_interest_expense: float = Field(ge=0)
    cash_balance: float = Field(ge=0)
    accounts_receivable: float = Field(default=0, ge=0)
    inventory: float = Field(default=0, ge=0)
    accounts_payable: float = Field(default=0, ge=0)
    existing_loans: float = Field(default=0, ge=0)
    monthly_emi: float = Field(default=0, ge=0)
    previous_defaults: int = Field(default=0, ge=0, le=20)
    credit_history_years: float = Field(default=1, ge=0, le=100)
    active_loans: int = Field(default=0, ge=0, le=100)
    credit_utilization: float = Field(default=0, ge=0, le=2)
    payment_history: float = Field(default=0.9, ge=0, le=1)
    avg_monthly_balance: float = Field(default=0, ge=0)
    monthly_inflows: float = Field(default=0, ge=0)
    monthly_outflows: float = Field(default=0, ge=0)
    bounced_payments: int = Field(default=0, ge=0, le=100)
    banking_relationship_years: float = Field(default=1, ge=0, le=100)

    @field_validator("company_name", "industry")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip(): raise ValueError("must not be blank")
        return value.strip()

class LoginInput(BaseModel):
    email: str = Field(min_length=5, max_length=180)
    password: str = Field(min_length=6, max_length=128)

