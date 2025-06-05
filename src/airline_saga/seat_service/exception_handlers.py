"""Exception handlers for the seat service."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from airline_saga.common.models import TransactionStatus
from airline_saga.common.exceptions import (
    SagaException,
    FlightNotFoundException,
    SeatNotFoundException,
    SeatNotAvailableException
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


async def flight_not_found_exception_handler(_: Request, exc: FlightNotFoundException):
    """Handler for flight not found exceptions."""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "booking_id": exc.booking_id,
            "status": TransactionStatus.FAILED,
            "message": str(exc)
        }
    )


async def seat_not_found_exception_handler(_: Request, exc: SeatNotFoundException):
    """Handler for seat not found exceptions."""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "booking_id": exc.booking_id,
            "status": TransactionStatus.FAILED,
            "message": str(exc)
        }
    )


async def seat_not_available_exception_handler(_: Request, exc: SeatNotAvailableException):
    """Handler for seat not available exceptions."""
    return JSONResponse(
        status_code=409,
        content={
            "success": False,
            "booking_id": exc.booking_id,
            "status": TransactionStatus.FAILED,
            "message": str(exc)
        }
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers for the seat service."""
    app.add_exception_handler(SagaException, saga_exception_handler)
    app.add_exception_handler(FlightNotFoundException, flight_not_found_exception_handler)
    app.add_exception_handler(SeatNotFoundException, seat_not_found_exception_handler)
    app.add_exception_handler(SeatNotAvailableException, seat_not_available_exception_handler)
