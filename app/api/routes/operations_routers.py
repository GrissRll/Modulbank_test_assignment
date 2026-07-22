from fastapi import APIRouter, status
from fastapi.params import Depends


from app.api.dependency import get_operation_service
from app.schemas.operation_schemas import (
    OperationSchema as CreateOperationSchema,
    ResponseOperationSchema,
)
from app.schemas.events_schemas import ResponseEventSchema
from app.services.operation_service import OperationService

router = APIRouter(prefix="/operations", tags=["operations"])


@router.post(
    "/", response_model=ResponseOperationSchema, status_code=status.HTTP_201_CREATED
)
async def create_operation(
    operation_data: CreateOperationSchema,
    operation_service: OperationService = Depends(get_operation_service),
):
    return await operation_service.register_operation(operation_data)


@router.get(
    "/{id}", response_model=ResponseOperationSchema, status_code=status.HTTP_200_OK
)
async def get_operation_by_id(
    id: str, operation_service: OperationService = Depends(get_operation_service)
):
    return await operation_service.get_operation_by_id(operation_id=id)


@router.get(
    "/{id}/events",
    response_model=list[ResponseEventSchema],
    status_code=status.HTTP_200_OK,
)
async def get_operation_event(
    id: str, operation_service: OperationService = Depends(get_operation_service)
):
    return await operation_service.get_events_by_operation_id(operation_id=id)


@router.post(
    "/{id}/submit", response_model=ResponseOperationSchema, status_code=status.HTTP_200_OK
)
async def submit_operation(
    id: str, operation_service: OperationService = Depends(get_operation_service)
):
    return await operation_service.submit_operation(operation_id=id)
