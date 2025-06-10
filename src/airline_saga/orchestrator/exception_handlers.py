"""Exception handlers for the orchestrator service."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from airline_saga.common.models import BookingStatus
from airline_saga.common.exceptions import (
    SagaException,
    OrchestratorException,
    BookingNotFoundException,
)


async def saga_exception_handler(_: Request, exc: SagaException):
    """Generic handler for all saga exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "booking_id": exc.booking_id,
            "status": BookingStatus.FAILED,
            "message": str(exc),
        },
    )


async def orchestrator_exception_handler(_: Request, exc: OrchestratorException):
    """Handler for orchestrator exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "booking_id": exc.booking_id,
            "status": BookingStatus.FAILED,
            "message": str(exc),
        },
    )


async def booking_not_found_exception_handler(
    _: Request, exc: BookingNotFoundException
):
    """Handler for booking not found exceptions."""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "booking_id": exc.booking_id,
            "status": BookingStatus.FAILED,
            "message": str(exc),
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers for the orchestrator service."""
    app.add_exception_handler(SagaException, saga_exception_handler)
    app.add_exception_handler(OrchestratorException, orchestrator_exception_handler)
    app.add_exception_handler(
        BookingNotFoundException, booking_not_found_exception_handler
    )
