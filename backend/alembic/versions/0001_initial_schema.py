"""Initial schema — all tables

Revision ID: 0001
Revises:
Create Date: 2025-01-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Users
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False, server_default=""),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Properties
    op.create_table(
        "properties",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), server_default=""),
        sa.Column("address", sa.String(500), server_default=""),
        sa.Column("borough", sa.String(50), server_default="brooklyn"),
        sa.Column("year_built", sa.Integer(), nullable=True),
        sa.Column("gross_sq_ft", sa.Float(), nullable=True),
        sa.Column("num_units", sa.Integer(), nullable=False),
        sa.Column("purchase_price", sa.Float(), nullable=False),
        sa.Column("closing_costs", sa.Float(), server_default="0"),
        sa.Column("renovation_budget_total", sa.Float(), server_default="0"),
        sa.Column("assumptions", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_properties_user_id", "properties", ["user_id"])

    # Units
    op.create_table(
        "units",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unit_number", sa.String(20), nullable=False),
        sa.Column("bedrooms", sa.Integer(), server_default="1"),
        sa.Column("bathrooms", sa.Float(), server_default="1.0"),
        sa.Column("sq_ft", sa.Float(), nullable=True),
        sa.Column("rent_type", sa.String(30), nullable=False),
        sa.Column("current_rent", sa.Float(), server_default="0"),
        sa.Column("legal_rent", sa.Float(), nullable=True),
        sa.Column("preferential_rent", sa.Float(), nullable=True),
        sa.Column("market_rent_est", sa.Float(), nullable=True),
        sa.Column("lease_expiry", sa.Date(), nullable=True),
        sa.Column("vacancy_rate", sa.Float(), server_default="0.05"),
        sa.Column("rent_growth_override", sa.Float(), nullable=True),
        sa.Column("renovation_budget", sa.Float(), server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_units_property_id", "units", ["property_id"])

    # Loans
    op.create_table(
        "loans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("loan_amount", sa.Float(), nullable=False),
        sa.Column("interest_rate", sa.Float(), nullable=False),
        sa.Column("term_years", sa.Integer(), nullable=False),
        sa.Column("amortization_years", sa.Integer(), nullable=True),
        sa.Column("is_interest_only", sa.Boolean(), server_default="false"),
        sa.Column("io_period_years", sa.Integer(), server_default="0"),
    )

    # Expenses
    op.create_table(
        "expenses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("annual_amount", sa.Float(), nullable=False),
        sa.Column("growth_rate", sa.Float(), server_default="0.03"),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_expenses_property_id", "expenses", ["property_id"])

    # Scenarios
    op.create_table(
        "scenarios",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("type", sa.String(50), server_default="custom"),
        sa.Column("overrides", JSONB, nullable=False, server_default="{}"),
        sa.Column("results", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_scenarios_property_id", "scenarios", ["property_id"])


def downgrade() -> None:
    op.drop_table("scenarios")
    op.drop_table("expenses")
    op.drop_table("loans")
    op.drop_table("units")
    op.drop_table("properties")
    op.drop_table("users")
