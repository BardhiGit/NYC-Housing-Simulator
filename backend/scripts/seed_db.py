"""
Database seeder — inserts the three demo properties for portfolio demos.

Usage:
  cd backend
  python -m scripts.seed_db

Requires a running PostgreSQL instance and migrated schema.
"""

from __future__ import annotations

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.db.models.expense import Expense
from app.db.models.loan import Loan
from app.db.models.property import Property
from app.db.models.unit import Unit
from app.db.models.user import User
from data.seed_data import get_all_seed_properties


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        # Create demo user
        demo_user = User(
            email="demo@strataview.nyc",
            name="Demo Investor",
            password_hash=hash_password("demo1234"),
        )
        db.add(demo_user)
        await db.flush()

        seed_props = get_all_seed_properties()
        for prop_input in seed_props:
            # Create property
            prop = Property(
                user_id=demo_user.id,
                name=prop_input.name,
                address=prop_input.address,
                borough=prop_input.borough.value,
                year_built=prop_input.year_built,
                gross_sq_ft=prop_input.gross_sq_ft,
                num_units=prop_input.num_units,
                purchase_price=prop_input.purchase_price,
                closing_costs=prop_input.closing_costs,
                renovation_budget_total=prop_input.renovation_budget_total,
                assumptions=prop_input.assumptions.model_dump(),
            )
            db.add(prop)
            await db.flush()

            # Units
            for u in prop_input.units:
                unit = Unit(
                    property_id=prop.id,
                    unit_number=u.unit_number,
                    bedrooms=u.bedrooms,
                    bathrooms=u.bathrooms,
                    sq_ft=u.sq_ft,
                    rent_type=u.rent_type.value,
                    current_rent=u.current_rent,
                    legal_rent=u.legal_rent,
                    preferential_rent=u.preferential_rent,
                    market_rent_est=u.market_rent_est,
                    lease_expiry=str(u.lease_expiry) if u.lease_expiry else None,
                    vacancy_rate=u.vacancy_rate,
                    rent_growth_override=u.rent_growth_override,
                    renovation_budget=u.renovation_budget,
                    notes=u.notes,
                )
                db.add(unit)

            # Loan
            if prop_input.loan:
                loan = Loan(
                    property_id=prop.id,
                    loan_amount=prop_input.loan.loan_amount,
                    interest_rate=prop_input.loan.interest_rate,
                    term_years=prop_input.loan.term_years,
                    amortization_years=prop_input.loan.amortization_years,
                    is_interest_only=prop_input.loan.is_interest_only,
                    io_period_years=prop_input.loan.io_period_years,
                )
                db.add(loan)

            # Expenses
            for e in prop_input.expenses:
                expense = Expense(
                    property_id=prop.id,
                    category=e.category.value,
                    annual_amount=e.annual_amount,
                    growth_rate=e.growth_rate,
                    notes=e.notes,
                )
                db.add(expense)

        await db.commit()
        print(f"✓ Seeded {len(seed_props)} properties for user: {demo_user.email}")
        print("  Login: demo@strataview.nyc / demo1234")


if __name__ == "__main__":
    asyncio.run(seed())
