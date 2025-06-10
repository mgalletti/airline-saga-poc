"""Data models for the airline booking saga pattern."""

import enum
import uuid
from typing import Dict, Optional, Any, List

from pydantic import BaseModel, Field


class TransactionStatus(str, enum.Enum):
    """Status of a transaction in the saga pattern."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class TransactionResult(BaseModel):
    """Result of a transaction in the saga pattern."""

    success: bool
    booking_id: str
    status: TransactionStatus
    message: str = ""
    data: Optional[Dict[str, Any]] = None


class SeatStatus(str, enum.Enum):
    """Status of a seat in the airline booking system."""

    AVAILABLE = "available"
    BLOCKED = "blocked"
    BOOKED = "booked"


class PaymentMethodType(str, enum.Enum):
    """Types of payment methods."""

    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    CRYPTO = "crypto"


class PaymentStatus(str, enum.Enum):
    """Status of a payment transaction."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class BookingStatus(str, enum.Enum):
    """Status of a booking in the system."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class BookingStep(BaseModel):
    """A step in the booking process."""

    service: str
    operation: str
    status: TransactionStatus
    timestamp: str
    message: Optional[str] = None


class BookingRequest(BaseModel):
    """Request model for starting a booking process."""

    passenger_name: str
    flight_number: str
    seat_number: str
    payment_details: Dict[str, Any]
    booking_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class BookingResponse(BaseModel):
    """Response model for a booking request."""

    booking_id: str
    status: BookingStatus
    message: str


class BookingStatusResponse(BaseModel):
    """Response model for a booking status request."""

    booking_id: str
    status: BookingStatus
    passenger_name: str
    flight_number: str
    seat_number: str
    steps: List[BookingStep]
    boarding_pass: Optional[Dict[str, Any]] = None


class BookingCancellationResponse(BaseModel):
    """Response model for a booking cancellation request."""

    booking_id: str
    status: BookingStatus
    message: str
    compensation_steps: List[BookingStep]
