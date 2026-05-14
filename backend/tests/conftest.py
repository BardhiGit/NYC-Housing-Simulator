"""
Shared test fixtures for the financial model test suite.

Fixtures are organized from simple to complex:
  - minimal_loan, minimal_property: smallest valid inputs for unit tests
  - seed_bronx, seed_brooklyn, seed_queens: full realistic NYC properties
  - all_seed_properties: list for parametrized tests

Design principle: fixtures mirror real NYC market conditions so that
test assertions are meaningful, not just "output is not None".
"""

from __future__ import annotations

import pytest

from app.models.inputs import (
    AssumptionInput,
    Borough,
    ExpenseCategory,
    ExpenseInput,
    LoanInput,
    PropertyInput,
    RentType,
    UnitInput,
)
from data.seed_data import bronx_rs_trap, brooklyn_appreciation_play, queens_best_case


# ---------------------------------------------------------------------------
# Primitive fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def standard_loan() -> LoanInput:
    """$1,000,000 at 6.5% for 30 years — standard NYC acquisition financing."""
    return LoanInput(loan_amount=1_000_000, interest_rate=0.065, term_years=30)


@pytest.fixture
def io_loan() -> LoanInput:
    """$1,000,000 at 6.5%, 3-year IO then 27-year amortization."""
    return LoanInput(
        loan_amount=1_000_000,
        interest_rate=0.065,
        term_years=30,
        amortization_years=30,
        io_period_years=3,
    )


@pytest.fixture
def balloon_loan() -> LoanInput:
    """$1,000,000 at 6.5%, 10-year balloon, amortizes over 30 years."""
    return LoanInput(
        loan_amount=1_000_000,
        interest_rate=0.065,
        term_years=10,
        amortization_years=30,
    )


@pytest.fixture
def simple_stabilized_unit() -> UnitInput:
    return UnitInput(
        unit_number="1A",
        bedrooms=2,
        rent_type=RentType.STABILIZED,
        current_rent=1_500,
        legal_rent=1_600,
    )


@pytest.fixture
def simple_fm_unit() -> UnitInput:
    return UnitInput(
        unit_number="2A",
        bedrooms=2,
        rent_type=RentType.FREE_MARKET,
        current_rent=2_800,
        market_rent_est=2_800,
    )


@pytest.fixture
def vacant_unit() -> UnitInput:
    return UnitInput(
        unit_number="3A",
        bedrooms=1,
        rent_type=RentType.VACANT,
        current_rent=0,
        market_rent_est=2_000,
    )


# ---------------------------------------------------------------------------
# Simple 2-unit property for isolated formula testing
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_property() -> PropertyInput:
    """
    2-unit property: 1 RS + 1 FM.
    Clean, predictable numbers for verifying formula correctness.
    """
    return PropertyInput(
        name="Test Property",
        address="1 Test St, Brooklyn, NY",
        borough=Borough.BROOKLYN,
        num_units=2,
        purchase_price=800_000,
        closing_costs=24_000,
        units=[
            UnitInput(
                unit_number="1", bedrooms=2, rent_type=RentType.STABILIZED,
                current_rent=1_500, legal_rent=1_600,
            ),
            UnitInput(
                unit_number="2", bedrooms=2, rent_type=RentType.FREE_MARKET,
                current_rent=2_500,
            ),
        ],
        loan=LoanInput(
            loan_amount=640_000,
            interest_rate=0.065,
            term_years=30,
        ),
        expenses=[
            ExpenseInput(category=ExpenseCategory.PROPERTY_TAX, annual_amount=12_000),
            ExpenseInput(category=ExpenseCategory.INSURANCE, annual_amount=4_000),
            ExpenseInput(category=ExpenseCategory.WATER_SEWER, annual_amount=3_600),
            ExpenseInput(category=ExpenseCategory.HEAT, annual_amount=3_000),
            ExpenseInput(category=ExpenseCategory.REPAIRS, annual_amount=2_400),
            ExpenseInput(category=ExpenseCategory.MANAGEMENT, annual_amount=4_800),
            ExpenseInput(category=ExpenseCategory.MISC, annual_amount=1_200),
        ],
        assumptions=AssumptionInput(
            holding_period=10,
            general_vacancy_rate=0.05,
            fm_rent_growth_rate=0.03,
            rs_rent_growth_rate=0.028,
            expense_growth_rate=0.03,
            exit_cap_rate=0.055,
            discount_rate=0.08,
        ),
    )


@pytest.fixture
def all_cash_property(simple_property) -> PropertyInput:
    """Same as simple_property but purchased with all cash (no loan)."""
    p = simple_property.model_copy(deep=True)
    p.loan = None
    return p


# ---------------------------------------------------------------------------
# Seed property fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def seed_bronx() -> PropertyInput:
    return bronx_rs_trap()


@pytest.fixture
def seed_brooklyn() -> PropertyInput:
    return brooklyn_appreciation_play()


@pytest.fixture
def seed_queens() -> PropertyInput:
    return queens_best_case()


@pytest.fixture(params=["bronx", "brooklyn", "queens"])
def all_seed_properties(request) -> PropertyInput:
    """Parametrized fixture — runs tests against all three seed properties."""
    return {
        "bronx": bronx_rs_trap(),
        "brooklyn": brooklyn_appreciation_play(),
        "queens": queens_best_case(),
    }[request.param]
