from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.exceptions.units.operation_exception import (
    OperationExistingError,
    OperationNotFoundError,
)


def operation_handler_registry(app: FastAPI):

    @app.exception_handler(OperationExistingError)
    def operation_existing_handler(request: Request, exc: OperationExistingError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Operation already exists."},
        )

    @app.exception_handler(OperationNotFoundError)
    def operation_not_found_handler(request: Request, exc: OperationNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Operation not found."},
        )
