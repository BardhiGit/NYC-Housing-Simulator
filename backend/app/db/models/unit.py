from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True
    )

    unit_number: Mapped[str] = mapped_column(String(20), nullable=False)
    bedrooms: Mapped[int] = mapped_column(Integer, default=1)
    bathrooms: Mapped[float] = mapped_column(Float, default=1.0)
    sq_ft: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    rent_type: Mapped[str] = mapped_column(String(30), nullable=False)  # stabilized|free_market|vacant|owner_occupied
    current_rent: Mapped[float] = mapped_column(Float, default=0.0)
    legal_rent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    preferential_rent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    market_rent_est: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    lease_expiry: Mapped[Optional[str]] = mapped_column(Date, nullable=True)  # stored as ISO date string
    vacancy_rate: Mapped[float] = mapped_column(Float, default=0.05)
    rent_growth_override: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    renovation_budget: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    property: Mapped["Property"] = relationship("Property", back_populates="units")  # type: ignore[name-defined]
