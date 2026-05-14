"""
Converters: database ORM models → financial engine Pydantic input models.

This is the bridge between persistence and calculation.
The financial engine only knows about PropertyInput — it has no DB awareness.
"""

from __future__ import annotations

from datetime import date

from app.db.models.expense import Expense as ExpenseORM
from app.db.models.loan import Loan as LoanORM
from app.db.models.property import Property as PropertyORM
from app.db.models.unit import Unit as UnitORM
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


def orm_to_property_input(prop: PropertyORM) -> PropertyInput:
    """
    Convert a fully-loaded PropertyORM (with units, loan, expenses loaded)
    into a PropertyInput suitable for the financial engine.

    The PropertyORM must have its relationships eagerly loaded before calling this.
    """
    units = [orm_to_unit_input(u) for u in (prop.units or [])]
    loan = orm_to_loan_input(prop.loan) if prop.loan else None
    expenses = [orm_to_expense_input(e) for e in (prop.expenses or [])]
    assumptions = _orm_to_assumptions(prop.assumptions or {})

    return PropertyInput(
        name=prop.name or "",
        address=prop.address or "",
        borough=Borough(prop.borough) if prop.borough else Borough.BROOKLYN,
        year_built=prop.year_built,
        gross_sq_ft=prop.gross_sq_ft,
        num_units=prop.num_units,
        purchase_price=prop.purchase_price,
        closing_costs=prop.closing_costs or 0.0,
        renovation_budget_total=prop.renovation_budget_total or 0.0,
        units=units,
        loan=loan,
        expenses=expenses,
        assumptions=assumptions,
    )


def orm_to_unit_input(unit: UnitORM) -> UnitInput:
    lease = None
    if unit.lease_expiry:
        if isinstance(unit.lease_expiry, str):
            try:
                lease = date.fromisoformat(unit.lease_expiry)
            except ValueError:
                pass
        elif isinstance(unit.lease_expiry, date):
            lease = unit.lease_expiry

    return UnitInput(
        unit_number=unit.unit_number,
        bedrooms=unit.bedrooms,
        bathrooms=unit.bathrooms,
        sq_ft=unit.sq_ft,
        rent_type=RentType(unit.rent_type),
        current_rent=unit.current_rent,
        legal_rent=unit.legal_rent,
        preferential_rent=unit.preferential_rent,
        market_rent_est=unit.market_rent_est,
        lease_expiry=lease,
        vacancy_rate=unit.vacancy_rate,
        rent_growth_override=unit.rent_growth_override,
        renovation_budget=unit.renovation_budget or 0.0,
        notes=unit.notes,
    )


def orm_to_loan_input(loan: LoanORM) -> LoanInput:
    return LoanInput(
        loan_amount=loan.loan_amount,
        interest_rate=loan.interest_rate,
        term_years=loan.term_years,
        amortization_years=loan.amortization_years,
        is_interest_only=loan.is_interest_only,
        io_period_years=loan.io_period_years or 0,
    )


def orm_to_expense_input(exp: ExpenseORM) -> ExpenseInput:
    return ExpenseInput(
        category=ExpenseCategory(exp.category),
        annual_amount=exp.annual_amount,
        growth_rate=exp.growth_rate,
        notes=exp.notes,
    )


def _orm_to_assumptions(data: dict) -> AssumptionInput:
    """
    Deserialize the JSONB assumptions blob into AssumptionInput.
    Falls back gracefully if fields are missing (old data, schema changes).
    """
    try:
        return AssumptionInput(**data)
    except Exception:
        return AssumptionInput()
