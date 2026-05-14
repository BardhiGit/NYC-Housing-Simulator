"""
Output data models — structured results returned by all financial services.

All monetary values are USD. Rates are decimal fractions unless noted.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Core Financial Results
# ---------------------------------------------------------------------------

class IncomeMetrics(BaseModel):
    gross_scheduled_income: float       # Annual GSI at 100% occupancy
    vacancy_loss: float                 # Annual dollar amount lost to vacancy
    effective_gross_income: float       # EGI = GSI × (1 - vacancy_rate)
    other_income: float                 # Laundry, storage, parking
    total_income: float                 # EGI + other_income


class OperatingMetrics(BaseModel):
    total_operating_expenses: float
    expense_by_category: dict[str, float]
    net_operating_income: float         # NOI = EGI - OpEx
    expense_ratio: float                # OpEx / EGI  (healthy NYC: 35-55%)


class DebtMetrics(BaseModel):
    monthly_payment: float
    annual_debt_service: float
    year1_interest: float               # Interest portion of first annual payment
    year1_principal: float              # Principal portion of first annual payment
    dscr: float                         # NOI / ADS  (lender min: 1.25x)
    loan_to_value: float                # Loan / Purchase Price


class ReturnMetrics(BaseModel):
    cash_flow_before_tax: float         # NOI - Annual Debt Service
    cash_on_cash_return: float          # CF / Total Cash Invested
    cap_rate: float                     # NOI / Purchase Price
    total_cash_invested: float          # Down payment + closing + renovation
    equity_at_purchase: float           # Purchase price - loan amount


class ValuationMetrics(BaseModel):
    price_per_unit: float
    price_per_sq_ft: Optional[float]
    implied_value_at_cap: float         # NOI / market_cap_rate (income approach)


class BreakEvenMetrics(BaseModel):
    break_even_occupancy: float         # (OpEx + ADS) / GSI — must be < 1
    break_even_rent: float              # Monthly rent per unit at current occupancy for break-even


class RentRollSummary(BaseModel):
    num_stabilized: int
    num_free_market: int
    num_vacant: int
    num_owner_occupied: int
    rs_percentage: float                # RS units / total rentable units
    monthly_gsi: float
    annual_gsi: float
    avg_rent_stabilized: Optional[float]
    avg_rent_free_market: Optional[float]
    total_market_rent_estimate: Optional[float]   # If all units were market rate
    stabilization_discount: Optional[float]       # GSI - total_market_rent_estimate


class FullFinancialResult(BaseModel):
    income: IncomeMetrics
    operating: OperatingMetrics
    debt: Optional[DebtMetrics]         # None for all-cash purchases
    returns: ReturnMetrics
    valuation: ValuationMetrics
    break_even: BreakEvenMetrics
    rent_roll: RentRollSummary


# ---------------------------------------------------------------------------
# Amortization Schedule
# ---------------------------------------------------------------------------

class AmortizationRow(BaseModel):
    month: int
    year: int
    payment: float
    principal: float
    interest: float
    balance: float
    cumulative_interest: float
    cumulative_principal: float


class AnnualAmortizationSummary(BaseModel):
    year: int
    total_payment: float
    total_interest: float
    total_principal: float
    year_end_balance: float
    interest_pct_of_payment: float      # Useful for visualizing P&I split over time


class AmortizationSchedule(BaseModel):
    monthly_payment: float
    total_interest: float
    total_principal: float
    rows: list[AmortizationRow]
    annual_summary: list[AnnualAmortizationSummary]


# ---------------------------------------------------------------------------
# Multi-Year Projection
# ---------------------------------------------------------------------------

class YearlyProjection(BaseModel):
    year: int
    gsi: float
    egi: float
    operating_expenses: float
    noi: float
    debt_service: float
    cash_flow: float
    loan_balance: float
    property_value: float               # NOI / exit_cap_rate (income approach)
    equity: float                       # property_value - loan_balance
    cumulative_cash_flow: float
    dscr: float
    cap_rate: float                     # NOI / original_purchase_price
    coc_return: float                   # cash_flow / total_cash_invested


class ProjectionResult(BaseModel):
    years: list[YearlyProjection]
    holding_period: int
    exit_year: int
    exit_property_value: float
    exit_loan_balance: float
    exit_selling_costs: float
    exit_net_proceeds: float            # exit_value - selling_costs - loan_balance
    total_operating_cash_flow: float    # Sum of annual cash flows
    total_return: float                 # total_operating_cash_flow + exit_net_proceeds
    equity_multiple: float              # (total_return + initial_equity) / initial_equity
    irr: float                          # Internal rate of return on equity
    npv: float                          # NPV at discount rate


# ---------------------------------------------------------------------------
# Monte Carlo Simulation
# ---------------------------------------------------------------------------

class MonteCarloParams(BaseModel):
    n_iterations: int = 10_000

    vacancy_mean: float
    vacancy_std: float = 0.025
    vacancy_min: float = 0.0
    vacancy_max: float = 0.30

    fm_rent_growth_mean: float
    fm_rent_growth_std: float = 0.015
    fm_rent_growth_min: float = -0.05
    fm_rent_growth_max: float = 0.12

    rs_rent_growth_mean: float = 0.025
    rs_rent_growth_std: float = 0.01
    rs_rent_growth_min: float = 0.0
    rs_rent_growth_max: float = 0.08

    expense_growth_mean: float
    expense_growth_std: float = 0.012
    expense_growth_min: float = 0.0
    expense_growth_max: float = 0.12

    exit_cap_mean: float
    exit_cap_std: float = 0.005
    exit_cap_min: float = 0.03
    exit_cap_max: float = 0.14

    # Renovation cost overrun: multiplier on budget (lognormal, right-skewed)
    reno_overrun_mean_log: float = 0.10    # Expected 10% overrun
    reno_overrun_std_log: float = 0.30


class DistributionStats(BaseModel):
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float
    mean: float
    std: float
    min_val: float
    max_val: float


class MonteCarloResults(BaseModel):
    n_iterations: int
    irr: DistributionStats
    coc_year1: DistributionStats
    min_dscr: DistributionStats         # Worst annual DSCR across holding period
    total_return: DistributionStats

    p_negative_cashflow_yr1: float      # Probability CF < 0 in year 1
    p_dscr_below_1: float               # Probability any year DSCR < 1.0
    p_dscr_below_125: float             # Probability any year DSCR < 1.25
    p_negative_irr: float               # Probability IRR < 0

    # Scenario snapshots
    worst_case: dict                    # p10 IRR scenario
    median_case: dict                   # p50 IRR scenario
    best_case: dict                     # p90 IRR scenario

    # Raw distributions (truncated for API response)
    irr_histogram: list[float]          # 200-point histogram data
    coc_histogram: list[float]
    total_return_histogram: list[float]


# ---------------------------------------------------------------------------
# Sensitivity Analysis
# ---------------------------------------------------------------------------

class SensitivityPoint(BaseModel):
    variable: str
    display_name: str
    base_value: float
    low_value: float        # base × 0.80
    high_value: float       # base × 1.20
    base_metric: float
    low_metric: float
    high_metric: float
    swing: float            # abs(high_metric - low_metric) — determines tornado bar width
    direction: str          # "positive" (metric up when var up) or "inverse"


class TornadoChartData(BaseModel):
    target_metric: str                  # "coc_return", "irr", "dscr", "noi"
    base_value: float
    variables: list[SensitivityPoint]   # Sorted by abs(swing) descending


class HeatmapCell(BaseModel):
    x_value: float
    y_value: float
    metric_value: float


class SensitivityHeatmap(BaseModel):
    x_variable: str
    y_variable: str
    target_metric: str
    cells: list[HeatmapCell]
    x_values: list[float]
    y_values: list[float]


# ---------------------------------------------------------------------------
# Investment Quality Score
# ---------------------------------------------------------------------------

class ScoreComponent(BaseModel):
    name: str
    display_name: str
    score: float
    max_score: float
    raw_value: float                    # The actual metric (e.g., 0.048 for 4.8% CoC)
    benchmark: str                      # "Excellent" | "Good" | "Acceptable" | "Weak" | "Poor"
    explanation: str                    # One sentence plain-English


class InvestmentScore(BaseModel):
    total: float                        # 0–100
    letter_grade: str                   # A / B / C / D / F
    components: list[ScoreComponent]
    interpretation: str                 # One-paragraph plain-English summary
    strengths: list[str]
    weaknesses: list[str]


# ---------------------------------------------------------------------------
# Red Flag Detector
# ---------------------------------------------------------------------------

class RedFlag(BaseModel):
    code: str                           # Machine-readable (e.g., "DSCR_BELOW_1")
    title: str
    description: str
    severity: str                       # CRITICAL | HIGH | MEDIUM | LOW
    affected_metric: str
    current_value: str                  # Formatted for display
    threshold: str                      # "Should be > 1.25x"
    recommendation: str


# ---------------------------------------------------------------------------
# Investment Memo
# ---------------------------------------------------------------------------

class MemoSection(BaseModel):
    title: str
    bullets: list[str]
    narrative: str                      # Prose paragraph


class InvestmentMemo(BaseModel):
    property_name: str
    generated_at: str
    executive_summary: str
    deal_type: str                      # "Cash Flow Play" | "Appreciation Play" | "Distressed" | etc.
    deal_overview: MemoSection
    strengths: MemoSection
    weaknesses: MemoSection
    key_risks: MemoSection
    what_makes_it_work: MemoSection
    suggested_offer_price: Optional[float]   # Reverse-DCF negotiation price
    suggested_offer_rationale: str
    negotiation_points: list[str]
    questions_before_buying: list[str]
    disclaimer: str = (
        "This analysis is for educational and informational purposes only. "
        "It is not legal advice, a licensed appraisal, or a guarantee of future performance. "
        "Rent-stabilization rules are simplified; consult an attorney before transacting."
    )
