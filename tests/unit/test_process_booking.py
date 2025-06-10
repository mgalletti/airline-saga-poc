"""Tests for the process_booking function."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from airline_saga.orchestrator.main import process_booking
from airline_saga.common.models import BookingStatus
from airline_saga.common.exceptions import OrchestratorException
from airline_saga.orchestrator.models import BookingDetails, PaymentDetails
from airline_saga.common.config import OrchestratorSettings

@pytest.fixture
def mock_booking():
    """Create a mock booking."""
    booking = MagicMock(spec=BookingDetails)
    booking.booking_id = "test-booking-id"
    booking.status = BookingStatus.PENDING
    booking.steps = []
    return booking


@pytest.fixture
def mock_payment_details():
    """Create mock payment details."""
    payment_details = MagicMock(spec=PaymentDetails)
    payment_details.amount = 100.0
    payment_details.currency = "USD"
    payment_details.payment_method_type = "credit_card"
    payment_details.payment_metadata = {"card_last4": "1234"}
    return payment_details


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock(spec=OrchestratorSettings)
    settings.commands = ["SEAT", "PAYMENT", "ALLOCATION"]
    return settings


@pytest.fixture
def mock_command_factory():
    """Create a mock command factory."""
    factory = MagicMock()
    return factory


@pytest.fixture
def mock_commands():
    """Create mock commands."""
    seat_command = MagicMock()
    seat_command.execute = AsyncMock()
    seat_command.undo = AsyncMock()
    
    payment_command = MagicMock()
    payment_command.execute = AsyncMock()
    payment_command.undo = AsyncMock()
    
    allocation_command = MagicMock()
    allocation_command.execute = AsyncMock()
    allocation_command.undo = AsyncMock()
    
    return {
        "SEAT": seat_command,
        "PAYMENT": payment_command,
        "ALLOCATION": allocation_command
    }


class TestProcessBooking:
    """Tests for the process_booking function."""
    
    @pytest.mark.asyncio
    @patch("airline_saga.orchestrator.main.bookings_db")
    @patch("airline_saga.orchestrator.main.get_settings")
    @patch("airline_saga.orchestrator.main.OrchestratorCommandFactory")
    async def test_process_booking_success(
        self, 
        mock_factory_class, 
        mock_get_settings, 
        mock_bookings_db,
        mock_booking, 
        mock_payment_details, 
        mock_settings,
        mock_commands
    ):
        """Test successful booking process."""
        # Setup mocks
        mock_bookings_db.__getitem__.return_value = mock_booking
        mock_get_settings.return_value = mock_settings
        
        mock_factory = MagicMock()
        mock_factory_class.return_value = mock_factory
        
        # Setup command factory to return our mock commands
        def get_command_side_effect(command_name):
            return mock_commands[command_name]
        
        mock_factory.get_command.side_effect = get_command_side_effect
        
        # Execute the function
        await process_booking(
            booking_id="test-booking-id",
            passenger_name="John Doe",
            flight_number="FL123",
            seat_number="12A",
            payment_details=mock_payment_details
        )
        
        # Verify all commands were executed in order
        mock_commands["SEAT"].execute.assert_called_once()
        mock_commands["PAYMENT"].execute.assert_called_once()
        mock_commands["ALLOCATION"].execute.assert_called_once()
        
        # Verify no undo operations were called
        mock_commands["SEAT"].undo.assert_not_called()
        mock_commands["PAYMENT"].undo.assert_not_called()
        mock_commands["ALLOCATION"].undo.assert_not_called()
        
        # Verify booking status was updated to COMPLETED
        assert mock_booking.status == BookingStatus.COMPLETED
        mock_bookings_db.__setitem__.assert_called_with("test-booking-id", mock_booking)

    @pytest.mark.asyncio
    @patch("airline_saga.orchestrator.main.bookings_db")
    @patch("airline_saga.orchestrator.main.get_settings")
    @patch("airline_saga.orchestrator.main.OrchestratorCommandFactory")
    async def test_process_booking_failure_with_compensation(
        self, 
        mock_factory_class, 
        mock_get_settings, 
        mock_bookings_db,
        mock_booking, 
        mock_payment_details, 
        mock_settings,
        mock_commands
    ):
        """Test booking process with failure and compensation."""
        # Setup mocks
        mock_bookings_db.__getitem__.return_value = mock_booking
        mock_get_settings.return_value = mock_settings
        
        mock_factory = MagicMock()
        mock_factory_class.return_value = mock_factory
        
        # Make the payment command fail
        mock_commands["PAYMENT"].execute.side_effect = OrchestratorException("Payment failed")
        
        # Setup command factory to return our mock commands
        def get_command_side_effect(command_name):
            return mock_commands[command_name]
        
        mock_factory.get_command.side_effect = get_command_side_effect
        
        # Execute the function
        await process_booking(
            booking_id="test-booking-id",
            passenger_name="John Doe",
            flight_number="FL123",
            seat_number="12A",
            payment_details=mock_payment_details
        )
        
        # Verify execution order
        mock_commands["SEAT"].execute.assert_called_once()
        mock_commands["PAYMENT"].execute.assert_called_once()
        mock_commands["ALLOCATION"].execute.assert_not_called()
        
        # Verify compensation was triggered for the SEAT command
        mock_commands["SEAT"].undo.assert_called_once()
        
        # Verify booking status was updated to FAILED
        assert mock_booking.status == BookingStatus.FAILED
        mock_bookings_db.__setitem__.assert_called_with("test-booking-id", mock_booking)

    @pytest.mark.asyncio
    @patch("airline_saga.orchestrator.main.bookings_db")
    @patch("airline_saga.orchestrator.main.get_settings")
    @patch("airline_saga.orchestrator.main.OrchestratorCommandFactory")
    async def test_process_booking_unexpected_exception(
        self, 
        mock_factory_class, 
        mock_get_settings, 
        mock_bookings_db,
        mock_booking, 
        mock_payment_details, 
        mock_settings
    ):
        """Test booking process with an unexpected exception."""
        # Setup mocks
        mock_bookings_db.__getitem__.return_value = mock_booking
        mock_get_settings.return_value = mock_settings
        
        mock_factory = MagicMock()
        mock_factory_class.return_value = mock_factory
        
        # Make the factory throw an unexpected exception
        mock_factory.get_command.side_effect = Exception("Unexpected error")
        
        # Execute the function
        await process_booking(
            booking_id="test-booking-id",
            passenger_name="John Doe",
            flight_number="FL123",
            seat_number="12A",
            payment_details=mock_payment_details
        )
        
        # Verify booking status was updated to FAILED
        assert mock_booking.status == BookingStatus.FAILED
        mock_bookings_db.__setitem__.assert_called_with("test-booking-id", mock_booking)