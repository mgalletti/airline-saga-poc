"""Orchestrator Service API implementation."""

from typing import Dict
from httpx import Response

import uuid
import httpx
from fastapi import FastAPI, BackgroundTasks

from airline_saga.common.models import (
    BookingStatus, BookingStep, TransactionResult
)
from airline_saga.common.config import OrchestratorSettings
from airline_saga.common.exceptions import (
    OrchestratorException,
    BookingNotFoundException
)
from airline_saga.orchestrator.models import (
    StartBookingRequest, StartBookingResponse, BookingDetails, CancellationResponse
)
from airline_saga.orchestrator.exception_handlers import register_exception_handlers
from airline_saga.common.logger import setup_request_logging, config_logger

SERVICE_NAME = "Orchestrator Service"

app: FastAPI = FastAPI(title=SERVICE_NAME, description="Service for orchestrating the booking saga")
logger = config_logger(service_name=SERVICE_NAME)

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
async def start_booking(request: StartBookingRequest, background_tasks: BackgroundTasks):
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
        steps=[]
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
        payment_details=request.payment_details
    )
    
    return StartBookingResponse(
        booking_id=booking_id,
        status=BookingStatus.PENDING,
        message="Booking process started"
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
            f"Booking {booking_id} not found",
            booking_id=booking_id
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
            f"Booking {booking_id} not found",
            booking_id=booking_id
        )
    
    booking = bookings_db[booking_id]
    
    # Check if booking can be cancelled
    if booking.status == BookingStatus.CANCELLED:
        return CancellationResponse(
            booking_id=booking_id,
            status=BookingStatus.CANCELLED,
            message="Booking already cancelled",
            compensation_steps=booking.steps
        )
    
    # Update booking status
    booking.status = BookingStatus.CANCELLED
    bookings_db[booking_id] = booking
    
    # Start the cancellation process in the background
    background_tasks.add_task(
        cancel_booking_process,
        booking_id=booking_id
    )
    
    return CancellationResponse(
        booking_id=booking_id,
        status=BookingStatus.CANCELLED,
        message="Booking cancellation started",
        compensation_steps=[]
    )


async def process_booking(
    booking_id: str,
    passenger_name: str,
    flight_number: str,
    seat_number: str,
    payment_details: dict
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
    
    try:
        # Step 1: Block seat
        async with httpx.AsyncClient() as client:
            block_response = await client.post(
                f"{settings.seat_service_url}/api/seats/block",
                json={
                    "booking_id": booking_id,
                    "flight_number": flight_number,
                    "seat_number": seat_number
                }
            )
            
            if block_response.status_code != 200:
                error_data = block_response.json()
                raise OrchestratorException(
                    f"Failed to block seat: {error_data.get('message', 'Unknown error')}",
                    booking_id=booking_id
                )
            
            block_result = TransactionResult(**block_response.json())
            booking.steps.append(
                BookingStep(
                    service="seat_service",
                    operation="block_seat",
                    status=block_result.status,
                    timestamp=block_result.data.get("timestamp", "")
                )
            )
        
        # Step 2: Process payment
        async with httpx.AsyncClient() as client:
            logger.info(f"Processing payment for booking {booking_id}")
            
            payment_response = await client.post(
                f"{settings.payment_service_url}/api/payments/process",
                json={
                    "booking_id": booking_id,
                    "amount": payment_details.amount,
                    "currency": payment_details.currency,
                    "payment_method_type": payment_details.payment_method_type,
                    "payment_metadata": payment_details.payment_metadata
                }
            )
            
            if payment_response.status_code != 200:
                logger.error("Payment service failed to process payment")
                error_data = payment_response.json()
                error_msg = error_data.get('message', 'Unknown error')
                
                booking.steps.append(
                    BookingStep(
                        service="payment_service",
                        operation="process_payment",
                        status="FAILED",
                        timestamp="",
                        message=error_msg,
                    )
                )
                # Payment failed, compensate by releasing the seat
                release_seat_response = await compensate_seat_blocking(booking_id, settings)
                release_seat_result = TransactionResult(**release_seat_response.json())
                logger.info(f"Release seat transaction result: {release_seat_result}")
                booking.steps.append(
                    BookingStep(
                        service="seat_service",
                        operation="release_seat",
                        status=release_seat_result.status,
                        timestamp=release_seat_result.data.get("timestamp", ""),
                    )
                )
                
                raise OrchestratorException(
                    f"Failed to process payment: {error_msg}",
                    booking_id=booking_id
                )
            
            payment_result = TransactionResult(**payment_response.json())
            booking.steps.append(
                BookingStep(
                    service="payment_service",
                    operation="process_payment",
                    status=payment_result.status,
                    timestamp=payment_result.data.get("timestamp", "")
                )
            )
            logger.info("Payment processed successfully")
        
        # Step 3: Allocate seat
        async with httpx.AsyncClient() as client:
            allocation_response = await client.post(
                f"{settings.allocation_service_url}/api/allocations/allocate",
                json={
                    "booking_id": booking_id,
                    "flight_number": flight_number,
                    "seat_number": seat_number,
                    "passenger_name": passenger_name
                }
            )
            
            if allocation_response.status_code != 200:
                # Allocation failed, compensate by refunding payment and releasing seat
                await compensate_payment_processing(booking_id, settings)
                await compensate_seat_blocking(booking_id, settings)
                
                error_data = allocation_response.json()
                raise OrchestratorException(
                    f"Failed to allocate seat: {error_data.get('message', 'Unknown error')}",
                    booking_id=booking_id
                )
            
            allocation_result = TransactionResult(**allocation_response.json())
            booking.steps.append(
                BookingStep(
                    service="allocation_service",
                    operation="allocate_seat",
                    status=allocation_result.status,
                    timestamp=allocation_result.data.get("timestamp", "")
                )
            )
            
            # Store boarding pass
            if allocation_result.data and "boarding_pass" in allocation_result.data:
                booking.boarding_pass = allocation_result.data["boarding_pass"]
        
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
                json={"booking_id": booking_id}
            )
            
            if allocation_response.status_code == 200:
                result = TransactionResult(**allocation_response.json())
                compensation_steps.append(
                    BookingStep(
                        service="allocation_service",
                        operation="cancel_allocation",
                        status=result.status,
                        timestamp=result.data.get("timestamp", "")
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
                json={"booking_id": booking_id}
            )
            
            if payment_response.status_code == 200:
                result = TransactionResult(**payment_response.json())
                compensation_steps.append(
                    BookingStep(
                        service="payment_service",
                        operation="refund_payment",
                        status=result.status,
                        timestamp=result.data.get("timestamp", "")
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
                json={"booking_id": booking_id}
            )
            
            if seat_response.status_code == 200:
                result = TransactionResult(**seat_response.json())
                compensation_steps.append(
                    BookingStep(
                        service="seat_service",
                        operation="release_seat",
                        status=result.status,
                        timestamp=result.data.get("timestamp", "")
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
                json={"booking_id": booking_id}
            )
            return response
    except Exception as e:
        logger.error(f"Error while releasing the seat: {str(e)}")
        raise


async def compensate_payment_processing(booking_id: str, settings: OrchestratorSettings):
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
                json={"booking_id": booking_id}
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
        reload=True
    )
