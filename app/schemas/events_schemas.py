from pydantic import BaseModel, Field
from app.models.operation import OperationStatus
from datetime import datetime


class EventSchema(BaseModel):
    operation_id: str
    event_id: int
    event_type: OperationStatus
    from_status: OperationStatus | None
    to_status: OperationStatus | None
    message: str = Field(...)

class ResponseEventSchema(EventSchema):
    occurred_at: datetime