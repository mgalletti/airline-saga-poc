"""Exception handlers for the allocation service."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from airline_saga.common.models import TransactionStatus
from airline_saga.common.exceptions import (
    SagaException,
    AllocationFailedException,
    BookingNotFoundException
)


async def saga_exception_handler(_: Request, exc: SagaException):
    """Generic handler for all saga exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "booking_id": exc.booking_id,
            "status": TransactionStatus.FAILED,
            "message": str(exc)
        }
    )


async def allocation_failed_exception_handler(_: Request, exc: AllocationFailedException):
    """Handler for allocation failed exceptions."""
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "booking_id": exc.booking_id,
            "status": TransactionStatus.FAILED,
            "message": str(exc)
        }
    )


async def booking_not_found_exception_handler(_: Request, exc: BookingNotFoundException):
    """Handler for booking not found exceptions."""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "booking_id": exc.booking_id,
            "status": TransactionStatus.FAILED,
            "message": str(exc)
        }
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers for the allocation service."""
    app.add_exception_handler(SagaException, saga_exception_handler)
    app.add_exception_handler(AllocationFailedException, allocation_failed_exception_handler)
    app.add_exception_handler(BookingNotFoundException, booking_not_found_exception_handler)
