"""
Red Flag Detector — rules engine for dangerous financial assumptions.

Each rule checks a specific condition and produces a structured warning.
Rules run against the pre-calculated FullFinancialResult plus raw inputs.

Severity levels:
  CRITICAL  — deal-breaking issue (DSCR < 1.0, etc.)
  HIGH      — significant risk requiring immediate attention
  MEDIUM    — notable concern worth investigating
  LOW       — informational, minor optimization opportunity

NYC-specific rules are labeled with (NYC).
"""

from __future__ import annotations

from app.models.inputs import PropertyInput, RentType
from app.models.outputs import FullFinancialResult, RedFlag


def detect_red_flags(
    prop: PropertyInput,
    fin: FullFinancialResult,
) -> list[RedFlag]:
    """
    Run all rules and return a list of triggered red flags, sorted by severity.
    """
    flags: list[RedFlag] = []
    _run_rules(prop, fin, flags)
    # Sort: CRITICAL → HIGH → MEDIUM → LOW
    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    flags.sort(key=lambda f: order.get(f.severity, 99))
    return flags


# ---------------------------------------------------------------------------
# Rule implementations
# ---------------------------------------------------------------------------

def _run_rules(prop: PropertyInput, fin: FullFinancialResult, flags: list[RedFlag]) -> None:

    # ── DSCR below 1.0 ───────────────────────────────────────────────────────
    if fin.debt and fin.debt.dscr < 1.0:
        flags.append(RedFlag(
            code="DSCR_BELOW_1",
            title="Income Cannot Cover Debt Service",
            description=(
                f"DSCR of {fin.debt.dscr:.2f}x means the property's net income covers only "
                f"{fin.debt.dscr * 100:.0f}% of the annual mortgage payment. You will need "
                f"to subsidize ${abs(fin.returns.cash_flow_before_tax):,.0f}/year from personal funds."
            ),
            severity="CRITICAL",
            affected_metric="DSCR",
            current_value=f"{fin.debt.dscr:.2f}x",
            threshold="Minimum 1.0x to break even; lenders require 1.25x",
            recommendation=(
                "Negotiate a lower purchase price, increase the down payment to reduce debt, "
                "or identify rent upside that will materially improve NOI within 12 months."
            ),
        ))

    # ── Negative cash flow ────────────────────────────────────────────────────
    elif fin.returns.cash_flow_before_tax < 0 and fin.debt:
        shortfall = abs(fin.returns.cash_flow_before_tax)
        flags.append(RedFlag(
            code="NEGATIVE_CASH_FLOW",
            title="Negative Annual Cash Flow",
            description=(
                f"Year-1 cash flow is -${shortfall:,.0f}. This is common for NYC "
                f"appreciation plays, but requires capital reserves and tolerance for monthly shortfalls."
            ),
            severity="HIGH",
            affected_metric="Cash Flow",
            current_value=f"-${shortfall:,.0f}/yr",
            threshold="> $0/yr to be cash-flow positive",
            recommendation=(
                "Confirm you have sufficient reserves (minimum 6 months of shortfall + expenses). "
                "Model break-even year assuming projected rent growth."
            ),
        ))

    # ── DSCR below lender threshold ───────────────────────────────────────────
    if fin.debt and 1.0 <= fin.debt.dscr < 1.25:
        flags.append(RedFlag(
            code="DSCR_BELOW_LENDER_MIN",
            title="DSCR Below Typical Lender Minimum",
            description=(
                f"DSCR of {fin.debt.dscr:.2f}x is below the 1.25x minimum most "
                f"community banks and agencies require for multifamily loans. "
                f"Refinancing will be difficult at these numbers."
            ),
            severity="HIGH",
            affected_metric="DSCR",
            current_value=f"{fin.debt.dscr:.2f}x",
            threshold="1.25x (lender minimum), 1.35x (preferred)",
            recommendation=(
                "Reduce leverage (larger down payment) or increase NOI before refinancing. "
                "Consider an IO period to reduce near-term debt service."
            ),
        ))

    # ── Break-even occupancy above 90% ───────────────────────────────────────
    if fin.break_even.break_even_occupancy > 0.90:
        be = fin.break_even.break_even_occupancy
        flags.append(RedFlag(
            code="HIGH_BREAKEVEN",
            title="Very High Break-Even Occupancy",
            description=(
                f"The property needs {be:.0%} occupancy just to cover expenses and debt. "
                f"Any significant vacancy could create a cash crisis."
            ),
            severity="HIGH",
            affected_metric="Break-Even Occupancy",
            current_value=f"{be:.0%}",
            threshold="< 85% recommended; > 90% is high risk",
            recommendation=(
                "Reduce expenses where possible. Prioritize filling vacant units quickly. "
                "Maintain a 6-month operating reserve."
            ),
        ))

    # ── Expense ratio above 65% ────────────────────────────────────────────────
    if fin.operating.expense_ratio > 0.65:
        flags.append(RedFlag(
            code="HIGH_EXPENSE_RATIO",
            title="Expense Ratio Exceeds 65%",
            description=(
                f"Operating expenses are {fin.operating.expense_ratio:.0%} of effective gross income. "
                f"NYC multifamily typically runs 35–55%. This leaves little margin for debt service."
            ),
            severity="HIGH",
            affected_metric="Expense Ratio",
            current_value=f"{fin.operating.expense_ratio:.0%}",
            threshold="< 55% typical NYC; < 65% acceptable",
            recommendation=(
                "Audit each expense category against borough benchmarks. "
                "High property tax relative to income is common in NYC Class 2 buildings — "
                "verify the tax assessment and file for review if appropriate."
            ),
        ))

    # ── LTV above 80% ────────────────────────────────────────────────────────
    if fin.debt and fin.debt.loan_to_value > 0.80:
        flags.append(RedFlag(
            code="HIGH_LTV",
            title="Loan-to-Value Exceeds 80%",
            description=(
                f"LTV of {fin.debt.loan_to_value:.0%} is above the 75–80% threshold "
                f"most conventional lenders accept for multifamily. PMI or higher rates may apply."
            ),
            severity="MEDIUM",
            affected_metric="LTV",
            current_value=f"{fin.debt.loan_to_value:.0%}",
            threshold="≤ 75% preferred; ≤ 80% maximum for most lenders",
            recommendation="Increase down payment to reduce LTV below 80%.",
        ))

    # ── High rent-stabilized percentage (NYC) ────────────────────────────────
    rs_pct = fin.rent_roll.rs_percentage
    if rs_pct > 0.75:
        flags.append(RedFlag(
            code="HIGH_RS_PERCENTAGE",
            title="75%+ Units Are Rent-Stabilized (NYC)",
            description=(
                f"{rs_pct:.0%} of rentable units are rent-stabilized. Post-HSTPA 2019, "
                f"there is no deregulation path. Rent growth is permanently capped at "
                f"RGB orders (~2–4%/yr). Exit value is constrained by capped NOI growth."
            ),
            severity="MEDIUM",
            affected_metric="RS%",
            current_value=f"{rs_pct:.0%}",
            threshold="< 50% for meaningful free-market upside",
            recommendation=(
                "Price this as a long-term income stream, not a value-add play. "
                "Do not underwrite deregulation scenarios — they are legally impossible post-2019."
            ),
        ))

    # ── Preferential rent gap (NYC) ────────────────────────────────────────
    pref_gap_units = [
        u for u in prop.units
        if u.rent_type == RentType.STABILIZED
        and u.legal_rent and u.preferential_rent
        and u.preferential_rent < u.legal_rent * 0.85
    ]
    if pref_gap_units:
        flags.append(RedFlag(
            code="PREF_RENT_GAP",
            title="Significant Preferential Rent Gaps (NYC)",
            description=(
                f"{len(pref_gap_units)} unit(s) pay preferential rents more than 15% below "
                f"their legal regulated rent. Post-HSTPA 2019, the landlord MUST continue "
                f"the preferential rent through the tenancy — this upside cannot be captured "
                f"until the tenant vacates."
            ),
            severity="MEDIUM",
            affected_metric="RS Preferential Rent",
            current_value=f"{len(pref_gap_units)} affected units",
            threshold="Pref rent should be close to legal rent for income stability",
            recommendation=(
                "Account for the gap in your income projection. The legal rent "
                "becomes collectible only at natural tenancy turnover, which can take many years."
            ),
        ))

    # ── No capex reserve ─────────────────────────────────────────────────────
    has_capex = any(
        e.category.value == "capex_reserve" for e in prop.expenses
    )
    if not has_capex and prop.assumptions.capex_reserve_per_unit_annual == 0:
        flags.append(RedFlag(
            code="NO_CAPEX_RESERVE",
            title="No Capital Expenditure Reserve",
            description=(
                "No CapEx reserve is budgeted. NYC buildings typically require "
                "$500–$1,500/unit/year for roof, mechanicals, windows, and common areas. "
                "Without reserves, major repairs will directly hit cash flow."
            ),
            severity="MEDIUM",
            affected_metric="CapEx Reserve",
            current_value="$0",
            threshold=f"$500–$1,500/unit/year recommended",
            recommendation=(
                f"Add a CapEx reserve of at least "
                f"${500 * prop.num_units:,.0f}/year ({prop.num_units} units × $500)."
            ),
        ))

    # ── Low repairs per unit ──────────────────────────────────────────────────
    repair_expense = fin.operating.expense_by_category.get("repairs", 0.0)
    repairs_per_unit = repair_expense / prop.num_units if prop.num_units > 0 else 0
    if 0 < repairs_per_unit < 300:
        flags.append(RedFlag(
            code="LOW_REPAIRS_BUDGET",
            title="Unusually Low Repairs Budget",
            description=(
                f"Repairs budget of ${repairs_per_unit:,.0f}/unit/year is below the NYC "
                f"minimum of ~$600–$1,000/unit/year for a stabilized building. "
                f"This may understate true operating costs."
            ),
            severity="LOW",
            affected_metric="Repairs",
            current_value=f"${repairs_per_unit:,.0f}/unit/yr",
            threshold="$600–$1,000/unit/yr typical for NYC multifamily",
            recommendation=(
                "Review maintenance history. If the broker pro forma uses a low repairs number, "
                "recast with $700–$800/unit to stress-test NOI."
            ),
        ))

    # ── Vacant units > 20% ────────────────────────────────────────────────────
    vacant_pct = fin.rent_roll.num_vacant / prop.num_units if prop.num_units > 0 else 0
    if vacant_pct > 0.20:
        flags.append(RedFlag(
            code="HIGH_VACANCY",
            title=f"{vacant_pct:.0%} of Units Currently Vacant",
            description=(
                f"{fin.rent_roll.num_vacant} of {prop.num_units} units are currently vacant. "
                f"Verify reason: renovation, eviction, or market conditions. "
                f"High vacancy means income projections depend on successful lease-up."
            ),
            severity="MEDIUM",
            affected_metric="Physical Vacancy",
            current_value=f"{vacant_pct:.0%} vacant",
            threshold="< 10% vacancy typical for NYC stabilized buildings",
            recommendation=(
                "Obtain lease-up timeline and budget. Ensure NOI projections "
                "reflect the income ramp, not stabilized occupancy from day one."
            ),
        ))

    # ── CoC below 2% ──────────────────────────────────────────────────────────
    if fin.returns.cash_on_cash_return < 0.02 and fin.returns.cash_on_cash_return >= 0:
        flags.append(RedFlag(
            code="LOW_COC",
            title="Cash-on-Cash Return Below 2%",
            description=(
                f"CoC of {fin.returns.cash_on_cash_return:.1%} is below savings account rates. "
                f"Your equity is doing less work than a money market fund."
            ),
            severity="LOW",
            affected_metric="Cash-on-Cash Return",
            current_value=f"{fin.returns.cash_on_cash_return:.1%}",
            threshold="> 5% for meaningful equity return; > 8% for excellent",
            recommendation=(
                "Model IRR over holding period to see if appreciation makes this viable. "
                "At sub-2% CoC, you are essentially betting on price appreciation."
            ),
        ))
