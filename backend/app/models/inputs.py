"""
Input data models for the NYC Housing Investment Simulator.

All monetary values are in USD. Rates are decimal fractions (0.065 = 6.5%).
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class Borough(str, Enum):
    MANHATTAN = "manhattan"
    BROOKLYN = "brooklyn"
    QUEENS = "queens"
    BRONX = "bronx"
    STATEN_ISLAND = "staten_island"


class RentType(str, Enum):
    STABILIZED = "stabilized"       # NYC rent-stabilized unit
    FREE_MARKET = "free_market"     # deregulated / market-rate unit
    VACANT = "vacant"               # currently unoccupied
    OWNER_OCCUPIED = "owner_occupied"  # landlord/family occupancy, no rental income


class ExpenseCategory(str, Enum):
    PROPERTY_TAX = "property_tax"
    INSURANCE = "insurance"
    WATER_SEWER = "water_sewer"
    HEAT = "heat"
    ELECTRIC = "electric"
    REPAIRS = "repairs"
    PAYROLL = "payroll"
    MANAGEMENT = "management"
    LEGAL_ACCOUNTING = "legal_accounting"
    CAPEX_RESERVE = "capex_reserve"
    MISC = "misc"


class UnitInput(BaseModel):
    """
    Represents a single rentable unit in the building.

    For rent-stabilized units:
      - current_rent  = what the tenant actually pays (may be preferential)
      - legal_rent    = the maximum collectible regulated rent per DHCR
      - preferential_rent = same as current_rent when below legal_rent

    Post-HSTPA 2019: landlord must maintain preferential rent for the duration
    of the tenancy. On vacancy, new tenant receives the legal regulated rent
    (not market rate). There is no longer a high-rent vacancy deregulation path.
    """

    unit_number: str = Field(description="e.g. '1A', '2F', 'Basement'")
    bedrooms: int = Field(ge=0, le=10)
    bathrooms: float = Field(default=1.0, ge=0)
    sq_ft: Optional[float] = Field(default=None, ge=0)
    rent_type: RentType

    # Monthly rents
    current_rent: float = Field(default=0.0, ge=0, description="Monthly rent actually collected")
    legal_rent: Optional[float] = Field(default=None, ge=0, description="RS: DHCR maximum rent")
    preferential_rent: Optional[float] = Field(default=None, ge=0, description="RS: rent when below legal")
    market_rent_est: Optional[float] = Field(default=None, ge=0, description="Analyst estimate of free-market rent")

    lease_expiry: Optional[date] = None
    vacancy_rate: float = Field(default=0.05, ge=0, le=1, description="Unit-level annual vacancy assumption")
    rent_growth_override: Optional[float] = Field(
        default=None, ge=-0.10, le=0.25,
        description="If set, overrides property-level rent growth assumption for this unit"
    )
    renovation_budget: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_rs_fields(self) -> "UnitInput":
        if self.rent_type == RentType.STABILIZED:
            if self.legal_rent is None:
                # Default legal rent to current rent if not provided
                self.legal_rent = self.current_rent
            if self.preferential_rent is not None:
                if self.preferential_rent > (self.legal_rent or self.current_rent):
                    raise ValueError("Preferential rent cannot exceed legal rent")
        return self


class LoanInput(BaseModel):
    """
    Mortgage / acquisition loan terms.

    Supports:
      - Standard fully-amortizing loans
      - Interest-only period followed by amortization
      - Balloon loans (term < amortization_years)
    """

    loan_amount: float = Field(gt=0)
    interest_rate: float = Field(gt=0, le=0.30, description="Annual rate, decimal (0.065 = 6.5%)")
    term_years: int = Field(gt=0, le=40, description="Loan term / balloon date in years")
    amortization_years: Optional[int] = Field(
        default=None, gt=0, le=40,
        description="Amortization period. If None, equals term_years (fully amortizing)"
    )
    is_interest_only: bool = Field(default=False)
    io_period_years: int = Field(default=0, ge=0, description="Years of interest-only before amortization begins")

    @model_validator(mode="after")
    def set_amortization(self) -> "LoanInput":
        if self.amortization_years is None:
            self.amortization_years = self.term_years
        if self.io_period_years >= self.term_years:
            raise ValueError("Interest-only period cannot equal or exceed loan term")
        return self


class ExpenseInput(BaseModel):
    """
    A single annual operating expense line item.

    NOTE: Debt service (mortgage payments) is NOT an operating expense.
    It belongs below the NOI line in the cash flow statement.
    """

    category: ExpenseCategory
    annual_amount: float = Field(ge=0)
    growth_rate: float = Field(default=0.03, ge=0, le=0.20, description="Annual growth rate")
    notes: Optional[str] = None


class AssumptionInput(BaseModel):
    """
    Forward-looking market and investment assumptions.

    These drive the multi-year projection, Monte Carlo simulation,
    and scenario analysis. Each can be overridden per scenario.
    """

    holding_period: int = Field(default=10, ge=1, le=30, description="Years before assumed sale")
    general_vacancy_rate: float = Field(default=0.05, ge=0, le=1)

    # Rent growth assumptions
    fm_rent_growth_rate: float = Field(
        default=0.03, ge=-0.10, le=0.15,
        description="Annual free-market rent growth"
    )
    rs_rent_growth_rate: float = Field(
        default=0.03, ge=0, le=0.10,
        description="Annual RS growth — should reflect expected RGB orders"
    )

    # Expense assumptions
    expense_growth_rate: float = Field(default=0.03, ge=0, le=0.20)

    # Exit assumptions
    exit_cap_rate: float = Field(default=0.055, ge=0.02, le=0.15, description="Cap rate applied at sale")
    selling_costs_pct: float = Field(default=0.05, ge=0, le=0.15, description="Broker + transfer taxes at exit")

    # Return requirements
    discount_rate: float = Field(default=0.08, ge=0.01, le=0.30, description="Target return for NPV")

    # Other income
    other_income_annual: float = Field(
        default=0.0, ge=0,
        description="Laundry, storage, parking, etc."
    )

    # Capital expenditure reserve (not included in OpEx unless added as expense line)
    capex_reserve_per_unit_annual: float = Field(default=500.0, ge=0)


class PropertyInput(BaseModel):
    """
    Complete property input model. The top-level object passed to all financial services.

    A valid analysis requires:
      - At least one unit in `units`
      - purchase_price > 0
      - A loan (optional — for all-cash analysis, omit)
      - At least some expense line items
    """

    name: str = Field(default="")
    address: str = Field(default="")
    borough: Borough = Borough.BROOKLYN
    year_built: Optional[int] = Field(default=None, ge=1800, le=2030)
    gross_sq_ft: Optional[float] = Field(default=None, gt=0)

    num_units: int = Field(gt=0, le=500)
    purchase_price: float = Field(gt=0)
    closing_costs: float = Field(default=0.0, ge=0)
    renovation_budget_total: float = Field(default=0.0, ge=0)

    units: list[UnitInput] = Field(default_factory=list)
    loan: Optional[LoanInput] = None
    expenses: list[ExpenseInput] = Field(default_factory=list)
    assumptions: AssumptionInput = Field(default_factory=AssumptionInput)

    @property
    def total_cash_invested(self) -> float:
        """Down payment + closing costs + renovation budget."""
        down_payment = self.purchase_price - (self.loan.loan_amount if self.loan else 0)
        return down_payment + self.closing_costs + self.renovation_budget_total

    @property
    def down_payment(self) -> float:
        if self.loan:
            return self.purchase_price - self.loan.loan_amount
        return self.purchase_price

    @model_validator(mode="after")
    def validate_loan_vs_price(self) -> "PropertyInput":
        if self.loan and self.loan.loan_amount >= self.purchase_price:
            raise ValueError("Loan amount must be less than purchase price")
        return self
