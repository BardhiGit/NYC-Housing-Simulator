"""
Amortization schedule generator.

Supports:
  - Standard fully-amortizing loans
  - Interest-only period then amortization
  - Balloon loans (term_years < amortization_years)

All math uses exact floating-point arithmetic (no rounding mid-schedule).
Rounding is applied only in the final output models.
"""

from __future__ import annotations

from app.models.inputs import LoanInput
from app.models.outputs import AmortizationRow, AmortizationSchedule, AnnualAmortizationSummary
from app.services.financial_engine import monthly_payment


class AmortizationService:
    """Wrapper class for clean API exposure."""

    @staticmethod
    def build(loan: LoanInput) -> AmortizationSchedule:
        return build_schedule(loan)

    @staticmethod
    def balance_at(loan: LoanInput, year: int) -> float:
        return balance_at_year(loan, year)


def build_schedule(loan: LoanInput) -> AmortizationSchedule:
    """
    Generate the complete monthly amortization schedule for a loan.

    IO Period Logic:
      Months 1..io_period_years×12: payment = interest only, no principal reduction
      Months after: standard amortizing payment on remaining (full) principal

    Balloon Logic:
      Amortize over amortization_years but the schedule stops at term_years×12.
      The final row's balance is the balloon payment due.
    """
    amort_years = loan.amortization_years or loan.term_years
    r = loan.interest_rate / 12  # monthly interest rate
    io_months = loan.io_period_years * 12
    term_months = loan.term_years * 12

    # Payment amounts
    io_payment = loan.loan_amount * r
    amort_payment = monthly_payment(loan.loan_amount, loan.interest_rate, amort_years)

    rows: list[AmortizationRow] = []
    balance = loan.loan_amount
    cum_interest = 0.0
    cum_principal = 0.0

    for month in range(1, term_months + 1):
        interest = balance * r

        if loan.is_interest_only:
            pmt = io_payment
            principal = 0.0
        elif month <= io_months:
            pmt = io_payment
            principal = 0.0
        else:
            pmt = amort_payment
            principal = pmt - interest

        balance -= principal
        cum_interest += interest
        cum_principal += principal

        # Prevent floating-point drift
        if balance < 0:
            balance = 0.0

        rows.append(AmortizationRow(
            month=month,
            year=(month - 1) // 12 + 1,
            payment=round(pmt, 2),
            principal=round(principal, 2),
            interest=round(interest, 2),
            balance=round(balance, 2),
            cumulative_interest=round(cum_interest, 2),
            cumulative_principal=round(cum_principal, 2),
        ))

    annual_summary = _annual_summary(rows)

    return AmortizationSchedule(
        monthly_payment=round(
            amort_payment if not loan.is_interest_only else io_payment, 2
        ),
        total_interest=round(cum_interest, 2),
        total_principal=round(cum_principal, 2),
        rows=rows,
        annual_summary=annual_summary,
    )


def balance_at_year(loan: LoanInput, year: int) -> float:
    """
    Return the remaining loan balance at the end of a given year.
    More efficient than generating the full schedule when only balance is needed.
    """
    if year <= 0:
        return loan.loan_amount
    if year > loan.term_years:
        return 0.0

    amort_years = loan.amortization_years or loan.term_years
    r = loan.interest_rate / 12
    io_months = loan.io_period_years * 12
    pmt = monthly_payment(loan.loan_amount, loan.interest_rate, amort_years)

    balance = loan.loan_amount
    for month in range(1, year * 12 + 1):
        interest = balance * r
        if loan.is_interest_only or month <= io_months:
            principal = 0.0
        else:
            principal = pmt - interest
        balance -= principal
        if balance < 0:
            balance = 0.0

    return round(balance, 2)


def _annual_summary(rows: list[AmortizationRow]) -> list[AnnualAmortizationSummary]:
    """Aggregate monthly rows into year-by-year totals."""
    summary: dict[int, dict] = {}

    for row in rows:
        yr = row.year
        if yr not in summary:
            summary[yr] = {
                "year": yr,
                "total_payment": 0.0,
                "total_interest": 0.0,
                "total_principal": 0.0,
                "year_end_balance": 0.0,
            }
        summary[yr]["total_payment"] += row.payment
        summary[yr]["total_interest"] += row.interest
        summary[yr]["total_principal"] += row.principal
        summary[yr]["year_end_balance"] = row.balance  # last month of year

    result = []
    for yr in sorted(summary.keys()):
        d = summary[yr]
        i_pct = d["total_interest"] / d["total_payment"] if d["total_payment"] > 0 else 0.0
        result.append(AnnualAmortizationSummary(
            year=d["year"],
            total_payment=round(d["total_payment"], 2),
            total_interest=round(d["total_interest"], 2),
            total_principal=round(d["total_principal"], 2),
            year_end_balance=round(d["year_end_balance"], 2),
            interest_pct_of_payment=round(i_pct, 4),
        ))

    return result
