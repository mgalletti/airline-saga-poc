"""Models specific to the allocation service."""

from typing import Optional
import enum

from pydantic import BaseModel


class AllocationStatus(str, enum.Enum):
    """Status of a seat allocation."""

    PENDING = "PENDING"
    ALLOCATED = "ALLOCATED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class AllocateSeatRequest(BaseModel):
    """Request to allocate a seat."""

    booking_id: str
    flight_number: str
    seat_number: str
    passenger_name: str


class CancelAllocationRequest(BaseModel):
    """Request to cancel a seat allocation."""

    booking_id: str


class BoardingPass(BaseModel):
    """Model representing a boarding pass."""

    passenger: str
    flight: str
    seat: str
    gate: str
    boarding_time: str


class Allocation(BaseModel):
    """Model representing a seat allocation."""

    allocation_id: str
    booking_id: str
    flight_number: str
    seat_number: str
    passenger_name: str
    status: AllocationStatus
    boarding_pass: Optional[BoardingPass] = None
