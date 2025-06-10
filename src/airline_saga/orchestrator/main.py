"""Orchestrator Service API implementation."""

from typing import Dict, List
from httpx import Response

import uuid
import httpx
from fastapi import FastAPI, BackgroundTasks

from airline_saga.common.models import BookingStatus, BookingStep, TransactionResult
from airline_saga.common.config import OrchestratorSettings
from airline_saga.orchestrator.models import PaymentDetails
from airline_saga.common.exceptions import (
    OrchestratorException,
    BookingNotFoundException,
)
from airline_saga.orchestrator.models import (
    StartBookingRequest,
    StartBookingResponse,
    BookingDetails,
    CancellationResponse,
)
from airline_saga.orchestrator.exception_handlers import register_exception_handlers
from airline_saga.orchestrator.services.commands import (
    OrchestratorCommand,
    OrchestratorCommandArgs,
)
from airline_saga.orchestrator.services.commands.command_factory import (
    OrchestratorCommandFactory,
)
from airline_saga.common.logger import setup_request_logging
from airline_saga.orchestrator import logger, SERVICE_NAME

app: FastAPI = FastAPI(
    title=SERVICE_NAME, description="Service for orchestrating the booking saga"
)

setup_request_logging(app, logger)

# Register exception handlers
register_exception_handlers(app)

# In-memory database for simplicity
bookings_db: Dict[str, BookingDetails] = {}


def get_settings() -> OrchestratorSettings:
    """Get service settings."""
    return OrchestratorSettings()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/bookings/start", response_model=StartBookingResponse)
async def start_booking(
    request: StartBookingRequest, background_tasks: BackgroundTasks
):
    """
    Start a new booking process.

    Args:
        request: The booking request
        background_tasks: FastAPI background tasks

    Returns:
        Booking response with booking ID
    """
    # Generate a booking ID
    booking_id = str(uuid.uuid4())

    # Create initial booking record
    booking = BookingDetails(
        booking_id=booking_id,
        status=BookingStatus.PENDING,
        passenger_name=request.passenger_name,
        flight_number=request.flight_number,
        seat_number=request.seat_number,
        steps=[],
    )

    # Store booking
    bookings_db[booking_id] = booking

    # Start the booking process in the background
    background_tasks.add_task(
        process_booking,
        booking_id=booking_id,
        passenger_name=request.passenger_name,
        flight_number=request.flight_number,
        seat_number=request.seat_number,
        payment_details=request.payment_details,
    )

    return StartBookingResponse(
        booking_id=booking_id,
        status=BookingStatus.PENDING,
        message="Booking process started",
    )


@app.get("/api/bookings", response_model=Dict[str, BookingDetails])
async def get_all_booking():
    """
    Get booking details.

    Args:
        booking_id: The booking ID

    Returns:
        Booking details
    """
    return bookings_db


@app.get("/api/bookings/{booking_id}", response_model=BookingDetails)
async def get_booking(booking_id: str):
    """
    Get booking details.

    Args:
        booking_id: The booking ID

    Returns:
        Booking details
    """
    if booking_id not in bookings_db:
        raise BookingNotFoundException(
            f"Booking {booking_id} not found", booking_id=booking_id
        )

    return bookings_db[booking_id]


@app.post("/api/bookings/{booking_id}/cancel", response_model=CancellationResponse)
async def cancel_booking(booking_id: str, background_tasks: BackgroundTasks):
    """
    Cancel a booking.

    Args:
        booking_id: The booking ID
        background_tasks: FastAPI background tasks

    Returns:
        Cancellation response
    """
    if booking_id not in bookings_db:
        raise BookingNotFoundException(
            f"Booking {booking_id} not found", booking_id=booking_id
        )

    booking = bookings_db[booking_id]

    # Check if booking can be cancelled
    if booking.status == BookingStatus.CANCELLED:
        return CancellationResponse(
            booking_id=booking_id,
            status=BookingStatus.CANCELLED,
            message="Booking already cancelled",
            compensation_steps=booking.steps,
        )

    # Update booking status
    booking.status = BookingStatus.CANCELLED
    bookings_db[booking_id] = booking

    # Start the cancellation process in the background
    background_tasks.add_task(cancel_booking_process, booking_id=booking_id)

    return CancellationResponse(
        booking_id=booking_id,
        status=BookingStatus.CANCELLED,
        message="Booking cancellation started",
        compensation_steps=[],
    )


async def process_booking(
    booking_id: str,
    passenger_name: str,
    flight_number: str,
    seat_number: str,
    payment_details: PaymentDetails,
):
    """
    Process a booking using the saga pattern.

    Args:
        booking_id: The booking ID
        passenger_name: The passenger name
        flight_number: The flight number
        seat_number: The seat number
        payment_details: The payment details
    """
    settings = get_settings()
    booking = bookings_db[booking_id]
    command_factory = OrchestratorCommandFactory(
        OrchestratorCommandArgs(
            booking=booking,
            passenger_name=passenger_name,
            flight_number=flight_number,
            seat_number=seat_number,
            payment_details=payment_details,
            settings=settings,
        )
    )

    try:
        to_do = [command_factory.get_command(command) for command in settings.commands]
        to_revert: List[OrchestratorCommand] = []

        # Dequeues commands to be executed sequentially and revert the executions if something fails.
        # Workflow is pretty dumb as it doesn't support conditional branching, parallelization, loops, etc.
        # After all, is a POC..
        while to_do:
            command = to_do.pop(0)
            try:
                await command.execute()
                to_revert.append(command)
            except OrchestratorException:
                to_do.insert(0, command)
                while to_revert:
                    revert_command = to_revert.pop()
                    await revert_command.undo()
                    to_do.insert(0, command)
                raise

        # All steps completed successfully
        booking.status = BookingStatus.COMPLETED
        bookings_db[booking_id] = booking

    except Exception as e:
        logger.error(f"Something went wrong: {str(e)}")
        # Handle any unexpected errors
        booking.status = BookingStatus.FAILED
        bookings_db[booking_id] = booking
        # In a real implementation, we would log the error and possibly notify an admin


async def cancel_booking_process(booking_id: str):
    """
    Cancel a booking using compensating transactions.

    Args:
        booking_id: The booking ID
    """
    settings = get_settings()
    booking = bookings_db[booking_id]
    compensation_steps = []

    # Step 1: Cancel allocation
    try:
        async with httpx.AsyncClient() as client:
            allocation_response = await client.post(
                f"{settings.allocation_service_url}/api/allocations/cancel",
                json={"booking_id": booking_id},
            )

            if allocation_response.status_code == 200:
                result = TransactionResult(**allocation_response.json())
                compensation_steps.append(
                    BookingStep(
                        service="allocation_service",
                        operation="cancel_allocation",
                        status=result.status,
                        timestamp=result.data.get("timestamp", ""),
                    )
                )
    except Exception:
        # Continue with other compensating transactions even if this one fails
        pass

    # Step 2: Refund payment
    try:
        async with httpx.AsyncClient() as client:
            payment_response = await client.post(
                f"{settings.payment_service_url}/api/payments/refund",
                json={"booking_id": booking_id},
            )

            if payment_response.status_code == 200:
                result = TransactionResult(**payment_response.json())
                compensation_steps.append(
                    BookingStep(
                        service="payment_service",
                        operation="refund_payment",
                        status=result.status,
                        timestamp=result.data.get("timestamp", ""),
                    )
                )
    except Exception:
        # Continue with other compensating transactions even if this one fails
        pass

    # Step 3: Release seat
    try:
        async with httpx.AsyncClient() as client:
            seat_response = await client.post(
                f"{settings.seat_service_url}/api/seats/release",
                json={"booking_id": booking_id},
            )

            if seat_response.status_code == 200:
                result = TransactionResult(**seat_response.json())
                compensation_steps.append(
                    BookingStep(
                        service="seat_service",
                        operation="release_seat",
                        status=result.status,
                        timestamp=result.data.get("timestamp", ""),
                    )
                )
    except Exception:
        # Continue even if this one fails
        pass

    # Update booking with compensation steps
    booking.steps.extend(compensation_steps)
    bookings_db[booking_id] = booking


async def compensate_seat_blocking(
    booking_id: str, settings: OrchestratorSettings
) -> Response:
    """
    Compensating transaction for seat blocking.

    Args:
        booking_id: The booking ID
        settings: The service settings
    """
    logger.info(f"Releasing the seat for booking: {booking_id}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.seat_service_url}/api/seats/release",
                json={"booking_id": booking_id},
            )
            return response
    except Exception as e:
        logger.error(f"Error while releasing the seat: {str(e)}")
        raise


async def compensate_payment_processing(
    booking_id: str, settings: OrchestratorSettings
):
    """
    Compensating transaction for payment processing.

    Args:
        booking_id: The booking ID
        settings: The service settings
    """
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.payment_service_url}/api/payments/refund",
                json={"booking_id": booking_id},
            )
    except Exception:
        # Log the error but continue
        pass


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "airline_saga.orchestrator.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
