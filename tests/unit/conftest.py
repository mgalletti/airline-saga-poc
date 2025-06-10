"""Common test fixtures for unit tests."""

import pytest
from unittest.mock import MagicMock

from airline_saga.orchestrator.models import BookingDetails, PaymentDetails
from airline_saga.common.models import BookingStatus, PaymentMethodType
from airline_saga.common.config import OrchestratorSettings
from airline_saga.orchestrator.services.commands import OrchestratorCommandArgs


@pytest.fixture
def mock_booking_details():
    """Create a mock BookingDetails instance."""
    return BookingDetails(
        booking_id="test-booking-id",
        status=BookingStatus.PENDING,
        passenger_name="John Doe",
        flight_number="FL123",
        seat_number="12A",
        steps=[]
    )


@pytest.fixture
def mock_payment_details():
    """Create a mock PaymentDetails instance."""
    return PaymentDetails(
        amount=100.0,
        currency="USD",
        payment_method_type=PaymentMethodType.CREDIT_CARD,
        payment_metadata={"card_last4": "1234"}
    )


@pytest.fixture
def mock_settings():
    """Create a mock OrchestratorSettings instance."""
    settings = MagicMock(spec=OrchestratorSettings)
    settings.seat_service_url = "http://seat-service"
    settings.payment_service_url = "http://payment-service"
    settings.allocation_service_url = "http://allocation-service"
    return settings


@pytest.fixture
def command_args(mock_booking_details, mock_payment_details, mock_settings):
    """Create a real OrchestratorCommandArgs instance with mock components."""
    return OrchestratorCommandArgs(
        booking=mock_booking_details,
        passenger_name="John Doe",
        flight_number="FL123",
        seat_number="12A",
        payment_details=mock_payment_details,
        settings=mock_settings
    )