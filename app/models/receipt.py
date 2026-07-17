from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReceiptResult(str, Enum):
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class ReceiptProcessingResult(str, Enum):
    APPLIED = "APPLIED"
    DUPLICATE = "DUPLICATE"
    IGNORED_CONFLICT = "IGNORED_CONFLICT"


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    operation_id: Mapped[str] = mapped_column(
        String(120),
        ForeignKey(
            "operations.operation_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    provider_payment_id: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    result: Mapped[ReceiptResult] = mapped_column(
        SqlEnum(
            ReceiptResult,
            name="receipt_result",
        ),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    provider_occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    processing_result: Mapped[ReceiptProcessingResult] = mapped_column(
        SqlEnum(
            ReceiptProcessingResult,
            name="receipt_processing_result",
        ),
        nullable=False,
    )

    payload_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    operation: Mapped["Operation"] = relationship(
        back_populates="receipts",
    )

    __table_args__ = (
        Index(
            "ix_receipts_operation_id_payload_hash",
            "operation_id",
            "payload_hash",
        ),
    )
