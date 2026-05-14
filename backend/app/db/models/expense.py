from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True
    )

    category: Mapped[str] = mapped_column(String(100), nullable=False)
    annual_amount: Mapped[float] = mapped_column(Float, nullable=False)
    growth_rate: Mapped[float] = mapped_column(Float, default=0.03)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    property: Mapped["Property"] = relationship("Property", back_populates="expenses")  # type: ignore[name-defined]
