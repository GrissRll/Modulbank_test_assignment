from sqlalchemy import (
    Integer,
    DateTime,
    Text,
    String,
    CheckConstraint,
    func,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from typing import Any

from app.db.base import Base


class PaymentDispatch(Base):
    __tablename__ = "payment_dispatches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_id: Mapped[str] = mapped_column(
        String(120),
        ForeignKey("operations.operation_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(120), nullable=False, unique=True
    )
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    attempt_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    __table_args__ = (
        CheckConstraint("attempt_count >= 0", name="ck_attempt_count_ge0"),
    )
