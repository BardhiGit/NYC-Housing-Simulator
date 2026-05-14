"""
Investment Quality Score: deterministic, explainable 0–100 scoring formula.

Score components and weights:
  Cash-on-Cash Return   20 pts — primary cash yield metric
  DSCR                  20 pts — debt safety margin
  Cap Rate              15 pts — unlevered yield
  Break-even Occupancy  15 pts — operational cushion
  Expense Ratio         10 pts — operational efficiency
  LTV                    5 pts — balance sheet risk
  RS% Penalty           -10 pts max — income growth constraint
  Vacancy Cushion        5 pts — sensitivity to vacancy
  Expense Ratio Penalty  10 pts — operational ceiling
  ─────────────────────────────
  Max raw:              100 pts

Letter grades:
  A: 75–100   Strong deal — uncommon in NYC
  B: 55–74    Acceptable — marginal cash flow, appreciation-dependent
  C: 35–54    Weak — negative cash flow likely, high risk
  D: 15–34    Poor — significant financial stress
  F: 0–14     Critical — avoid

NYC context: scores tend to run 20–55 due to high prices relative to rents.
A score > 65 in NYC typically requires low leverage or below-market acquisition.
"""

from __future__ import annotations

from typing import Optional

from app.models.inputs import PropertyInput
from app.models.outputs import FullFinancialResult, InvestmentScore, ScoreComponent
from app.services.projection import ProjectionResult


# ---------------------------------------------------------------------------
# Component scoring functions
# ---------------------------------------------------------------------------

def _score_coc(coc: float) -> tuple[float, str, str]:
    """Max 20 pts. NYC thresholds skewed lower than national averages."""
    if coc >= 0.08:    return 20.0, "Excellent", f"{coc:.1%} CoC — exceptional for NYC"
    if coc >= 0.06:    return 15.0, "Good",      f"{coc:.1%} CoC — solid positive cash flow"
    if coc >= 0.04:    return 10.0, "Acceptable", f"{coc:.1%} CoC — modest return"
    if coc >= 0.02:    return 5.0,  "Weak",      f"{coc:.1%} CoC — minimal return on equity"
    if coc >= 0.0:     return 2.0,  "Poor",      f"{coc:.1%} CoC — barely positive"
    return 0.0,  "Critical",  f"{coc:.1%} CoC — negative cash flow"


def _score_dscr(dscr_val: float) -> tuple[float, str, str]:
    """Max 20 pts. Lender minimum is 1.25x; below 1.0 is technically insolvent."""
    if dscr_val >= 1.50:   return 20.0, "Excellent",  f"{dscr_val:.2f}x DSCR — very safe"
    if dscr_val >= 1.35:   return 16.0, "Good",       f"{dscr_val:.2f}x DSCR — lender-comfortable"
    if dscr_val >= 1.25:   return 12.0, "Acceptable", f"{dscr_val:.2f}x DSCR — meets lender minimum"
    if dscr_val >= 1.10:   return 7.0,  "Weak",       f"{dscr_val:.2f}x DSCR — thin coverage"
    if dscr_val >= 1.00:   return 3.0,  "Poor",       f"{dscr_val:.2f}x DSCR — barely covering debt"
    return max(0.0, 20.0 * dscr_val - 20.0), "Critical", f"{dscr_val:.2f}x DSCR — debt not covered by income"


def _score_cap_rate(cap: float) -> tuple[float, str, str]:
    """Max 15 pts. NYC cap rates compress toward 3-5%; 6%+ is rare and strong."""
    if cap >= 0.065:   return 15.0, "Excellent",  f"{cap:.2%} cap rate — high for NYC"
    if cap >= 0.055:   return 12.0, "Good",       f"{cap:.2%} cap rate — above market"
    if cap >= 0.045:   return 8.0,  "Acceptable", f"{cap:.2%} cap rate — market rate"
    if cap >= 0.035:   return 4.0,  "Weak",       f"{cap:.2%} cap rate — below market"
    return 1.0, "Poor", f"{cap:.2%} cap rate — very compressed"


def _score_break_even(be_occ: float) -> tuple[float, str, str]:
    """Max 15 pts. Lower break-even % = more cushion against vacancies."""
    if be_occ <= 0.65:   return 15.0, "Excellent",  f"{be_occ:.0%} break-even occ. — wide cushion"
    if be_occ <= 0.75:   return 12.0, "Good",       f"{be_occ:.0%} break-even occ. — adequate cushion"
    if be_occ <= 0.85:   return 7.0,  "Acceptable", f"{be_occ:.0%} break-even occ. — tight"
    if be_occ <= 0.90:   return 3.0,  "Weak",       f"{be_occ:.0%} break-even occ. — very tight"
    if be_occ <= 1.00:   return 1.0,  "Poor",       f"{be_occ:.0%} break-even occ. — nearly no cushion"
    return 0.0, "Critical", f"{be_occ:.0%} break-even exceeds 100% — impossible to break even"


def _score_expense_ratio(ratio: float) -> tuple[float, str, str]:
    """Max 10 pts. NYC multifamily typical: 35-55%."""
    if ratio <= 0.40:   return 10.0, "Excellent",  f"{ratio:.0%} expense ratio — well-managed"
    if ratio <= 0.50:   return 8.0,  "Good",       f"{ratio:.0%} expense ratio — efficient"
    if ratio <= 0.60:   return 5.0,  "Acceptable", f"{ratio:.0%} expense ratio — average"
    if ratio <= 0.70:   return 2.0,  "Weak",       f"{ratio:.0%} expense ratio — high"
    return 0.0, "Poor", f"{ratio:.0%} expense ratio — expenses consuming most income"


def _score_ltv(ltv: float) -> tuple[float, str, str]:
    """Max 5 pts. Lower leverage = less risk, more financial flexibility."""
    if ltv <= 0.60:   return 5.0, "Excellent", f"{ltv:.0%} LTV — conservative leverage"
    if ltv <= 0.70:   return 4.0, "Good",      f"{ltv:.0%} LTV — moderate leverage"
    if ltv <= 0.75:   return 3.0, "Acceptable",f"{ltv:.0%} LTV — standard"
    if ltv <= 0.80:   return 2.0, "Weak",      f"{ltv:.0%} LTV — high leverage"
    return 1.0, "Poor", f"{ltv:.0%} LTV — very high leverage"


def _score_rs_penalty(rs_pct: float) -> tuple[float, str, str]:
    """
    Max -10 pts (penalty only). High RS% constrains rent growth and exit value.
    NYC reality: many buildings are 60-100% RS; this is a risk, not disqualifying.
    """
    if rs_pct <= 0.25:   return 0.0,   "Low Risk",   f"{rs_pct:.0%} RS units — minimal stabilization constraint"
    if rs_pct <= 0.50:   return -3.0,  "Moderate",   f"{rs_pct:.0%} RS units — some income growth constraint"
    if rs_pct <= 0.75:   return -6.0,  "High",       f"{rs_pct:.0%} RS units — significant growth constraint"
    return -10.0, "Very High",  f"{rs_pct:.0%} RS units — income growth severely constrained"


def _score_irr(irr: float) -> tuple[float, str, str]:
    """Max 5 pts. Holistic return metric including appreciation."""
    if irr >= 0.15:   return 5.0, "Excellent",  f"{irr:.1%} IRR — strong total return"
    if irr >= 0.10:   return 4.0, "Good",       f"{irr:.1%} IRR — above hurdle"
    if irr >= 0.07:   return 2.0, "Acceptable", f"{irr:.1%} IRR — below typical hurdle"
    if irr >= 0.04:   return 1.0, "Weak",       f"{irr:.1%} IRR — weak total return"
    return 0.0, "Poor", f"{irr:.1%} IRR — inadequate return"


# ---------------------------------------------------------------------------
# Main scoring class
# ---------------------------------------------------------------------------

class ScoringService:

    @classmethod
    def score(
        cls,
        prop: PropertyInput,
        financials: FullFinancialResult,
        projection: Optional[ProjectionResult] = None,
    ) -> InvestmentScore:
        """
        Compute Investment Quality Score from pre-calculated financial results.

        If a projection result is provided, the IRR component is included.
        Otherwise the score is capped at 95 (no IRR component).
        """
        components: list[ScoreComponent] = []

        # ── Cash-on-Cash ─────────────────────────────────────────────────────
        coc = financials.returns.cash_on_cash_return
        pts, bench, expl = _score_coc(coc)
        components.append(ScoreComponent(
            name="coc_return",
            display_name="Cash-on-Cash Return",
            score=pts,
            max_score=20.0,
            raw_value=coc,
            benchmark=bench,
            explanation=expl,
        ))

        # ── DSCR ─────────────────────────────────────────────────────────────
        dscr_val = financials.debt.dscr if financials.debt else 0.0
        pts, bench, expl = _score_dscr(dscr_val) if financials.debt else (0.0, "N/A", "No debt")
        components.append(ScoreComponent(
            name="dscr",
            display_name="Debt Service Coverage",
            score=pts,
            max_score=20.0,
            raw_value=dscr_val,
            benchmark=bench,
            explanation=expl,
        ))

        # ── Cap Rate ──────────────────────────────────────────────────────────
        cap = financials.returns.cap_rate
        pts, bench, expl = _score_cap_rate(cap)
        components.append(ScoreComponent(
            name="cap_rate",
            display_name="Cap Rate",
            score=pts,
            max_score=15.0,
            raw_value=cap,
            benchmark=bench,
            explanation=expl,
        ))

        # ── Break-even Occupancy ──────────────────────────────────────────────
        be = financials.break_even.break_even_occupancy
        pts, bench, expl = _score_break_even(be)
        components.append(ScoreComponent(
            name="break_even",
            display_name="Break-Even Occupancy",
            score=pts,
            max_score=15.0,
            raw_value=be,
            benchmark=bench,
            explanation=expl,
        ))

        # ── Expense Ratio ─────────────────────────────────────────────────────
        er = financials.operating.expense_ratio
        pts, bench, expl = _score_expense_ratio(er)
        components.append(ScoreComponent(
            name="expense_ratio",
            display_name="Expense Ratio",
            score=pts,
            max_score=10.0,
            raw_value=er,
            benchmark=bench,
            explanation=expl,
        ))

        # ── LTV ───────────────────────────────────────────────────────────────
        ltv = financials.debt.loan_to_value if financials.debt else 0.0
        pts, bench, expl = _score_ltv(ltv) if financials.debt else (5.0, "N/A", "All-cash purchase")
        components.append(ScoreComponent(
            name="ltv",
            display_name="Loan-to-Value",
            score=pts,
            max_score=5.0,
            raw_value=ltv,
            benchmark=bench,
            explanation=expl,
        ))

        # ── RS Penalty ────────────────────────────────────────────────────────
        rs_pct = financials.rent_roll.rs_percentage
        pts, bench, expl = _score_rs_penalty(rs_pct)
        components.append(ScoreComponent(
            name="rs_penalty",
            display_name="Rent-Stabilization Risk",
            score=pts,
            max_score=0.0,    # penalty component, max is 0
            raw_value=rs_pct,
            benchmark=bench,
            explanation=expl,
        ))

        # ── IRR (if projection available) ─────────────────────────────────────
        if projection:
            pts, bench, expl = _score_irr(projection.irr)
            components.append(ScoreComponent(
                name="irr",
                display_name="Total Return (IRR)",
                score=pts,
                max_score=5.0,
                raw_value=projection.irr,
                benchmark=bench,
                explanation=expl,
            ))

        # ── Total ─────────────────────────────────────────────────────────────
        total = max(0.0, min(100.0, sum(c.score for c in components)))

        letter = _letter_grade(total)
        strengths = [c.explanation for c in components if c.score >= c.max_score * 0.75 and c.max_score > 0]
        weaknesses = [c.explanation for c in components if c.score < c.max_score * 0.40 and c.max_score > 0]

        return InvestmentScore(
            total=round(total, 1),
            letter_grade=letter,
            components=components,
            interpretation=_build_interpretation(total, financials, prop),
            strengths=strengths,
            weaknesses=weaknesses,
        )


def _letter_grade(score: float) -> str:
    if score >= 75: return "A"
    if score >= 55: return "B"
    if score >= 35: return "C"
    if score >= 15: return "D"
    return "F"


def _build_interpretation(total: float, fin: FullFinancialResult, prop: PropertyInput) -> str:
    cf = fin.returns.cash_flow_before_tax
    dscr_val = fin.debt.dscr if fin.debt else None
    rs_pct = fin.rent_roll.rs_percentage

    if total >= 75:
        return (
            f"Strong deal by NYC standards. Cash flow is positive, debt coverage is "
            f"comfortable, and the expense structure is well-managed."
        )
    if total >= 55:
        cf_txt = f"positive (${cf:,.0f}/yr)" if cf >= 0 else f"negative (${cf:,.0f}/yr)"
        return (
            f"Acceptable deal with some risk. Year-1 cash flow is {cf_txt}. "
            f"Returns depend partly on appreciation. Ensure you have reserves for "
            f"unexpected expenses."
        )
    if total >= 35:
        return (
            f"Weak deal at current parameters. "
            f"{'Cash flow is negative — you will need to fund the shortfall monthly. ' if cf < 0 else ''}"
            f"This may work as a long-term appreciation play if you can hold through lean years."
        )
    return (
        f"Poor investment at this price and financing. "
        f"{'DSCR of ' + f'{dscr_val:.2f}x indicates income cannot cover debt. ' if dscr_val and dscr_val < 1.0 else ''}"
        f"Significant price reduction or restructuring needed before this deal makes sense."
    )
