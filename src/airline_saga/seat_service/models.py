"""Models specific to the seat service."""

from typing import Dict, Optional, List

from pydantic import BaseModel

from airline_saga.common.models import SeatStatus


class Seat(BaseModel):
    """Model representing a seat on a flight."""
    
    seat_number: str
    status: SeatStatus = SeatStatus.AVAILABLE
    booking_id: Optional[str] = None
    metadata: Optional[Dict] = None


class Flight(BaseModel):
    """Model representing a flight with its seats."""
    
    flight_number: str
    seats: List[Seat]


class BlockSeatRequest(BaseModel):
    """Request to block a seat."""
    
    booking_id: str
    flight_number: str
    seat_number: str


class ReleaseSeatRequest(BaseModel):
    """Request to release a blocked seat."""
    
    booking_id: str
