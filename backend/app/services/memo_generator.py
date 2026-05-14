"""
Rule-based investment memo generator.

Generates a structured, plain-English investment memo without requiring
an LLM. The memo is fully deterministic: same inputs → same memo.

The memo reads like a professional deal summary an analyst would write
for a senior associate. It surfaces the most important facts, flags risks,
and makes concrete recommendations.

Design: each section is built from a decision tree of rules applied to
the financial metrics. The resulting text is assembled into a MemoSection.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from app.models.inputs import PropertyInput
from app.models.outputs import (
    FullFinancialResult,
    InvestmentMemo,
    InvestmentScore,
    MemoSection,
    ProjectionResult,
    RedFlag,
)


def generate_memo(
    prop: PropertyInput,
    fin: FullFinancialResult,
    score: InvestmentScore,
    red_flags: list[RedFlag],
    projection: Optional[ProjectionResult] = None,
) -> InvestmentMemo:
    """Build a complete investment memo from pre-calculated results."""

    deal_type = _classify_deal(fin, projection)
    exec_summary = _executive_summary(prop, fin, score, deal_type)

    return InvestmentMemo(
        property_name=prop.name or prop.address or "Subject Property",
        generated_at=date.today().isoformat(),
        executive_summary=exec_summary,
        deal_type=deal_type,
        deal_overview=_deal_overview(prop, fin, projection),
        strengths=_strengths_section(fin, projection, score),
        weaknesses=_weaknesses_section(fin, red_flags),
        key_risks=_key_risks_section(prop, fin, red_flags),
        what_makes_it_work=_what_makes_it_work(prop, fin, projection),
        suggested_offer_price=_suggested_offer_price(fin, prop),
        suggested_offer_rationale=_offer_rationale(prop, fin),
        negotiation_points=_negotiation_points(prop, fin, red_flags),
        questions_before_buying=_due_diligence_questions(prop, fin, red_flags),
    )


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _classify_deal(fin: FullFinancialResult, projection: Optional[ProjectionResult]) -> str:
    cf = fin.returns.cash_flow_before_tax
    cap = fin.returns.cap_rate
    rs_pct = fin.rent_roll.rs_percentage

    if cf > 0 and cap > 0.06:
        return "Cash Flow Play"
    if cf > 0 and cap >= 0.045:
        return "Balanced Return"
    if cf < 0 and projection and projection.irr > 0.08:
        return "Appreciation Play"
    if cf < 0 and rs_pct > 0.70:
        return "Income-Constrained (High RS)"
    if fin.debt and fin.debt.dscr < 1.0:
        return "Distressed / Restructuring Needed"
    if cf >= 0:
        return "Marginal Cash Flow"
    return "Speculative"


def _executive_summary(
    prop: PropertyInput,
    fin: FullFinancialResult,
    score: InvestmentScore,
    deal_type: str,
) -> str:
    name = prop.name or prop.address or "This property"
    cf = fin.returns.cash_flow_before_tax
    cap = fin.returns.cap_rate
    coc = fin.returns.cash_on_cash_return
    grade = score.letter_grade

    cf_txt = f"${cf:,.0f}/yr positive cash flow" if cf >= 0 else f"${abs(cf):,.0f}/yr negative cash flow"

    dscr_txt = ""
    if fin.debt:
        dscr_val = fin.debt.dscr
        if dscr_val < 1.0:
            dscr_txt = f" DSCR of {dscr_val:.2f}x — income does not cover debt."
        elif dscr_val < 1.25:
            dscr_txt = f" DSCR of {dscr_val:.2f}x — below lender minimums."
        else:
            dscr_txt = f" DSCR of {dscr_val:.2f}x — adequate debt coverage."

    return (
        f"{name} is classified as a {deal_type}. "
        f"Year-1 financials show a {cap:.2%} cap rate, {coc:.1%} cash-on-cash return, and {cf_txt}.{dscr_txt} "
        f"Investment Quality Score: {score.total:.0f}/100 (Grade {grade})."
    )


def _deal_overview(
    prop: PropertyInput,
    fin: FullFinancialResult,
    projection: Optional[ProjectionResult],
) -> MemoSection:
    rr = fin.rent_roll
    bullets = [
        f"Purchase price: ${prop.purchase_price:,.0f} "
        f"(${fin.valuation.price_per_unit:,.0f}/unit"
        + (f", ${fin.valuation.price_per_sq_ft:,.0f}/SF" if fin.valuation.price_per_sq_ft else "") + ")",
        f"Unit mix: {rr.num_stabilized} rent-stabilized, {rr.num_free_market} free-market, "
        f"{rr.num_vacant} vacant",
        f"Monthly gross scheduled income: ${rr.monthly_gsi:,.0f} "
        f"(${rr.annual_gsi:,.0f} annualized)",
        f"Year-1 NOI: ${fin.operating.net_operating_income:,.0f}",
        f"Year-1 cap rate: {fin.returns.cap_rate:.2%}",
    ]
    if fin.debt:
        bullets.append(
            f"Debt: ${prop.loan.loan_amount:,.0f} at {prop.loan.interest_rate:.2%} "  # type: ignore
            f"for {prop.loan.term_years} years, "  # type: ignore
            f"${fin.debt.monthly_payment:,.0f}/mo"
        )
    if projection:
        bullets.append(
            f"10-year IRR: {projection.irr:.1%} | "
            f"Equity multiple: {projection.equity_multiple:.2f}x"
        )

    narrative = (
        f"The property comprises {prop.num_units} units in {prop.borough.value.title()}, "
        f"with {rr.rs_percentage:.0%} of rentable units rent-stabilized. "
        f"Total cash required at closing: ${prop.total_cash_invested:,.0f} "
        f"(down payment + closing costs + renovation)."
    )
    return MemoSection(title="Deal Overview", bullets=bullets, narrative=narrative)


def _strengths_section(
    fin: FullFinancialResult,
    projection: Optional[ProjectionResult],
    score: InvestmentScore,
) -> MemoSection:
    bullets = []

    if fin.returns.cash_flow_before_tax > 0:
        bullets.append(
            f"Positive day-one cash flow of ${fin.returns.cash_flow_before_tax:,.0f}/yr "
            f"provides income from the start."
        )
    if fin.debt and fin.debt.dscr >= 1.35:
        bullets.append(
            f"Strong DSCR of {fin.debt.dscr:.2f}x — well above the 1.25x lender minimum."
        )
    if fin.returns.cap_rate >= 0.055:
        bullets.append(
            f"Cap rate of {fin.returns.cap_rate:.2%} is above typical NYC multifamily range, "
            f"implying reasonable unlevered yield."
        )
    if fin.operating.expense_ratio < 0.50:
        bullets.append(
            f"Lean expense ratio of {fin.operating.expense_ratio:.0%} — "
            f"well-managed operating structure."
        )
    if fin.break_even.break_even_occupancy < 0.80:
        bullets.append(
            f"Break-even occupancy of {fin.break_even.break_even_occupancy:.0%} "
            f"provides significant buffer against vacancy."
        )
    if projection and projection.irr > 0.10:
        bullets.append(
            f"10-year IRR of {projection.irr:.1%} exceeds a 10% investor hurdle."
        )
    if projection and projection.equity_multiple > 1.8:
        bullets.append(
            f"Equity multiple of {projection.equity_multiple:.2f}x over the holding period."
        )

    if not bullets:
        bullets.append("No material financial strengths identified at this price and terms.")

    narrative = (
        "The property's strengths are centered on "
        + (
            "cash flow generation and debt coverage."
            if fin.returns.cash_flow_before_tax > 0 and fin.debt and fin.debt.dscr >= 1.25
            else "long-term appreciation potential rather than near-term income."
        )
    )
    return MemoSection(title="Strengths", bullets=bullets, narrative=narrative)


def _weaknesses_section(
    fin: FullFinancialResult,
    red_flags: list[RedFlag],
) -> MemoSection:
    bullets = []

    if fin.returns.cash_flow_before_tax < 0:
        bullets.append(
            f"Negative cash flow: -${abs(fin.returns.cash_flow_before_tax):,.0f}/yr "
            f"requires ongoing capital injection from owner."
        )
    if fin.debt and fin.debt.dscr < 1.25:
        bullets.append(
            f"DSCR of {fin.debt.dscr:.2f}x is below the 1.25x lender minimum — "
            f"refinancing will be difficult."
        )
    if fin.returns.cap_rate < 0.04:
        bullets.append(
            f"Cap rate of {fin.returns.cap_rate:.2%} offers little margin — "
            f"any NOI deterioration significantly impacts value."
        )
    if fin.operating.expense_ratio > 0.60:
        bullets.append(
            f"High expense ratio ({fin.operating.expense_ratio:.0%}) compresses NOI — "
            f"limited room for unexpected costs."
        )
    if fin.rent_roll.rs_percentage > 0.60:
        bullets.append(
            f"{fin.rent_roll.rs_percentage:.0%} RS units permanently constrain "
            f"rent growth to RGB orders (~2–4%/yr)."
        )

    critical = [f for f in red_flags if f.severity == "CRITICAL"]
    for flag in critical:
        if flag.title not in " ".join(bullets):
            bullets.append(f"{flag.title}: {flag.description[:120]}...")

    if not bullets:
        bullets.append("No significant financial weaknesses identified.")

    narrative = (
        "The primary weaknesses are "
        + (
            "the negative cash flow position, which creates ongoing capital requirements."
            if fin.returns.cash_flow_before_tax < 0
            else "the constrained rent growth from stabilized units and thin margins."
        )
    )
    return MemoSection(title="Weaknesses", bullets=bullets, narrative=narrative)


def _key_risks_section(
    prop: PropertyInput,
    fin: FullFinancialResult,
    red_flags: list[RedFlag],
) -> MemoSection:
    bullets = [
        "Interest rate risk: if refinancing at maturity, rising rates compress cash flow further.",
        "Expense inflation risk: NYC property taxes, water/sewer, and insurance have outpaced CPI historically.",
        f"Vacancy risk: break-even requires {fin.break_even.break_even_occupancy:.0%} occupancy — "
        f"NYC has low vacancy but lease expirations can cluster.",
    ]

    if fin.rent_roll.rs_percentage > 0.50:
        bullets.append(
            "Regulatory risk: further changes to NYC rent laws (e.g., Good Cause Eviction "
            "expansion) could further limit free-market unit flexibility."
        )
    if fin.debt and fin.debt.loan_to_value > 0.75:
        bullets.append(
            f"Refinancing risk: LTV of {fin.debt.loan_to_value:.0%} may limit refinancing "
            f"options if property values decline."
        )
    if fin.rent_roll.num_vacant > 0:
        bullets.append(
            f"Lease-up risk: {fin.rent_roll.num_vacant} vacant unit(s) — "
            f"projections assume successful re-tenanting."
        )

    narrative = (
        "The most significant risk in this deal is "
        + (
            "the ongoing cash shortfall, which requires the investor to have deep reserves."
            if fin.returns.cash_flow_before_tax < 0
            else "the sensitivity to expense growth and vacancy in a high-cost operating environment."
        )
    )
    return MemoSection(title="Key Risks", bullets=bullets, narrative=narrative)


def _what_makes_it_work(
    prop: PropertyInput,
    fin: FullFinancialResult,
    projection: Optional[ProjectionResult],
) -> MemoSection:
    """
    Reverse-engineering: what conditions must be true for this to be a good deal?
    """
    bullets = []
    cf = fin.returns.cash_flow_before_tax

    if cf < 0:
        # How much rent growth breaks even?
        annual_shortfall = abs(cf)
        annual_gsi = fin.income.gross_scheduled_income
        needed_growth = annual_shortfall / annual_gsi if annual_gsi > 0 else 0
        bullets.append(
            f"Rents need to grow ~{needed_growth:.1%}/yr in excess of expenses "
            f"just to break even on cash flow."
        )

    if fin.debt and fin.debt.dscr < 1.25:
        # What NOI improvement makes DSCR 1.25x?
        needed_noi = fin.debt.annual_debt_service * 1.25
        noi_gap = needed_noi - fin.operating.net_operating_income
        bullets.append(
            f"NOI needs to increase by ${noi_gap:,.0f} to reach 1.25x DSCR. "
            f"This requires either rent growth, expense reduction, or lease-up of vacant units."
        )

    # What price makes CoC > 6%?
    suggested = _suggested_offer_price(fin, prop)
    if suggested and suggested < prop.purchase_price * 0.99:
        discount = (prop.purchase_price - suggested) / prop.purchase_price
        bullets.append(
            f"A purchase price of ${suggested:,.0f} ({discount:.0%} below ask) "
            f"would bring CoC return to the ~6% target threshold."
        )

    if fin.rent_roll.num_vacant > 0:
        vacant_income = fin.rent_roll.num_vacant * (
            fin.rent_roll.avg_rent_free_market or fin.rent_roll.avg_rent_stabilized or 1500
        ) * 12
        bullets.append(
            f"Leasing {fin.rent_roll.num_vacant} vacant unit(s) at market rent "
            f"would add ~${vacant_income:,.0f}/yr to GSI."
        )

    if not bullets:
        bullets.append("At current parameters, the deal already meets basic investment thresholds.")

    narrative = (
        "For this deal to work as underwritten, it depends primarily on "
        + (
            "long-term property appreciation compensating for negative cash flow."
            if cf < 0
            else "maintaining current occupancy and controlling expense growth."
        )
    )
    return MemoSection(title="What Would Make This Deal Work", bullets=bullets, narrative=narrative)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _suggested_offer_price(fin: FullFinancialResult, prop: PropertyInput) -> Optional[float]:
    """
    Reverse-engineer a purchase price that achieves DSCR ≥ 1.25x
    using the income approach: target_price = NOI / market_cap_rate.

    If current deal has no debt or already meets threshold, return None.
    """
    if not fin.debt or fin.debt.dscr >= 1.25:
        return None

    # Target: NOI / price = market cap rate approximation (NOI / ask as starting point)
    # Alternatively: price at which the same NOI gives 5% CoC
    # We use: target price = NOI / (market cap rate + 0.5%)
    market_cap = prop.assumptions.exit_cap_rate
    noi = fin.operating.net_operating_income
    if market_cap <= 0 or noi <= 0:
        return None

    target_price = noi / (market_cap + 0.005)  # slight premium for DSCR buffer
    return round(target_price / 1000) * 1000  # round to nearest $1,000


def _offer_rationale(prop: PropertyInput, fin: FullFinancialResult) -> str:
    noi = fin.operating.net_operating_income
    suggested = _suggested_offer_price(fin, prop)
    if not suggested:
        return "Current pricing is at or near fair value given the NOI."
    discount = (prop.purchase_price - suggested) / prop.purchase_price
    return (
        f"Based on the property's NOI of ${noi:,.0f} and a target cap rate of "
        f"{prop.assumptions.exit_cap_rate + 0.005:.2%}, the implied fair value is "
        f"${suggested:,.0f} — approximately {discount:.0%} below the current ask of "
        f"${prop.purchase_price:,.0f}."
    )


def _negotiation_points(
    prop: PropertyInput,
    fin: FullFinancialResult,
    red_flags: list[RedFlag],
) -> list[str]:
    points = []

    if fin.returns.cash_flow_before_tax < 0:
        points.append(
            f"Price reduction of at least ${abs(fin.returns.cash_flow_before_tax) / 0.05:,.0f} "
            f"needed to achieve 5% CoC at current financing terms."
        )
    if fin.rent_roll.num_vacant > 0:
        points.append(
            f"Seller should provide rent concession or price credit for {fin.rent_roll.num_vacant} "
            f"vacant unit(s) — you're paying for income that isn't there yet."
        )
    if fin.rent_roll.rs_percentage > 0.50:
        points.append(
            "Negotiate an estoppel certificate confirming legal rent and preferential rent "
            "for each RS unit — discrepancies can void post-closing income assumptions."
        )

    high_flags = [f for f in red_flags if f.severity in ("CRITICAL", "HIGH")]
    if len(high_flags) >= 2:
        points.append(
            "Multiple high-severity risk factors. Consider a conditional offer with "
            "a financial audit period before going hard on your deposit."
        )

    points.append(
        "Request a 5-year operating history (rent rolls, tax returns, utility bills). "
        "Broker pro formas routinely understate expenses by 15–25%."
    )
    return points


def _due_diligence_questions(
    prop: PropertyInput,
    fin: FullFinancialResult,
    red_flags: list[RedFlag],
) -> list[str]:
    questions = [
        "What is the current DHCR legal rent for each stabilized unit? Get the full rent history.",
        "Are there any open 421-a, J-51, or other tax abatements expiring? When?",
        "What is the current assessed value and when was it last reassessed? Any pending challenges?",
        "Are there any HPD or DOB violations? What is the cure timeline and cost?",
        "When was the roof, boiler, and elevator (if any) last replaced?",
        "What is the actual vacancy history over the last 3 years?",
        "Are any tenants in arrears or pending eviction proceedings?",
        "Is the building in a flood zone? What is the FEMA flood insurance requirement?",
        "Is the building subject to any ground lease or air rights encumbrances?",
        "What caused each current vacancy? Renovation, eviction, or market conditions?",
    ]

    if fin.rent_roll.rs_percentage > 0.50:
        questions.append(
            "Have any Individual Apartment Improvement (IAI) increases been taken? "
            "Is the documentation in order?"
        )
    if fin.debt and fin.debt.loan_to_value > 0.75:
        questions.append(
            "Is the existing debt assumable? What are the prepayment penalties?"
        )

    return questions
