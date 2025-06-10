"""Exception handlers for the payment service."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from airline_saga.common.models import TransactionStatus
from airline_saga.common.exceptions import (
    SagaException,
    PaymentFailedException,
    RefundFailedException,
    BookingNotFoundException,
)


async def saga_exception_handler(_: Request, exc: SagaException):
    """Generic handler for all saga exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "booking_id": exc.booking_id,
            "status": TransactionStatus.FAILED,
            "message": str(exc),
        },
    )


async def payment_failed_exception_handler(_: Request, exc: PaymentFailedException):
    """Handler for payment failed exceptions."""
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "booking_id": exc.booking_id,
            "status": TransactionStatus.FAILED,
            "message": str(exc),
        },
    )


async def refund_failed_exception_handler(_: Request, exc: RefundFailedException):
    """Handler for refund failed exceptions."""
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "booking_id": exc.booking_id,
            "status": TransactionStatus.FAILED,
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
            "status": TransactionStatus.FAILED,
            "message": str(exc),
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers for the payment service."""
    app.add_exception_handler(SagaException, saga_exception_handler)
    app.add_exception_handler(PaymentFailedException, payment_failed_exception_handler)
    app.add_exception_handler(RefundFailedException, refund_failed_exception_handler)
    app.add_exception_handler(
        BookingNotFoundException, booking_not_found_exception_handler
    )
