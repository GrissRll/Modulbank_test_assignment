from sqlalchemy import (
    Numeric,
    Enum,
    String,
    DateTime,
    Text,
    CheckConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from decimal import Decimal
from datetime import datetime
from enum import StrEnum

from app.db.base import Base


class OperationStatus(StrEnum):
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class Currency(StrEnum):
    RUB = "RUB"


class Operation(Base):
    __tablename__ = "operations"

    operation_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[OperationStatus] = mapped_column(
        Enum(OperationStatus, name="operation_status"),
        default=OperationStatus.CREATED,
        server_default=OperationStatus.CREATED.value,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    __table_args__ = (CheckConstraint("amount > 0", name="ck_amount_gt_0"),)

    events: Mapped[list["OperationEvent"]] = relationship(
        back_populates="operation",
        cascade="all, delete-orphan",
        order_by="OperationEvent.event_id",
    )

    receipts: Mapped[list["Receipt"]] = relationship(
        back_populates="operation",
        cascade="all, delete-orphan",
    )
