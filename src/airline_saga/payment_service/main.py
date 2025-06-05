"""Payment Service API implementation."""

from typing import Dict
import uuid
from fastapi import FastAPI

from airline_saga.common.models import TransactionStatus, TransactionResult, PaymentStatus
from airline_saga.common.config import PaymentServiceSettings
from airline_saga.common.exceptions import (
    PaymentFailedException,
    RefundFailedException,
    BookingNotFoundException
)
from airline_saga.payment_service.models import (
    Payment, ProcessPaymentRequest, RefundPaymentRequest
)
from airline_saga.payment_service.exception_handlers import register_exception_handlers

app: FastAPI = FastAPI(title="Payment Service", description="Service for processing payments")

# Register exception handlers
register_exception_handlers(app)

# In-memory database for simplicity
payments_db: Dict[str, Payment] = {}
payment_by_booking_id: Dict[str, str] = {}  # booking_id -> payment_id


def get_settings() -> PaymentServiceSettings:
    """Get service settings."""
    return PaymentServiceSettings()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/payments/process")
async def process_payment(request: ProcessPaymentRequest):
    """
    Process a payment for a booking.
    
    Args:
        request: The payment request
        
    Returns:
        Transaction result
    """
    booking_id = request.booking_id
    
    # Check if payment already exists for this booking
    if booking_id in payment_by_booking_id:
        existing_payment_id = payment_by_booking_id[booking_id]
        existing_payment = payments_db[existing_payment_id]
        
        # If payment is already completed, return success
        if existing_payment.status == PaymentStatus.COMPLETED:
            return TransactionResult(
                success=True,
                booking_id=booking_id,
                status=TransactionStatus.COMPLETED,
                message="Payment already processed",
                data={
                    "payment_id": existing_payment_id,
                    "amount": existing_payment.amount,
                    "currency": existing_payment.currency
                }
            )
    
    # Generate a payment ID
    payment_id = f"pay_{str(uuid.uuid4())[:8]}"
    
    # Simulate payment processing
    # In a real implementation, this would call a payment gateway
    
    # For demonstration, fail payments with amount > 1000
    if request.amount > 1000:
        raise PaymentFailedException(
            "Payment amount exceeds limit",
            booking_id=booking_id
        )
    
    # Create payment record
    payment = Payment(
        payment_id=payment_id,
        booking_id=booking_id,
        amount=request.amount,
        currency=request.currency,
        payment_method_type=request.payment_method_type,
        payment_metadata=request.payment_metadata,
        status=PaymentStatus.COMPLETED
    )
    
    # Store payment
    payments_db[payment_id] = payment
    payment_by_booking_id[booking_id] = payment_id
    
    return TransactionResult(
        success=True,
        booking_id=booking_id,
        status=TransactionStatus.COMPLETED,
        message="Payment processed successfully",
        data={
            "payment_id": payment_id,
            "amount": request.amount,
            "currency": request.currency
        }
    )


@app.post("/api/payments/refund")
async def refund_payment(request: RefundPaymentRequest):
    """
    Refund a payment for a booking.
    
    Args:
        request: The refund request
        
    Returns:
        Transaction result
    """
    booking_id = request.booking_id
    
    # Check if payment exists for this booking
    if booking_id not in payment_by_booking_id:
        raise BookingNotFoundException(
            f"No payment found for booking {booking_id}",
            booking_id=booking_id
        )
    
    payment_id = payment_by_booking_id[booking_id]
    payment = payments_db[payment_id]
    
    # Check if payment can be refunded
    if payment.status == PaymentStatus.REFUNDED:
        return TransactionResult(
            success=True,
            booking_id=booking_id,
            status=TransactionStatus.REFUNDED,
            message="Payment already refunded",
            data={
                "payment_id": payment_id,
                "refund_id": f"ref_{payment_id[4:]}"  # Use a deterministic refund ID
            }
        )
    
    if payment.status != PaymentStatus.COMPLETED:
        raise RefundFailedException(
            f"Payment {payment_id} cannot be refunded (status: {payment.status})",
            booking_id=booking_id
        )
    
    # Simulate refund processing
    # In a real implementation, this would call a payment gateway
    
    # Update payment status
    payment.status = PaymentStatus.REFUNDED
    payments_db[payment_id] = payment
    
    # Generate a refund ID
    refund_id = f"ref_{payment_id[4:]}"
    
    return TransactionResult(
        success=True,
        booking_id=booking_id,
        status=TransactionStatus.REFUNDED,
        message="Payment refunded successfully",
        data={
            "payment_id": payment_id,
            "refund_id": refund_id
        }
    )


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "airline_saga.payment_service.main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=True
    )
