from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.exceptions.units.operation_exception import (
    OperationExistingError,
    OperationNotFoundError,
    OperationStatusError,
    OperationSubmitConflict,
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

    @app.exception_handler(OperationStatusError)
    def operation_wrong_status_handler(request: Request, exc: OperationStatusError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": {"status:": exc.status, "reason": exc.reason}},
        )

    @app.exception_handler(OperationSubmitConflict)
    def operation_submit_conflict_handler(request: Request, exc: OperationSubmitConflict):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Operation not submitted. CONFLICT."},
        )
