from pydantic import BaseModel, Field
from app.models.operation import Currency, OperationStatus
from decimal import Decimal

class OperationSchema(BaseModel):
    operation_id: str
    amount: Decimal = Field(gt=0)
    currency: Currency
    description: str | None = Field(default=None, max_length=500)


class ResponseOperationSchema(OperationSchema):
    status: OperationStatus
    provider_payment_id: str | None


