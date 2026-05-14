"""
Multi-year cash flow projection engine.

Models annual cash flows over the holding period and computes:
  - NOI growth (RS-capped vs. FM-market)
  - Expense growth (inflation-driven)
  - Loan amortization (balance at each year)
  - Property value (income approach: NOI / cap_rate)
  - Exit proceeds
  - IRR and NPV on equity

Rent-stabilization rules applied:
  - RS units: growth capped at rs_rent_growth_rate (reflects RGB orders)
  - FM units: growth at fm_rent_growth_rate
  - Vacant units: no income; when unit "turns over" it earns legal rent (RS)
    or market rent (FM) at the property-level assumption
"""

from __future__ import annotations

import math
from typing import Optional

from app.models.inputs import LoanInput, PropertyInput, RentType, UnitInput
from app.models.outputs import ProjectionResult, YearlyProjection
from app.services.amortization import balance_at_year
from app.services.financial_engine import (
    annual_debt_service,
    break_even_occupancy,
    cap_rate as calc_cap_rate,
    cash_on_cash,
    dscr,
    effective_gross_income,
    expense_ratio,
)


# ---------------------------------------------------------------------------
# IRR / NPV helpers
# ---------------------------------------------------------------------------

def calculate_npv(cash_flows: list[float], discount_rate: float) -> float:
    """NPV = Σ CF_t / (1 + r)^t"""
    return sum(cf / (1 + discount_rate) ** t for t, cf in enumerate(cash_flows))


def calculate_irr(
    cash_flows: list[float],
    initial_guess: float = 0.10,
    tolerance: float = 1e-7,
    max_iter: int = 1_000,
) -> float:
    """
    IRR via Newton-Raphson, with bisection fallback.
    cash_flows[0] must be negative (equity outlay at purchase).
    Returns the annualized IRR as a decimal (0.12 = 12%).
    Returns NaN if no solution found (e.g., all cash flows positive or negative).
    """
    try:
        import numpy_financial as npf  # type: ignore
        result = npf.irr(cash_flows)
        if result is not None and not math.isnan(result):
            return float(result)
    except Exception:
        pass

    # Newton-Raphson fallback
    rate = initial_guess
    for _ in range(max_iter):
        npv = sum(cf / (1 + rate) ** t for t, cf in enumerate(cash_flows))
        dnpv = sum(
            -t * cf / (1 + rate) ** (t + 1)
            for t, cf in enumerate(cash_flows)
            if t > 0
        )
        if abs(dnpv) < 1e-14:
            break
        new_rate = rate - npv / dnpv
        if abs(new_rate - rate) < tolerance:
            return new_rate
        # Clamp to avoid divergence
        rate = max(-0.9999, min(new_rate, 50.0))

    # Bisection fallback
    return _bisection_irr(cash_flows)


def _bisection_irr(
    cash_flows: list[float],
    low: float = -0.999,
    high: float = 10.0,
    tol: float = 1e-6,
    max_iter: int = 200,
) -> float:
    def npv(r: float) -> float:
        return sum(cf / (1 + r) ** t for t, cf in enumerate(cash_flows))

    npv_low, npv_high = npv(low), npv(high)
    if npv_low * npv_high > 0:
        return float("nan")

    for _ in range(max_iter):
        mid = (low + high) / 2
        npv_mid = npv(mid)
        if abs(npv_mid) < tol:
            return mid
        if npv_low * npv_mid < 0:
            high = mid
            npv_high = npv_mid
        else:
            low = mid
            npv_low = npv_mid

    return (low + high) / 2


# ---------------------------------------------------------------------------
# Rent growth logic
# ---------------------------------------------------------------------------

def _grow_unit_rent(unit: UnitInput, fm_growth: float, rs_growth: float) -> float:
    """
    Return the new annual rent for a unit after one year of growth.

    RS rules:
      - Growth capped at rs_growth (reflects RGB orders)
      - New rent cannot exceed legal_rent (DHCR cap)
      - Post-HSTPA 2019: preferential rent carries through tenancy

    FM rules:
      - Growth at fm_growth (market-driven)
    """
    if unit.rent_type in (RentType.VACANT, RentType.OWNER_OCCUPIED):
        return unit.current_rent  # no change

    rate = unit.rent_growth_override if unit.rent_growth_override is not None else (
        rs_growth if unit.rent_type == RentType.STABILIZED else fm_growth
    )

    new_rent = unit.current_rent * (1 + rate)

    # RS: can never exceed legal rent
    if unit.rent_type == RentType.STABILIZED and unit.legal_rent:
        new_rent = min(new_rent, unit.legal_rent)

    return new_rent


def _project_unit_rents(
    units: list[UnitInput],
    fm_growth: float,
    rs_growth: float,
    year: int,
) -> list[float]:
    """
    Compound rent growth for `year` years. Returns list of monthly rents.
    This is applied cumulatively — not recalculated from scratch each year.
    """
    rents = []
    for unit in units:
        rent = unit.current_rent
        legal = unit.legal_rent

        for _ in range(year):
            if unit.rent_type in (RentType.VACANT, RentType.OWNER_OCCUPIED):
                break
            rate = unit.rent_growth_override if unit.rent_growth_override is not None else (
                rs_growth if unit.rent_type == RentType.STABILIZED else fm_growth
            )
            rent = rent * (1 + rate)
            if unit.rent_type == RentType.STABILIZED and legal:
                rent = min(rent, legal)

        rents.append(rent)
    return rents


# ---------------------------------------------------------------------------
# Main projection service
# ---------------------------------------------------------------------------

class ProjectionService:

    @classmethod
    def project(
        cls,
        prop: PropertyInput,
        override_assumptions: Optional[dict] = None,
    ) -> ProjectionResult:
        """
        Build a year-by-year projection over the holding period.

        override_assumptions: dict of AssumptionInput field names → new values.
        Used by the scenario engine to run "what-if" projections without
        modifying the base property.
        """
        a = prop.assumptions

        # Apply any scenario overrides
        fm_growth = override_assumptions.get("fm_rent_growth_rate", a.fm_rent_growth_rate) if override_assumptions else a.fm_rent_growth_rate
        rs_growth = override_assumptions.get("rs_rent_growth_rate", a.rs_rent_growth_rate) if override_assumptions else a.rs_rent_growth_rate
        exp_growth = override_assumptions.get("expense_growth_rate", a.expense_growth_rate) if override_assumptions else a.expense_growth_rate
        exit_cap = override_assumptions.get("exit_cap_rate", a.exit_cap_rate) if override_assumptions else a.exit_cap_rate
        vacancy = override_assumptions.get("general_vacancy_rate", a.general_vacancy_rate) if override_assumptions else a.general_vacancy_rate
        holding = override_assumptions.get("holding_period", a.holding_period) if override_assumptions else a.holding_period
        discount = override_assumptions.get("discount_rate", a.discount_rate) if override_assumptions else a.discount_rate
        sell_costs_pct = override_assumptions.get("selling_costs_pct", a.selling_costs_pct) if override_assumptions else a.selling_costs_pct

        ads = annual_debt_service(prop.loan) if prop.loan else 0.0
        total_invested = prop.total_cash_invested

        # Cash flow series for IRR: index 0 = initial equity outlay (negative)
        irr_cashflows: list[float] = [-total_invested]

        yearly_projections: list[YearlyProjection] = []
        cum_cf = 0.0

        base_opex = sum(e.annual_amount for e in prop.expenses)

        for yr in range(1, holding + 1):
            # ── Grow rents ──────────────────────────────────────────────────
            year_rents = _project_unit_rents(prop.units, fm_growth, rs_growth, yr)

            # Rebuild GSI from projected rents
            gsi = sum(
                rent * 12
                for unit, rent in zip(prop.units, year_rents)
                if unit.rent_type not in (RentType.VACANT, RentType.OWNER_OCCUPIED)
            )

            # Apply vacancy (unit-level or default)
            vac_loss = sum(
                rent * 12 * (unit.vacancy_rate if unit.vacancy_rate is not None else vacancy)
                for unit, rent in zip(prop.units, year_rents)
                if unit.rent_type not in (RentType.VACANT, RentType.OWNER_OCCUPIED)
            )

            egi = gsi - vac_loss + a.other_income_annual

            # ── Grow expenses ───────────────────────────────────────────────
            opex = base_opex * (1 + exp_growth) ** yr

            noi = egi - opex

            # ── Loan balance ────────────────────────────────────────────────
            loan_balance = balance_at_year(prop.loan, yr) if prop.loan else 0.0

            # ── Property value (income approach) ────────────────────────────
            prop_value = noi / exit_cap if exit_cap > 0 else 0.0

            equity = prop_value - loan_balance

            cf = noi - ads
            cum_cf += cf

            yearly_projections.append(YearlyProjection(
                year=yr,
                gsi=round(gsi, 2),
                egi=round(egi, 2),
                operating_expenses=round(opex, 2),
                noi=round(noi, 2),
                debt_service=round(ads, 2),
                cash_flow=round(cf, 2),
                loan_balance=round(loan_balance, 2),
                property_value=round(prop_value, 2),
                equity=round(equity, 2),
                cumulative_cash_flow=round(cum_cf, 2),
                dscr=round(dscr(noi, ads), 4),
                cap_rate=round(calc_cap_rate(noi, prop.purchase_price), 4),
                coc_return=round(cash_on_cash(cf, total_invested), 4),
            ))

            irr_cashflows.append(cf)

        # ── Exit calculation ─────────────────────────────────────────────────
        exit_noi = yearly_projections[-1].noi
        exit_value = exit_noi / exit_cap if exit_cap > 0 else 0.0
        exit_loan_balance = yearly_projections[-1].loan_balance
        exit_selling = exit_value * sell_costs_pct
        exit_net_proceeds = exit_value - exit_selling - exit_loan_balance

        # Add exit proceeds to final year CF for IRR
        irr_cashflows[-1] += exit_net_proceeds

        total_op_cf = sum(yr.cash_flow for yr in yearly_projections)
        total_return = total_op_cf + exit_net_proceeds
        init_equity = total_invested

        # Equity multiple: total dollar return / equity invested
        equity_multiple = (total_return + init_equity) / init_equity if init_equity > 0 else 0.0

        irr = calculate_irr(irr_cashflows)
        npv = calculate_npv(irr_cashflows, discount)

        return ProjectionResult(
            years=yearly_projections,
            holding_period=holding,
            exit_year=holding,
            exit_property_value=round(exit_value, 2),
            exit_loan_balance=round(exit_loan_balance, 2),
            exit_selling_costs=round(exit_selling, 2),
            exit_net_proceeds=round(exit_net_proceeds, 2),
            total_operating_cash_flow=round(total_op_cf, 2),
            total_return=round(total_return, 2),
            equity_multiple=round(equity_multiple, 3),
            irr=round(irr, 5) if not math.isnan(irr) else 0.0,
            npv=round(npv, 2),
        )
