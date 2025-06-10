"""Utility functions for the airline saga pattern implementation."""

import uuid
from datetime import datetime
from typing import Dict, Any

from airline_saga.common.models import TransactionStatus, BookingStep


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with an optional prefix."""
    return f"{prefix}_{str(uuid.uuid4())[:8]}" if prefix else str(uuid.uuid4())


def create_booking_step(
    service: str, operation: str, status: TransactionStatus
) -> BookingStep:
    """Create a booking step with the current timestamp."""
    return BookingStep(
        service=service,
        operation=operation,
        status=status,
        timestamp=datetime.utcnow().isoformat(),
    )


def format_error_response(message: str, booking_id: str = None) -> Dict[str, Any]:
    """Format an error response."""
    response = {
        "success": False,
        "message": message,
        "status": TransactionStatus.FAILED,
    }

    if booking_id:
        response["booking_id"] = booking_id

    return response
