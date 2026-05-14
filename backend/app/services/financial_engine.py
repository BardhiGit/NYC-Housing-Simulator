"""
Core financial calculation engine.

Formula reference (all standard real estate finance):
  GSI  = Σ(unit_monthly_rent × 12) at 100% occupancy
  EGI  = GSI × (1 − vacancy_rate) + other_income
  NOI  = EGI − Operating Expenses
  Cap  = NOI / Purchase Price
  CoC  = (NOI − ADS) / Total_Cash_Invested
  DSCR = NOI / Annual_Debt_Service
  BE%  = (OpEx + ADS) / GSI          ← break-even occupancy

Rent Stabilization notes (NYC-specific):
  - RS units grow at RGB orders (~2-4%/yr), never at market rates
  - Legal rent = DHCR maximum; preferential rent ≤ legal rent
  - Post-HSTPA 2019: preferential rent persists through tenancy
  - On vacancy: new tenant gets legal rent, not free-market rent
  - No deregulation path via renovation or high-rent threshold (post-2019)
"""

from __future__ import annotations

from typing import Optional

from app.models.inputs import (
    AssumptionInput,
    ExpenseCategory,
    LoanInput,
    PropertyInput,
    RentType,
    UnitInput,
)
from app.models.outputs import (
    BreakEvenMetrics,
    DebtMetrics,
    FullFinancialResult,
    IncomeMetrics,
    OperatingMetrics,
    RentRollSummary,
    ReturnMetrics,
    ValuationMetrics,
)


# ---------------------------------------------------------------------------
# Standalone formula functions (testable in isolation)
# ---------------------------------------------------------------------------

def monthly_payment(loan_amount: float, annual_rate: float, term_years: int) -> float:
    """
    Standard mortgage payment formula:
      PMT = P × [r(1+r)^n] / [(1+r)^n − 1]
    where r = monthly rate, n = number of monthly payments.
    """
    if annual_rate <= 0:
        return loan_amount / (term_years * 12)
    r = annual_rate / 12
    n = term_years * 12
    return loan_amount * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def annual_debt_service(loan: LoanInput) -> float:
    """
    Annualized debt service. Handles IO periods.
    During IO period: payment = loan_amount × annual_rate / 12
    After IO period: standard amortizing payment on full principal.
    """
    if loan.is_interest_only:
        # Pure IO — no principal reduction
        return loan.loan_amount * loan.interest_rate

    if loan.io_period_years > 0:
        # IO period then amortization — return year-1 IO payment
        return loan.loan_amount * loan.interest_rate

    amort_years = loan.amortization_years or loan.term_years
    pmt = monthly_payment(loan.loan_amount, loan.interest_rate, amort_years)
    return pmt * 12


def gross_scheduled_income(units: list[UnitInput]) -> float:
    """
    GSI: Annual income if all non-vacant, non-owner-occupied units pay full rent,
    100% of the time. Vacant and owner-occupied units contribute $0.
    """
    return sum(
        u.current_rent * 12
        for u in units
        if u.rent_type not in (RentType.VACANT, RentType.OWNER_OCCUPIED)
    )


def effective_gross_income(
    gsi: float,
    units: list[UnitInput],
    default_vacancy_rate: float,
    other_income: float = 0.0,
) -> tuple[float, float]:
    """
    EGI with unit-level vacancy rates.

    Returns: (egi, total_vacancy_loss)

    Vacancy loss uses the unit's own vacancy_rate if set, else the property default.
    Vacant units already have $0 rent — no double-counting.
    """
    vacancy_loss = 0.0
    for unit in units:
        if unit.rent_type in (RentType.VACANT, RentType.OWNER_OCCUPIED):
            continue
        rate = unit.vacancy_rate if unit.vacancy_rate is not None else default_vacancy_rate
        vacancy_loss += unit.current_rent * 12 * rate

    egi = gsi - vacancy_loss + other_income
    return egi, vacancy_loss


def net_operating_income(egi: float, total_opex: float) -> float:
    """
    NOI = EGI - Operating Expenses
    Debt service is NOT included — it belongs below the NOI line.
    """
    return egi - total_opex


def cap_rate(noi: float, purchase_price: float) -> float:
    """Cap Rate = NOI / Purchase Price. Returns 0 if price is 0."""
    return noi / purchase_price if purchase_price > 0 else 0.0


def cash_on_cash(cash_flow: float, total_cash_invested: float) -> float:
    """CoC = Annual Cash Flow Before Tax / Total Cash Invested."""
    return cash_flow / total_cash_invested if total_cash_invested > 0 else 0.0


def dscr(noi: float, ads: float) -> float:
    """DSCR = NOI / Annual Debt Service. > 1.25 is lender-comfortable."""
    return noi / ads if ads > 0 else float("inf")


def break_even_occupancy(opex: float, ads: float, gsi: float) -> float:
    """
    Break-even occupancy = (OpEx + Debt Service) / GSI
    The minimum occupancy rate to cover all obligations.
    Healthy: below 80%. Dangerous: above 90%.
    """
    return (opex + ads) / gsi if gsi > 0 else 1.0


def expense_ratio(opex: float, egi: float) -> float:
    """
    Expense Ratio = OpEx / EGI
    NYC multifamily benchmark: 35–55%
    Red flag: > 65%
    """
    return opex / egi if egi > 0 else 0.0


def loan_to_value(loan_amount: float, purchase_price: float) -> float:
    """LTV = Loan / Purchase Price."""
    return loan_amount / purchase_price if purchase_price > 0 else 0.0


# ---------------------------------------------------------------------------
# Rent roll analysis helpers
# ---------------------------------------------------------------------------

def _rent_roll_summary(units: list[UnitInput], gsi: float) -> RentRollSummary:
    stabilized = [u for u in units if u.rent_type == RentType.STABILIZED]
    free_market = [u for u in units if u.rent_type == RentType.FREE_MARKET]
    vacant = [u for u in units if u.rent_type == RentType.VACANT]
    owner = [u for u in units if u.rent_type == RentType.OWNER_OCCUPIED]

    rentable = len(stabilized) + len(free_market)
    rs_pct = len(stabilized) / rentable if rentable > 0 else 0.0

    avg_rs = (
        sum(u.current_rent for u in stabilized) / len(stabilized)
        if stabilized else None
    )
    avg_fm = (
        sum(u.current_rent for u in free_market) / len(free_market)
        if free_market else None
    )

    # Market rent uplift: how much more could this building earn if fully deregulated
    total_market = None
    discount = None
    if any(u.market_rent_est for u in units):
        total_market = sum(
            (u.market_rent_est or u.current_rent) * 12
            for u in units
            if u.rent_type not in (RentType.VACANT, RentType.OWNER_OCCUPIED)
        )
        discount = total_market - gsi

    return RentRollSummary(
        num_stabilized=len(stabilized),
        num_free_market=len(free_market),
        num_vacant=len(vacant),
        num_owner_occupied=len(owner),
        rs_percentage=rs_pct,
        monthly_gsi=gsi / 12,
        annual_gsi=gsi,
        avg_rent_stabilized=avg_rs,
        avg_rent_free_market=avg_fm,
        total_market_rent_estimate=total_market,
        stabilization_discount=discount,
    )


def _opex_by_category(prop: PropertyInput, egi: float) -> tuple[float, dict[str, float]]:
    """Returns (total_opex, breakdown_dict)."""
    by_cat: dict[str, float] = {}
    for exp in prop.expenses:
        by_cat[exp.category.value] = by_cat.get(exp.category.value, 0.0) + exp.annual_amount
    total = sum(by_cat.values())
    return total, by_cat


def _break_even_rent(
    opex: float, ads: float, occupied_units: int, prop: PropertyInput
) -> float:
    """
    Monthly rent per occupied unit needed to break even.
    Total needed = OpEx + ADS; spread across occupied units × 12 months.
    """
    if occupied_units == 0:
        return 0.0
    return (opex + ads) / (occupied_units * 12)


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

class FinancialEngine:
    """
    Stateless calculation engine. All methods are class-level — instantiation
    is not required. Pass a PropertyInput and receive structured results.
    """

    @classmethod
    def calculate(cls, prop: PropertyInput) -> FullFinancialResult:
        """
        Run the full Year-1 financial analysis.
        This is the primary entry point used by the API and tests.
        """
        assumptions = prop.assumptions

        # ── Income ──────────────────────────────────────────────────────────
        gsi = gross_scheduled_income(prop.units)
        egi, vac_loss = effective_gross_income(
            gsi,
            prop.units,
            assumptions.general_vacancy_rate,
            assumptions.other_income_annual,
        )
        income = IncomeMetrics(
            gross_scheduled_income=gsi,
            vacancy_loss=vac_loss,
            effective_gross_income=egi - assumptions.other_income_annual,
            other_income=assumptions.other_income_annual,
            total_income=egi,
        )

        # ── Expenses ─────────────────────────────────────────────────────────
        total_opex, opex_by_cat = _opex_by_category(prop, egi)
        noi = net_operating_income(egi, total_opex)
        operating = OperatingMetrics(
            total_operating_expenses=total_opex,
            expense_by_category=opex_by_cat,
            net_operating_income=noi,
            expense_ratio=expense_ratio(total_opex, egi),
        )

        # ── Debt ─────────────────────────────────────────────────────────────
        debt_metrics: Optional[DebtMetrics] = None
        ads = 0.0
        if prop.loan:
            ads = annual_debt_service(prop.loan)
            pmt = ads / 12
            # Year-1 interest and principal split
            r = prop.loan.interest_rate / 12
            y1_interest = sum(
                (prop.loan.loan_amount - sum(
                    monthly_payment(prop.loan.loan_amount, prop.loan.interest_rate,
                                    prop.loan.amortization_years or prop.loan.term_years)
                    - (prop.loan.loan_amount - sum(
                        monthly_payment(prop.loan.loan_amount, prop.loan.interest_rate,
                                        prop.loan.amortization_years or prop.loan.term_years)
                        for _ in range(m)
                    ) + 0) * r
                    for _ in range(m)
                )) * r
                for m in range(12)
            )
            # Simpler year-1 I&P calculation
            y1_interest = cls._year1_interest(prop.loan)
            y1_principal = ads - y1_interest

            debt_metrics = DebtMetrics(
                monthly_payment=pmt,
                annual_debt_service=ads,
                year1_interest=y1_interest,
                year1_principal=y1_principal,
                dscr=dscr(noi, ads),
                loan_to_value=loan_to_value(prop.loan.loan_amount, prop.purchase_price),
            )

        # ── Returns ─────────────────────────────────────────────────────────
        cf = noi - ads
        total_invested = prop.total_cash_invested
        returns = ReturnMetrics(
            cash_flow_before_tax=cf,
            cash_on_cash_return=cash_on_cash(cf, total_invested),
            cap_rate=cap_rate(noi, prop.purchase_price),
            total_cash_invested=total_invested,
            equity_at_purchase=prop.down_payment,
        )

        # ── Valuation ────────────────────────────────────────────────────────
        implied_val = noi / assumptions.exit_cap_rate if assumptions.exit_cap_rate > 0 else 0.0
        ppsf = (
            prop.purchase_price / prop.gross_sq_ft
            if prop.gross_sq_ft and prop.gross_sq_ft > 0
            else None
        )
        valuation = ValuationMetrics(
            price_per_unit=prop.purchase_price / prop.num_units,
            price_per_sq_ft=ppsf,
            implied_value_at_cap=implied_val,
        )

        # ── Break-even ───────────────────────────────────────────────────────
        be_occ = break_even_occupancy(total_opex, ads, gsi)
        occupied_count = sum(
            1 for u in prop.units
            if u.rent_type not in (RentType.VACANT, RentType.OWNER_OCCUPIED)
        )
        be_rent = _break_even_rent(total_opex, ads, occupied_count, prop)
        break_even = BreakEvenMetrics(
            break_even_occupancy=be_occ,
            break_even_rent=be_rent,
        )

        # ── Rent Roll ────────────────────────────────────────────────────────
        rent_roll = _rent_roll_summary(prop.units, gsi)

        return FullFinancialResult(
            income=income,
            operating=operating,
            debt=debt_metrics,
            returns=returns,
            valuation=valuation,
            break_even=break_even,
            rent_roll=rent_roll,
        )

    @staticmethod
    def _year1_interest(loan: LoanInput) -> float:
        """
        Calculate total interest paid in year 1 of the loan.
        For IO loans: full year's interest = loan × annual_rate.
        For amortizing: sum the interest portion of each of the first 12 payments.
        """
        if loan.is_interest_only or loan.io_period_years >= 1:
            return loan.loan_amount * loan.interest_rate

        r = loan.interest_rate / 12
        amort_years = loan.amortization_years or loan.term_years
        pmt = monthly_payment(loan.loan_amount, loan.interest_rate, amort_years)

        balance = loan.loan_amount
        total_interest = 0.0
        for _ in range(12):
            interest = balance * r
            principal = pmt - interest
            total_interest += interest
            balance -= principal
        return total_interest

    @classmethod
    def quick_estimate(
        cls,
        purchase_price: float,
        total_monthly_rent: float,
        vacancy_rate: float,
        total_annual_expenses: float,
        loan_amount: float,
        annual_rate: float,
        term_years: int,
        closing_costs: float = 0.0,
    ) -> dict:
        """
        Fast back-of-envelope calculation without unit-level detail.
        Used for the "quick check" widget on the UI.
        """
        gsi = total_monthly_rent * 12
        vac_loss = gsi * vacancy_rate
        egi = gsi - vac_loss
        noi = egi - total_annual_expenses
        ads = monthly_payment(loan_amount, annual_rate, term_years) * 12
        cf = noi - ads
        down = purchase_price - loan_amount
        total_invested = down + closing_costs

        return {
            "gsi": round(gsi, 2),
            "egi": round(egi, 2),
            "noi": round(noi, 2),
            "annual_debt_service": round(ads, 2),
            "cash_flow": round(cf, 2),
            "cap_rate": round(cap_rate(noi, purchase_price) * 100, 2),
            "coc_return": round(cash_on_cash(cf, total_invested) * 100, 2),
            "dscr": round(dscr(noi, ads), 2),
            "break_even_occupancy": round(break_even_occupancy(total_annual_expenses, ads, gsi) * 100, 2),
        }
