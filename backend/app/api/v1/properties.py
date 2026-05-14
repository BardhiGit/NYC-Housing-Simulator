"""
Properties CRUD + nested unit / loan / expense endpoints.

All endpoints require authentication. Users can only access their own properties.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.db.models.expense import Expense
from app.db.models.loan import Loan
from app.db.models.property import Property
from app.db.models.unit import Unit
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.property import (
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
    LoanCreate,
    LoanResponse,
    LoanUpdate,
    PropertyCreate,
    PropertyDetailResponse,
    PropertyResponse,
    PropertyUpdate,
    UnitCreate,
    UnitResponse,
    UnitUpdate,
)

router = APIRouter(prefix="/properties", tags=["properties"])


# ---------------------------------------------------------------------------
# Property CRUD
# ---------------------------------------------------------------------------

@router.get("", response_model=list[PropertyResponse])
async def list_properties(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Property)
        .where(Property.user_id == user.id)
        .order_by(Property.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=PropertyResponse, status_code=201)
async def create_property(
    body: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prop = Property(
        user_id=user.id,
        name=body.name,
        address=body.address,
        borough=body.borough.value,
        year_built=body.year_built,
        gross_sq_ft=body.gross_sq_ft,
        num_units=body.num_units,
        purchase_price=body.purchase_price,
        closing_costs=body.closing_costs,
        renovation_budget_total=body.renovation_budget_total,
        assumptions=body.assumptions.model_dump(),
    )
    db.add(prop)
    await db.flush()
    return prop


@router.get("/{property_id}", response_model=PropertyDetailResponse)
async def get_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prop = await _load_property(db, property_id, user.id)
    return prop


@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: uuid.UUID,
    body: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prop = await _load_property(db, property_id, user.id)
    updates = body.model_dump(exclude_none=True)
    for field, value in updates.items():
        if field == "assumptions":
            prop.assumptions = value.model_dump() if hasattr(value, "model_dump") else value
        elif field == "borough":
            prop.borough = value.value if hasattr(value, "value") else value
        else:
            setattr(prop, field, value)
    return prop


@router.delete("/{property_id}", status_code=204)
async def delete_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prop = await _load_property(db, property_id, user.id)
    await db.delete(prop)


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------

@router.get("/{property_id}/units", response_model=list[UnitResponse])
async def list_units(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _load_property(db, property_id, user.id)  # authorization check
    result = await db.execute(select(Unit).where(Unit.property_id == property_id))
    return result.scalars().all()


@router.post("/{property_id}/units", response_model=UnitResponse, status_code=201)
async def add_unit(
    property_id: uuid.UUID,
    body: UnitCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _load_property(db, property_id, user.id)
    unit = Unit(
        property_id=property_id,
        unit_number=body.unit_number,
        bedrooms=body.bedrooms,
        bathrooms=body.bathrooms,
        sq_ft=body.sq_ft,
        rent_type=body.rent_type.value,
        current_rent=body.current_rent,
        legal_rent=body.legal_rent,
        preferential_rent=body.preferential_rent,
        market_rent_est=body.market_rent_est,
        lease_expiry=body.lease_expiry,
        vacancy_rate=body.vacancy_rate,
        rent_growth_override=body.rent_growth_override,
        renovation_budget=body.renovation_budget,
        notes=body.notes,
    )
    db.add(unit)
    await db.flush()
    return unit


@router.put("/{property_id}/units/{unit_id}", response_model=UnitResponse)
async def update_unit(
    property_id: uuid.UUID,
    unit_id: uuid.UUID,
    body: UnitUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _load_property(db, property_id, user.id)
    unit = await _get_unit(db, unit_id, property_id)
    for field, value in body.model_dump(exclude_none=True).items():
        if field == "rent_type":
            unit.rent_type = value.value if hasattr(value, "value") else value
        else:
            setattr(unit, field, value)
    return unit


@router.delete("/{property_id}/units/{unit_id}", status_code=204)
async def delete_unit(
    property_id: uuid.UUID,
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _load_property(db, property_id, user.id)
    unit = await _get_unit(db, unit_id, property_id)
    await db.delete(unit)


# ---------------------------------------------------------------------------
# Loan
# ---------------------------------------------------------------------------

@router.post("/{property_id}/loan", response_model=LoanResponse, status_code=201)
async def set_loan(
    property_id: uuid.UUID,
    body: LoanCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prop = await _load_property(db, property_id, user.id)
    # Delete existing loan if any (one loan per property)
    if prop.loan:
        await db.delete(prop.loan)
        await db.flush()

    loan = Loan(
        property_id=property_id,
        loan_amount=body.loan_amount,
        interest_rate=body.interest_rate,
        term_years=body.term_years,
        amortization_years=body.amortization_years,
        is_interest_only=body.is_interest_only,
        io_period_years=body.io_period_years,
    )
    db.add(loan)
    await db.flush()
    return loan


@router.put("/{property_id}/loan", response_model=LoanResponse)
async def update_loan(
    property_id: uuid.UUID,
    body: LoanUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prop = await _load_property(db, property_id, user.id)
    if not prop.loan:
        raise HTTPException(status_code=404, detail="No loan found — use POST to create one")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(prop.loan, field, value)
    return prop.loan


@router.delete("/{property_id}/loan", status_code=204)
async def delete_loan(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prop = await _load_property(db, property_id, user.id)
    if prop.loan:
        await db.delete(prop.loan)


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------

@router.get("/{property_id}/expenses", response_model=list[ExpenseResponse])
async def list_expenses(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _load_property(db, property_id, user.id)
    result = await db.execute(select(Expense).where(Expense.property_id == property_id))
    return result.scalars().all()


@router.post("/{property_id}/expenses", response_model=ExpenseResponse, status_code=201)
async def add_expense(
    property_id: uuid.UUID,
    body: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _load_property(db, property_id, user.id)
    expense = Expense(
        property_id=property_id,
        category=body.category.value,
        annual_amount=body.annual_amount,
        growth_rate=body.growth_rate,
        notes=body.notes,
    )
    db.add(expense)
    await db.flush()
    return expense


@router.put("/{property_id}/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    property_id: uuid.UUID,
    expense_id: uuid.UUID,
    body: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _load_property(db, property_id, user.id)
    result = await db.execute(
        select(Expense).where(Expense.id == expense_id, Expense.property_id == property_id)
    )
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    for field, value in body.model_dump(exclude_none=True).items():
        if field == "category":
            expense.category = value.value if hasattr(value, "value") else value
        else:
            setattr(expense, field, value)
    return expense


@router.delete("/{property_id}/expenses/{expense_id}", status_code=204)
async def delete_expense(
    property_id: uuid.UUID,
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _load_property(db, property_id, user.id)
    result = await db.execute(
        select(Expense).where(Expense.id == expense_id, Expense.property_id == property_id)
    )
    expense = result.scalar_one_or_none()
    if expense:
        await db.delete(expense)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _load_property(
    db: AsyncSession,
    property_id: uuid.UUID,
    user_id: uuid.UUID,
    with_relations: bool = True,
) -> Property:
    """Load property with all relationships, enforcing user ownership."""
    query = select(Property).where(Property.id == property_id, Property.user_id == user_id)
    if with_relations:
        query = query.options(
            selectinload(Property.units),
            selectinload(Property.loan),
            selectinload(Property.expenses),
            selectinload(Property.scenarios),
        )
    result = await db.execute(query)
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


async def _get_unit(db: AsyncSession, unit_id: uuid.UUID, property_id: uuid.UUID) -> Unit:
    result = await db.execute(
        select(Unit).where(Unit.id == unit_id, Unit.property_id == property_id)
    )
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit
