from fastapi import FastAPI
from app.exceptions.handlers.operation_handlers import operation_handler_registry


def handlers_registration(app:FastAPI):
    operation_handler_registry(app)