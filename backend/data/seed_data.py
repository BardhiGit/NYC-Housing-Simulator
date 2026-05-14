"""
Seed data: three realistic NYC multifamily properties with deliberate stories.

Property 1 — Bronx, 6-unit, RS-heavy:
  "The RS Trap" — priced attractively at $900K but the rent-stabilized units
  cap income growth permanently. Negative cash flow illustrates why RS buildings
  in the Bronx are hard to underwrite at today's rates.

Property 2 — Brooklyn, 12-unit, mixed RS/FM:
  "The Appreciation Play" — a Bushwick walkup that looks reasonable at a 4.2% cap
  but is deeply cash-flow negative once debt service is applied. Investors buy these
  hoping for long-term appreciation and free-market unit turnover.

Property 3 — Queens, 4-unit, FM-heavy:
  "The Best NYC Can Offer" — a distressed acquisition in Jackson Heights with
  mostly FM units. After a renovation, it's cash-flow positive — barely.
  Represents the ceiling of what NYC yields can realistically look like.

All numbers are approximate estimates for educational purposes.
"""

from __future__ import annotations

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


def bronx_rs_trap() -> PropertyInput:
    """
    6-unit Bronx walkup, all rent-stabilized.
    Purchase price: $900,000. Year built: 1952.
    The story: attractive price point, but RS caps make it a cash-flow trap
    at 2024 interest rates.
    """
    units = [
        UnitInput(unit_number="1F", bedrooms=2, bathrooms=1.0, sq_ft=750,
                  rent_type=RentType.STABILIZED,
                  current_rent=1_350, legal_rent=1_400, market_rent_est=2_200),
        UnitInput(unit_number="1R", bedrooms=1, bathrooms=1.0, sq_ft=600,
                  rent_type=RentType.STABILIZED,
                  current_rent=1_100, legal_rent=1_100, market_rent_est=1_700),
        UnitInput(unit_number="2F", bedrooms=2, bathrooms=1.0, sq_ft=750,
                  rent_type=RentType.STABILIZED,
                  current_rent=1_280, legal_rent=1_350, market_rent_est=2_200,
                  preferential_rent=1_280),
        UnitInput(unit_number="2R", bedrooms=1, bathrooms=1.0, sq_ft=600,
                  rent_type=RentType.STABILIZED,
                  current_rent=980, legal_rent=1_200, market_rent_est=1_700,
                  preferential_rent=980),
        UnitInput(unit_number="3F", bedrooms=2, bathrooms=1.0, sq_ft=750,
                  rent_type=RentType.STABILIZED,
                  current_rent=1_420, legal_rent=1_420, market_rent_est=2_200),
        UnitInput(unit_number="3R", bedrooms=2, bathrooms=1.0, sq_ft=700,
                  rent_type=RentType.STABILIZED,
                  current_rent=1_260, legal_rent=1_300, market_rent_est=2_100),
    ]

    expenses = [
        ExpenseInput(category=ExpenseCategory.PROPERTY_TAX, annual_amount=14_400),
        ExpenseInput(category=ExpenseCategory.INSURANCE, annual_amount=5_200),
        ExpenseInput(category=ExpenseCategory.WATER_SEWER, annual_amount=6_800),
        ExpenseInput(category=ExpenseCategory.HEAT, annual_amount=9_600,
                     notes="Landlord-paid heat, pre-war building"),
        ExpenseInput(category=ExpenseCategory.ELECTRIC, annual_amount=1_800,
                     notes="Common areas only"),
        ExpenseInput(category=ExpenseCategory.REPAIRS, annual_amount=5_400,
                     notes="$900/unit — aging building"),
        ExpenseInput(category=ExpenseCategory.MANAGEMENT, annual_amount=7_800,
                     notes="10% of GSI"),
        ExpenseInput(category=ExpenseCategory.LEGAL_ACCOUNTING, annual_amount=2_400),
        ExpenseInput(category=ExpenseCategory.CAPEX_RESERVE, annual_amount=3_000,
                     notes="$500/unit/yr"),
        ExpenseInput(category=ExpenseCategory.MISC, annual_amount=1_800),
    ]

    return PropertyInput(
        name="137 Grant Ave — Bronx RS Study",
        address="137 Grant Ave, Bronx, NY 10456",
        borough=Borough.BRONX,
        year_built=1952,
        gross_sq_ft=4_200,
        num_units=6,
        purchase_price=900_000,
        closing_costs=27_000,     # ~3% closing costs
        renovation_budget_total=0,
        units=units,
        loan=LoanInput(
            loan_amount=720_000,  # 80% LTV
            interest_rate=0.0695,
            term_years=30,
            amortization_years=30,
        ),
        expenses=expenses,
        assumptions=AssumptionInput(
            holding_period=10,
            general_vacancy_rate=0.04,    # NYC vacancy is tight
            fm_rent_growth_rate=0.03,
            rs_rent_growth_rate=0.028,    # RGB historical average
            expense_growth_rate=0.035,    # NYC expenses inflate faster than CPI
            exit_cap_rate=0.055,
            selling_costs_pct=0.05,
            discount_rate=0.08,
            other_income_annual=1_200,   # laundry
            capex_reserve_per_unit_annual=500,
        ),
    )


def brooklyn_appreciation_play() -> PropertyInput:
    """
    12-unit Bushwick walkup, 8 RS + 4 FM units.
    Purchase price: $3,200,000. Year built: 1962.
    The story: Brooklyn appreciation play. Cap rate is 4.2% — acceptable for
    the market — but DSCR is 0.76x. Investor needs strong balance sheet
    and patience for FM units to turn over.
    """
    units = [
        # RS units (8) — typical Bushwick stabilized rents
        UnitInput(unit_number="1A", bedrooms=1, bathrooms=1.0, sq_ft=650,
                  rent_type=RentType.STABILIZED,
                  current_rent=1_450, legal_rent=1_500, market_rent_est=2_400),
        UnitInput(unit_number="1B", bedrooms=2, bathrooms=1.0, sq_ft=850,
                  rent_type=RentType.STABILIZED,
                  current_rent=1_680, legal_rent=1_750, market_rent_est=3_000),
        UnitInput(unit_number="2A", bedrooms=1, bathrooms=1.0, sq_ft=650,
                  rent_type=RentType.STABILIZED,
                  current_rent=1_390, legal_rent=1_600, market_rent_est=2_400,
                  preferential_rent=1_390),
        UnitInput(unit_number="2B", bedrooms=2, bathrooms=1.0, sq_ft=850,
                  rent_type=RentType.STABILIZED,
                  current_rent=1_600, legal_rent=1_750, market_rent_est=3_000),
        UnitInput(unit_number="3A", bedrooms=1, bathrooms=1.0, sq_ft=650,
                  rent_type=RentType.STABILIZED,
                  current_rent=1_520, legal_rent=1_520, market_rent_est=2_400),
        UnitInput(unit_number="3B", bedrooms=2, bathrooms=1.0, sq_ft=850,
                  rent_type=RentType.STABILIZED,
                  current_rent=1_710, legal_rent=1_710, market_rent_est=3_000),
        UnitInput(unit_number="4A", bedrooms=1, bathrooms=1.0, sq_ft=650,
                  rent_type=RentType.STABILIZED,
                  current_rent=1_480, legal_rent=1_560, market_rent_est=2_400,
                  preferential_rent=1_480),
        UnitInput(unit_number="4B", bedrooms=2, bathrooms=1.0, sq_ft=850,
                  rent_type=RentType.STABILIZED,
                  current_rent=1_650, legal_rent=1_800, market_rent_est=3_000),
        # FM units (4) — recently renovated, higher rents
        UnitInput(unit_number="5A", bedrooms=1, bathrooms=1.0, sq_ft=650,
                  rent_type=RentType.FREE_MARKET,
                  current_rent=2_450, market_rent_est=2_450),
        UnitInput(unit_number="5B", bedrooms=2, bathrooms=1.0, sq_ft=900,
                  rent_type=RentType.FREE_MARKET,
                  current_rent=3_200, market_rent_est=3_200),
        UnitInput(unit_number="6A", bedrooms=1, bathrooms=1.0, sq_ft=650,
                  rent_type=RentType.FREE_MARKET,
                  current_rent=2_350, market_rent_est=2_500),
        UnitInput(unit_number="6B", bedrooms=2, bathrooms=1.0, sq_ft=900,
                  rent_type=RentType.FREE_MARKET,
                  current_rent=3_100, market_rent_est=3_200),
    ]

    expenses = [
        ExpenseInput(category=ExpenseCategory.PROPERTY_TAX, annual_amount=42_000,
                     notes="NYC Class 2, assessed above typical for Brooklyn"),
        ExpenseInput(category=ExpenseCategory.INSURANCE, annual_amount=14_400),
        ExpenseInput(category=ExpenseCategory.WATER_SEWER, annual_amount=11_200),
        ExpenseInput(category=ExpenseCategory.HEAT, annual_amount=9_600,
                     notes="Gas heat, landlord-paid"),
        ExpenseInput(category=ExpenseCategory.ELECTRIC, annual_amount=4_200),
        ExpenseInput(category=ExpenseCategory.REPAIRS, annual_amount=10_800,
                     notes="$900/unit average"),
        ExpenseInput(category=ExpenseCategory.PAYROLL, annual_amount=14_400,
                     notes="Part-time super"),
        ExpenseInput(category=ExpenseCategory.MANAGEMENT, annual_amount=14_000,
                     notes="~5% of GSI"),
        ExpenseInput(category=ExpenseCategory.LEGAL_ACCOUNTING, annual_amount=5_000),
        ExpenseInput(category=ExpenseCategory.CAPEX_RESERVE, annual_amount=6_000,
                     notes="$500/unit/yr"),
        ExpenseInput(category=ExpenseCategory.MISC, annual_amount=4_800),
    ]

    return PropertyInput(
        name="447 Myrtle Ave — Brooklyn Mixed",
        address="447 Myrtle Ave, Brooklyn, NY 11205",
        borough=Borough.BROOKLYN,
        year_built=1962,
        gross_sq_ft=10_200,
        num_units=12,
        purchase_price=3_200_000,
        closing_costs=96_000,     # ~3%
        renovation_budget_total=0,
        units=units,
        loan=LoanInput(
            loan_amount=2_560_000,  # 80% LTV
            interest_rate=0.068,
            term_years=30,
            amortization_years=30,
        ),
        expenses=expenses,
        assumptions=AssumptionInput(
            holding_period=10,
            general_vacancy_rate=0.045,
            fm_rent_growth_rate=0.035,   # Bushwick has strong FM rent growth
            rs_rent_growth_rate=0.028,
            expense_growth_rate=0.035,
            exit_cap_rate=0.05,          # cap rate compression assumption (appreciation)
            selling_costs_pct=0.05,
            discount_rate=0.08,
            other_income_annual=2_400,   # laundry + storage
            capex_reserve_per_unit_annual=500,
        ),
    )


def queens_best_case() -> PropertyInput:
    """
    4-unit Jackson Heights, 1 RS + 3 FM units.
    Purchase price: $1,050,000 (distressed seller). Year built: 1955.
    The story: the best realistic NYC deal — positive cash flow by year 3,
    IRR ~9% over 10 years. Still tight, but this is what NYC ceiling looks like.
    """
    units = [
        UnitInput(unit_number="1F", bedrooms=2, bathrooms=1.0, sq_ft=800,
                  rent_type=RentType.STABILIZED,
                  current_rent=1_550, legal_rent=1_600, market_rent_est=2_500),
        UnitInput(unit_number="2F", bedrooms=2, bathrooms=1.0, sq_ft=800,
                  rent_type=RentType.FREE_MARKET,
                  current_rent=2_400, market_rent_est=2_500),
        UnitInput(unit_number="2R", bedrooms=1, bathrooms=1.0, sq_ft=650,
                  rent_type=RentType.FREE_MARKET,
                  current_rent=1_950, market_rent_est=2_100),
        UnitInput(unit_number="3F", bedrooms=2, bathrooms=1.0, sq_ft=800,
                  rent_type=RentType.VACANT,
                  current_rent=0, market_rent_est=2_500,
                  renovation_budget=15_000,
                  notes="Vacant — needs kitchen renovation before re-letting"),
    ]

    expenses = [
        ExpenseInput(category=ExpenseCategory.PROPERTY_TAX, annual_amount=11_200),
        ExpenseInput(category=ExpenseCategory.INSURANCE, annual_amount=5_800),
        ExpenseInput(category=ExpenseCategory.WATER_SEWER, annual_amount=5_200),
        ExpenseInput(category=ExpenseCategory.HEAT, annual_amount=4_800,
                     notes="Gas heat, landlord-paid"),
        ExpenseInput(category=ExpenseCategory.ELECTRIC, annual_amount=1_600),
        ExpenseInput(category=ExpenseCategory.REPAIRS, annual_amount=3_200,
                     notes="$800/unit — good condition"),
        ExpenseInput(category=ExpenseCategory.MANAGEMENT, annual_amount=4_200,
                     notes="Self-managed, minimal"),
        ExpenseInput(category=ExpenseCategory.LEGAL_ACCOUNTING, annual_amount=2_000),
        ExpenseInput(category=ExpenseCategory.CAPEX_RESERVE, annual_amount=2_000,
                     notes="$500/unit/yr"),
        ExpenseInput(category=ExpenseCategory.MISC, annual_amount=1_200),
    ]

    return PropertyInput(
        name="82-15 Baxter Ave — Queens Best Case",
        address="82-15 Baxter Ave, Jackson Heights, NY 11372",
        borough=Borough.QUEENS,
        year_built=1955,
        gross_sq_ft=3_250,
        num_units=4,
        purchase_price=1_050_000,
        closing_costs=31_500,   # 3%
        renovation_budget_total=15_000,   # unit 3F renovation
        units=units,
        loan=LoanInput(
            loan_amount=787_500,   # 75% LTV — lower leverage for better DSCR
            interest_rate=0.0675,
            term_years=30,
            amortization_years=30,
        ),
        expenses=expenses,
        assumptions=AssumptionInput(
            holding_period=10,
            general_vacancy_rate=0.05,
            fm_rent_growth_rate=0.03,
            rs_rent_growth_rate=0.028,
            expense_growth_rate=0.03,
            exit_cap_rate=0.055,
            selling_costs_pct=0.05,
            discount_rate=0.08,
            other_income_annual=1_200,
            capex_reserve_per_unit_annual=500,
        ),
    )


def get_all_seed_properties() -> list[PropertyInput]:
    """Return all three seed properties for testing and API seeding."""
    return [
        bronx_rs_trap(),
        brooklyn_appreciation_play(),
        queens_best_case(),
    ]
