"""
Reference data endpoints — static data served without auth.

These power the contextual UI elements:
  - RGB order chart (historical rent increase orders)
  - Borough expense benchmarks (typical NYC operating costs)
  - Metric explanations (tooltip content for the frontend)
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/reference", tags=["reference"])


# ---------------------------------------------------------------------------
# NYC Rent Guidelines Board historical orders
# Source: nyc.gov/rgborders — one-year lease increases
# ---------------------------------------------------------------------------

RGB_ORDERS = [
    {"year": 2024, "one_year": 0.0275, "two_year": 0.0525},
    {"year": 2023, "one_year": 0.0300, "two_year": 0.0550},
    {"year": 2022, "one_year": 0.0325, "two_year": 0.0500},
    {"year": 2021, "one_year": 0.0000, "two_year": 0.0025},  # COVID zero increase
    {"year": 2020, "one_year": 0.0150, "two_year": 0.0250},
    {"year": 2019, "one_year": 0.0150, "two_year": 0.0250},
    {"year": 2018, "one_year": 0.0150, "two_year": 0.0250},
    {"year": 2017, "one_year": 0.0000, "two_year": 0.0200},
    {"year": 2016, "one_year": 0.0000, "two_year": 0.0200},
    {"year": 2015, "one_year": 0.0100, "two_year": 0.0250},
    {"year": 2014, "one_year": 0.0100, "two_year": 0.0275},
    {"year": 2013, "one_year": 0.0400, "two_year": 0.0775},
    {"year": 2012, "one_year": 0.0300, "two_year": 0.0600},
    {"year": 2011, "one_year": 0.0375, "two_year": 0.0700},
    {"year": 2010, "one_year": 0.0250, "two_year": 0.0450},
    {"year": 2009, "one_year": 0.0300, "two_year": 0.0600},
    {"year": 2008, "one_year": 0.0475, "two_year": 0.0875},
    {"year": 2007, "one_year": 0.0375, "two_year": 0.0875},
    {"year": 2006, "one_year": 0.0225, "two_year": 0.0450},
    {"year": 2005, "one_year": 0.0350, "two_year": 0.0700},
]


# ---------------------------------------------------------------------------
# Borough expense benchmarks ($/unit/year estimates for NYC multifamily)
# These are representative estimates for portfolio modeling purposes
# ---------------------------------------------------------------------------

EXPENSE_BENCHMARKS = {
    "manhattan": {
        "property_tax": 22_000,
        "insurance": 10_000,
        "water_sewer": 8_000,
        "heat": 9_000,
        "electric": 4_000,
        "repairs": 1_200,
        "payroll": 18_000,
        "management": 8_000,
        "legal_accounting": 3_500,
        "capex_reserve": 800,
        "misc": 3_000,
        "note": "Per-unit estimates. Manhattan values are highest in NYC.",
    },
    "brooklyn": {
        "property_tax": 14_000,
        "insurance": 7_000,
        "water_sewer": 6_500,
        "heat": 7_000,
        "electric": 3_000,
        "repairs": 900,
        "payroll": 12_000,
        "management": 6_000,
        "legal_accounting": 2_500,
        "capex_reserve": 600,
        "misc": 2_000,
        "note": "Per-unit estimates. Brooklyn varies widely by neighborhood.",
    },
    "queens": {
        "property_tax": 11_000,
        "insurance": 6_000,
        "water_sewer": 5_500,
        "heat": 6_500,
        "electric": 2_500,
        "repairs": 800,
        "payroll": 10_000,
        "management": 5_000,
        "legal_accounting": 2_000,
        "capex_reserve": 500,
        "misc": 1_800,
        "note": "Per-unit estimates.",
    },
    "bronx": {
        "property_tax": 10_000,
        "insurance": 5_500,
        "water_sewer": 5_000,
        "heat": 8_000,
        "electric": 2_200,
        "repairs": 900,
        "payroll": 9_000,
        "management": 4_500,
        "legal_accounting": 2_000,
        "capex_reserve": 500,
        "misc": 1_500,
        "note": "Heat costs tend to be high in older Bronx buildings (pre-war radiators).",
    },
    "staten_island": {
        "property_tax": 9_000,
        "insurance": 5_000,
        "water_sewer": 4_500,
        "heat": 5_500,
        "electric": 2_000,
        "repairs": 700,
        "payroll": 8_000,
        "management": 4_000,
        "legal_accounting": 1_800,
        "capex_reserve": 500,
        "misc": 1_200,
        "note": "Lower expense base than other boroughs.",
    },
}


# ---------------------------------------------------------------------------
# Metric definitions (tooltip content for the frontend)
# ---------------------------------------------------------------------------

METRIC_DEFINITIONS = {
    "gsi": {
        "name": "Gross Scheduled Income",
        "formula": "Σ(unit_rent × 12) at 100% occupancy",
        "interpretation": "Maximum annual rent if every unit is occupied all year",
        "healthy_range": "N/A — depends on market",
    },
    "egi": {
        "name": "Effective Gross Income",
        "formula": "GSI × (1 − vacancy_rate) + other_income",
        "interpretation": "Realistic annual income after vacancy",
        "healthy_range": "N/A",
    },
    "noi": {
        "name": "Net Operating Income",
        "formula": "EGI − Operating Expenses",
        "interpretation": "Building income before debt service. The most important number in multifamily.",
        "healthy_range": "N/A — depends on purchase price",
    },
    "cap_rate": {
        "name": "Capitalization Rate",
        "formula": "NOI / Purchase Price",
        "interpretation": "Unlevered yield on the asset. NYC multifamily: 3–6%.",
        "healthy_range": "NYC: 3.5–6%; below 3.5% is very compressed",
    },
    "dscr": {
        "name": "Debt Service Coverage Ratio",
        "formula": "NOI / Annual Debt Service",
        "interpretation": "How many times NOI covers the mortgage payment. Below 1.0x means the property can't pay its own debt.",
        "healthy_range": "> 1.25x (lender minimum); > 1.35x preferred",
    },
    "coc_return": {
        "name": "Cash-on-Cash Return",
        "formula": "(NOI − Annual Debt Service) / Total Cash Invested",
        "interpretation": "Annual cash yield on your equity investment",
        "healthy_range": "NYC: 4–8%; below 2% is poor; above 8% is exceptional",
    },
    "break_even_occupancy": {
        "name": "Break-Even Occupancy",
        "formula": "(Operating Expenses + Debt Service) / GSI",
        "interpretation": "Minimum occupancy rate to cover all costs. Lower is safer.",
        "healthy_range": "< 85%; above 90% is dangerous",
    },
    "expense_ratio": {
        "name": "Expense Ratio",
        "formula": "Operating Expenses / EGI",
        "interpretation": "Fraction of income consumed by expenses. Lower is more efficient.",
        "healthy_range": "NYC: 35–55%; above 65% is a red flag",
    },
    "ltv": {
        "name": "Loan-to-Value",
        "formula": "Loan Amount / Purchase Price",
        "interpretation": "Leverage level. Higher LTV = more risk, higher potential returns.",
        "healthy_range": "≤ 75% preferred; ≤ 80% for most lenders",
    },
    "irr": {
        "name": "Internal Rate of Return",
        "formula": "Rate r such that NPV of all cash flows = 0",
        "interpretation": "Annualized return on equity over the holding period including appreciation",
        "healthy_range": "> 10% is above hurdle; > 15% is strong",
    },
    "equity_multiple": {
        "name": "Equity Multiple",
        "formula": "(Total Cash Returned + Initial Equity) / Initial Equity",
        "interpretation": "Total dollar multiple on invested capital over the holding period",
        "healthy_range": "> 1.5x for 10 years; > 2.0x is strong",
    },
}


@router.get("/rgb-orders")
async def get_rgb_orders():
    """NYC Rent Guidelines Board historical annual increase orders."""
    avg_1yr = sum(r["one_year"] for r in RGB_ORDERS) / len(RGB_ORDERS)
    return {
        "orders": RGB_ORDERS,
        "historical_average_one_year": round(avg_1yr, 4),
        "latest": RGB_ORDERS[0],
        "note": "RGB orders set maximum annual increases for rent-stabilized units in NYC.",
    }


@router.get("/expense-benchmarks/{borough}")
async def get_expense_benchmarks(borough: str):
    """Per-unit annual expense benchmarks for NYC multifamily by borough."""
    borough = borough.lower().replace("-", "_").replace(" ", "_")
    benchmarks = EXPENSE_BENCHMARKS.get(borough)
    if not benchmarks:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"No benchmarks for borough: {borough}")
    return {"borough": borough, "benchmarks": benchmarks}


@router.get("/expense-benchmarks")
async def get_all_benchmarks():
    """All borough benchmarks for comparison."""
    return {"boroughs": EXPENSE_BENCHMARKS}


@router.get("/metrics")
async def get_metric_definitions():
    """Plain-English definitions for all financial metrics — used for tooltips."""
    return {"metrics": METRIC_DEFINITIONS}


@router.get("/preset-scenarios")
async def get_preset_scenarios():
    """Available preset scenario templates with their override parameters."""
    return {
        "presets": [
            {"type": "base", "name": "Base Case", "description": "No overrides — uses property assumptions", "overrides": {}},
            {"type": "optimistic", "name": "Bull Case", "description": "Higher rents, lower vacancy, lower exit cap", "overrides": {"fm_rent_growth_rate": 0.04, "general_vacancy_rate": 0.03, "exit_cap_rate": 0.045}},
            {"type": "pessimistic", "name": "Bear Case", "description": "Flat rents, higher vacancy, higher exit cap", "overrides": {"fm_rent_growth_rate": 0.01, "general_vacancy_rate": 0.08, "exit_cap_rate": 0.07}},
            {"type": "rent_freeze", "name": "Rent Freeze", "description": "0% rent growth — NYC political risk scenario", "overrides": {"fm_rent_growth_rate": 0.0, "rs_rent_growth_rate": 0.0}},
            {"type": "high_rates", "name": "Higher Rates", "description": "Exit at higher cap rate — refinancing risk", "overrides": {"exit_cap_rate": 0.08}},
            {"type": "high_vacancy", "name": "High Vacancy", "description": "Recession vacancy scenario", "overrides": {"general_vacancy_rate": 0.12}},
        ]
    }
