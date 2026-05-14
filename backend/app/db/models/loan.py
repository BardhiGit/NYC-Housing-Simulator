from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    loan_amount: Mapped[float] = mapped_column(Float, nullable=False)
    interest_rate: Mapped[float] = mapped_column(Float, nullable=False)
    term_years: Mapped[int] = mapped_column(Integer, nullable=False)
    amortization_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_interest_only: Mapped[bool] = mapped_column(Boolean, default=False)
    io_period_years: Mapped[int] = mapped_column(Integer, default=0)

    property: Mapped["Property"] = relationship("Property", back_populates="loan")  # type: ignore[name-defined]
