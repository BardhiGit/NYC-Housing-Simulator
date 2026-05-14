from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), default="")
    address: Mapped[str] = mapped_column(String(500), default="")
    borough: Mapped[str] = mapped_column(String(50), default="brooklyn")
    year_built: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gross_sq_ft: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    num_units: Mapped[int] = mapped_column(Integer, nullable=False)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False)
    closing_costs: Mapped[float] = mapped_column(Float, default=0.0)
    renovation_budget_total: Mapped[float] = mapped_column(Float, default=0.0)

    # AssumptionInput stored as JSONB — avoids a separate table for a flat structure
    assumptions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="properties")  # type: ignore[name-defined]
    units: Mapped[list["Unit"]] = relationship(  # type: ignore[name-defined]
        "Unit", back_populates="property", cascade="all, delete-orphan"
    )
    loan: Mapped[Optional["Loan"]] = relationship(  # type: ignore[name-defined]
        "Loan", back_populates="property", uselist=False, cascade="all, delete-orphan"
    )
    expenses: Mapped[list["Expense"]] = relationship(  # type: ignore[name-defined]
        "Expense", back_populates="property", cascade="all, delete-orphan"
    )
    scenarios: Mapped[list["Scenario"]] = relationship(  # type: ignore[name-defined]
        "Scenario", back_populates="property", cascade="all, delete-orphan"
    )
