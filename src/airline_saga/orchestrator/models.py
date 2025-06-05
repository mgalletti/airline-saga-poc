"""Models specific to the orchestrator service."""

from typing import Dict, Any, List, Optional

from pydantic import BaseModel

from airline_saga.common.models import BookingStatus, BookingStep, PaymentMethodType


class PaymentDetails(BaseModel):
    """Details of a payment for a booking."""
    
    amount: float
    currency: str
    payment_method_type: PaymentMethodType
    payment_metadata: Dict[str, Any]


class StartBookingRequest(BaseModel):
    """Request to start a booking process."""
    
    passenger_name: str
    flight_number: str
    seat_number: str
    payment_details: PaymentDetails


class StartBookingResponse(BaseModel):
    """Response for a booking start request."""
    
    booking_id: str
    status: BookingStatus
    message: str


class BookingDetails(BaseModel):
    """Details of a booking."""
    
    booking_id: str
    status: BookingStatus
    passenger_name: str
    flight_number: str
    seat_number: str
    steps: List[BookingStep]
    boarding_pass: Optional[Dict[str, Any]] = None


class CancellationResponse(BaseModel):
    """Response for a booking cancellation request."""
    
    booking_id: str
    status: BookingStatus
    message: str
    compensation_steps: List[BookingStep]
