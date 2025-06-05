from typing import Dict
from airline_saga.seat_service.models import Flight, SeatStatus, Seat

def init_flights_db() -> Dict[str, Flight]:
    flights_db = {}
    """Initialize the service with some sample data."""
    # Create sample flights
    flights_db["FL001"] = Flight(
        flight_number="FL001",
        seats=[
            Seat(seat_number="1A"),
            Seat(seat_number="1B"),
            Seat(seat_number="1C"),
            Seat(seat_number="2A"),
            Seat(seat_number="2B"),
            Seat(seat_number="2C"),
        ]
    )
    
    flights_db["FL002"] = Flight(
        flight_number="FL002",
        seats=[
            Seat(seat_number="1A"),
            Seat(seat_number="1B"),
            Seat(seat_number="1C"),
            Seat(seat_number="2A"),
            Seat(seat_number="2B"),
            Seat(seat_number="2C"),
        ]
    )
    
    # Set some seats as blocked or booked for demonstration
    flight = flights_db["FL001"]
    flight.seats[1].status = SeatStatus.BLOCKED
    flight.seats[1].booking_id = "demo-booking-1"
    flight.seats[2].status = SeatStatus.BOOKED
    flight.seats[2].booking_id = "demo-booking-2"
    return flights_db