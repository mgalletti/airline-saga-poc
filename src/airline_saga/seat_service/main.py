"""Seat Service API implementation."""

from typing import Dict, Optional
from fastapi import FastAPI, Query
from contextlib import asynccontextmanager

from airline_saga.common.models import TransactionStatus, TransactionResult
from airline_saga.common.config import SeatServiceSettings
from airline_saga.common.exceptions import (
    FlightNotFoundException,
    SeatNotFoundException,
    SeatNotAvailableException,
)
from airline_saga.seat_service.models import (
    Flight,
    BlockSeatRequest,
    ReleaseSeatRequest,
    SeatStatus,
)
from airline_saga.seat_service.exception_handlers import register_exception_handlers
from airline_saga.seat_service.utils import init_flights_db

# In-memory database for simplicity
# flights_db: Dict[str, Flight] = {}
blocked_seats: Dict[str, Dict] = {}  # booking_id -> {flight_number, seat_number}


@asynccontextmanager
async def setup_teardown_lifespan(app: FastAPI):
    global flights_db
    flights_db = init_flights_db()
    # Track blocked seats
    blocked_seats["demo-booking-1"] = {"flight_number": "FL001", "seat_number": "1B"}

    yield


app = FastAPI(
    title="Seat Service",
    description="Service for managing flight seats",
    lifespan=setup_teardown_lifespan,
)

# Register exception handlers
register_exception_handlers(app)


def get_settings() -> SeatServiceSettings:
    """Get service settings."""
    return SeatServiceSettings()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/flights/{flight_number}")
async def get_flight(
    flight_number: str,
    status: Optional[SeatStatus] = Query(None, description="Filter seats by status"),
):
    """
    Get flight information with optional seat status filtering.

    Args:
        flight_number: The flight number
        status: Optional filter for seat status (available, blocked, booked)

    Returns:
        Flight information with seats
    """
    if flight_number not in flights_db:
        raise FlightNotFoundException(f"Flight {flight_number} not found")

    flight = flights_db[flight_number]

    # If status filter is provided, filter the seats
    if status:
        filtered_seats = [seat for seat in flight.seats if seat.status == status]
        # Return a new Flight object with only the filtered seats
        return Flight(flight_number=flight_number, seats=filtered_seats)

    return flight


@app.get("/api/flights/{flight_number}/seats/{seat_number}")
async def get_seat_of_flight(flight_number: str, seat_number: str):
    """
    Get flight information with optional seat status filtering.

    Args:
        flight_number: The flight number
        status: Optional filter for seat status (available, blocked, booked)

    Returns:
        Flight information with seats
    """
    if flight_number not in flights_db:
        raise FlightNotFoundException(f"Flight {flight_number} not found")

    flight = flights_db[flight_number]

    seat = next((s for s in flight.seats if s.seat_number == seat_number), None)
    if not seat:
        raise SeatNotFoundException(
            f"Seat {seat_number} not found in flight {flight_number}"
        )

    return seat


@app.post("/api/seats/block")
async def block_seat(request: BlockSeatRequest):
    """
    Block a seat for a booking.

    Args:
        request: The block seat request

    Returns:
        Transaction result
    """
    flight_number = request.flight_number
    seat_number = request.seat_number
    booking_id = request.booking_id

    # Validate flight
    if flight_number not in flights_db:
        raise FlightNotFoundException(
            f"Flight {flight_number} not found", booking_id=booking_id
        )

    flight = flights_db[flight_number]

    # Find the seat
    seat = next((s for s in flight.seats if s.seat_number == seat_number), None)
    if not seat:
        raise SeatNotFoundException(
            f"Seat {seat_number} not found on flight {flight_number}",
            booking_id=booking_id,
        )

    # Check if seat is available
    if seat.status != SeatStatus.AVAILABLE:
        raise SeatNotAvailableException(
            f"Seat {seat_number} on flight {flight_number} is not available",
            booking_id=booking_id,
        )

    # Block the seat
    seat.status = SeatStatus.BLOCKED
    seat.booking_id = booking_id

    # Track the blocked seat
    blocked_seats[booking_id] = {
        "flight_number": flight_number,
        "seat_number": seat_number,
    }

    return TransactionResult(
        success=True,
        booking_id=booking_id,
        status=TransactionStatus.COMPLETED,
        message=f"Seat {seat_number} on flight {flight_number} blocked successfully",
        data={"flight_number": flight_number, "seat_number": seat_number},
    )


@app.post("/api/seats/release")
async def release_seat(request: ReleaseSeatRequest):
    """
    Release a blocked seat.

    Args:
        request: The release seat request

    Returns:
        Transaction result
    """
    booking_id = request.booking_id

    # Check if the booking has a blocked seat
    if booking_id not in blocked_seats:
        raise SeatNotFoundException(
            f"No blocked seat found for booking {booking_id}", booking_id=booking_id
        )

    # Get the flight and seat
    flight_number = blocked_seats[booking_id]["flight_number"]
    seat_number = blocked_seats[booking_id]["seat_number"]

    flight = flights_db[flight_number]
    seat = next((s for s in flight.seats if s.seat_number == seat_number), None)

    if not seat:
        raise SeatNotFoundException(
            f"Seat {seat_number} not found on flight {flight_number}",
            booking_id=booking_id,
        )

    # Release the seat
    seat.status = SeatStatus.AVAILABLE
    seat.booking_id = None

    # Remove from blocked seats
    del blocked_seats[booking_id]

    return TransactionResult(
        success=True,
        booking_id=booking_id,
        status=TransactionStatus.RELEASED,
        message=f"Seat {seat_number} on flight {flight_number} released successfully",
        data={"flight_number": flight_number, "seat_number": seat_number},
    )


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "airline_saga.seat_service.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
