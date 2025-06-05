"""Models specific to the payment service."""

from typing import Dict, Any

from pydantic import BaseModel

from airline_saga.common.models import PaymentMethodType, PaymentStatus


class ProcessPaymentRequest(BaseModel):
    """Request to process a payment."""
    
    booking_id: str
    amount: float
    currency: str
    payment_method_type: PaymentMethodType
    payment_metadata: Dict[str, Any]


class RefundPaymentRequest(BaseModel):
    """Request to refund a payment."""
    
    booking_id: str


class Payment(BaseModel):
    """Model representing a payment."""
    
    payment_id: str
    booking_id: str
    amount: float
    currency: str
    payment_method_type: PaymentMethodType
    payment_metadata: Dict[str, Any]
    status: PaymentStatus
