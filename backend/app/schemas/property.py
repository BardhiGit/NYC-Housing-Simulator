"""
API request/response schemas for properties, units, loans, expenses, and scenarios.

These are the shapes of data going in/out of the HTTP API.
They differ from the financial engine's PropertyInput by having:
  - id fields (UUIDs)
  - timestamps
  - user_id context
  - flat structure (not nested for creation)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.inputs import AssumptionInput, Borough, ExpenseCategory, RentType


# ---------------------------------------------------------------------------
# Property
# ---------------------------------------------------------------------------

class PropertyCreate(BaseModel):
    name: str = ""
    address: str = ""
    borough: Borough = Borough.BROOKLYN
    year_built: Optional[int] = None
    gross_sq_ft: Optional[float] = None
    num_units: int = Field(gt=0)
    purchase_price: float = Field(gt=0)
    closing_costs: float = Field(default=0.0, ge=0)
    renovation_budget_total: float = Field(default=0.0, ge=0)
    assumptions: AssumptionInput = Field(default_factory=AssumptionInput)


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    borough: Optional[Borough] = None
    year_built: Optional[int] = None
    gross_sq_ft: Optional[float] = None
    num_units: Optional[int] = None
    purchase_price: Optional[float] = None
    closing_costs: Optional[float] = None
    renovation_budget_total: Optional[float] = None
    assumptions: Optional[AssumptionInput] = None


class PropertyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    address: str
    borough: str
    year_built: Optional[int]
    gross_sq_ft: Optional[float]
    num_units: int
    purchase_price: float
    closing_costs: float
    renovation_budget_total: float
    assumptions: dict
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Unit
# ---------------------------------------------------------------------------

class UnitCreate(BaseModel):
    unit_number: str
    bedrooms: int = Field(default=1, ge=0)
    bathrooms: float = Field(default=1.0, ge=0)
    sq_ft: Optional[float] = None
    rent_type: RentType
    current_rent: float = Field(default=0.0, ge=0)
    legal_rent: Optional[float] = None
    preferential_rent: Optional[float] = None
    market_rent_est: Optional[float] = None
    lease_expiry: Optional[str] = None   # ISO date string
    vacancy_rate: float = Field(default=0.05, ge=0, le=1)
    rent_growth_override: Optional[float] = None
    renovation_budget: float = 0.0
    notes: Optional[str] = None


class UnitUpdate(UnitCreate):
    pass


class UnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID
    unit_number: str
    bedrooms: int
    bathrooms: float
    sq_ft: Optional[float]
    rent_type: str
    current_rent: float
    legal_rent: Optional[float]
    preferential_rent: Optional[float]
    market_rent_est: Optional[float]
    lease_expiry: Optional[str]
    vacancy_rate: float
    rent_growth_override: Optional[float]
    renovation_budget: float
    notes: Optional[str]


# ---------------------------------------------------------------------------
# Loan
# ---------------------------------------------------------------------------

class LoanCreate(BaseModel):
    loan_amount: float = Field(gt=0)
    interest_rate: float = Field(gt=0, le=0.30)
    term_years: int = Field(gt=0, le=40)
    amortization_years: Optional[int] = None
    is_interest_only: bool = False
    io_period_years: int = Field(default=0, ge=0)


class LoanUpdate(LoanCreate):
    pass


class LoanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID
    loan_amount: float
    interest_rate: float
    term_years: int
    amortization_years: Optional[int]
    is_interest_only: bool
    io_period_years: int


# ---------------------------------------------------------------------------
# Expense
# ---------------------------------------------------------------------------

class ExpenseCreate(BaseModel):
    category: ExpenseCategory
    annual_amount: float = Field(ge=0)
    growth_rate: float = Field(default=0.03, ge=0, le=0.20)
    notes: Optional[str] = None


class ExpenseUpdate(ExpenseCreate):
    pass


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID
    category: str
    annual_amount: float
    growth_rate: float
    notes: Optional[str]


# ---------------------------------------------------------------------------
# Scenario
# ---------------------------------------------------------------------------

class ScenarioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: str = "custom"    # base|optimistic|pessimistic|custom
    overrides: dict = Field(default_factory=dict)


class ScenarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID
    name: str
    type: str
    overrides: dict
    results: Optional[dict]
    created_at: datetime


# ---------------------------------------------------------------------------
# Composite (property with all relationships — used for GET /properties/{id})
# ---------------------------------------------------------------------------

class PropertyDetailResponse(PropertyResponse):
    units: list[UnitResponse] = []
    loan: Optional[LoanResponse] = None
    expenses: list[ExpenseResponse] = []
    scenarios: list[ScenarioResponse] = []
