from sqlalchemy import (
    Enum,
    String,
    DateTime,
    Text,
    func,
    Integer,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from datetime import datetime

from app.db.base import Base
from app.models.operation import OperationStatus


class OperationEvent(Base):
    __tablename__ = "operation_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_id: Mapped[str] = mapped_column(
        String(120),
        ForeignKey("operations.operation_id", ondelete="CASCADE"),
        nullable=False,
    )
    event_id: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[OperationStatus] = mapped_column(
        Enum(OperationStatus, name="operation_status")
    )
    from_status: Mapped[OperationStatus | None] = mapped_column(
        Enum(OperationStatus, name="operation_status"), nullable=True
    )
    to_status: Mapped[OperationStatus | None] = mapped_column(
        Enum(OperationStatus, name="operation_status"), nullable=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    operation: Mapped["Operation"] = relationship(
        back_populates="events",
    )

    __table_args__ = (
        UniqueConstraint(
            "operation_id",
            "event_id",
            name="uq_operation_events_operation_id_event_id",
        ),
        CheckConstraint(
            "event_id > 0",
            name="ck_operation_events_event_id_positive",
        ),
    )
