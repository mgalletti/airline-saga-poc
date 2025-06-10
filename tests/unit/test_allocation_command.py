"""Tests for the AllocateCommand class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from airline_saga.orchestrator.services.commands.allocation_command import AllocateCommand
from airline_saga.orchestrator.services.commands import OrchestratorCommandArgs
from airline_saga.common.models import TransactionResult, TransactionStatus, BookingStep
from airline_saga.common.exceptions import OrchestratorException


@pytest.fixture
def command_args():
    """Create mock command args for testing."""
    args = MagicMock(spec=OrchestratorCommandArgs)
    args.booking = MagicMock()
    args.booking.booking_id = "test-booking-id"
    args.booking.steps = []
    args.flight_number = "FL123"
    args.seat_number = "12A"
    args.passenger_name = "John Doe"
    args.settings = MagicMock()
    args.settings.allocation_service_url = "http://allocation-service"
    args.settings.payment_service_url = "http://payment-service"  # Used in undo method
    return args


class TestAllocateCommand:
    """Tests for the AllocateCommand class."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_execute_success(self, mock_client, command_args):
        """Test successful execution of the allocation command."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "booking_id": "test-booking-id",
            "status": "COMPLETED",
            "message": "Seat allocated successfully",
            "data": {
                "timestamp": "2023-01-01T12:00:00Z",
                "boarding_pass": {"gate": "A1", "boarding_time": "14:30"}
            }
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance
        
        # Execute command
        command = AllocateCommand(command_args)
        await command.execute()
        
        # Verify API call
        mock_client_instance.__aenter__.return_value.post.assert_called_once_with(
            "http://allocation-service/api/allocations/allocate",
            json={
                "booking_id": "test-booking-id",
                "flight_number": "FL123",
                "seat_number": "12A",
                "passenger_name": "John Doe"
            }
        )
        
        # Verify booking step was added
        assert len(command_args.booking.steps) == 1
        step = command_args.booking.steps[0]
        assert step.service == "allocation_service"
        assert step.operation == "allocate_seat"
        assert step.status == TransactionStatus.COMPLETED
        assert step.timestamp == "2023-01-01T12:00:00Z"
        
        # Verify boarding pass was stored
        assert command_args.booking.boarding_pass == {"gate": "A1", "boarding_time": "14:30"}

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_execute_failure(self, mock_client, command_args):
        """Test failed execution of the allocation command."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "success": False,
            "message": "Allocation failed"
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance
        
        # Execute command and expect exception
        command = AllocateCommand(command_args)
        with pytest.raises(OrchestratorException, match="Failed to allocate seat"):
            await command.execute()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_undo_success(self, mock_client, command_args):
        """Test successful undo of the allocation command."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status = "CANCELLED"
        mock_response.data = {"timestamp": "2023-01-01T12:30:00Z"}
        mock_response.json.return_value = {
            "success": True,
            "booking_id": "test-booking-id",
            "status": "CANCELLED",
            "message": "Allocation cancelled successfully",
            "data": {"timestamp": "2023-01-01T12:30:00Z"}
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance
        
        # Execute undo
        command = AllocateCommand(command_args)
        await command.undo()
        
        # Verify API call
        mock_client_instance.__aenter__.return_value.post.assert_called_once_with(
            "http://payment-service/api/allocations/cancel",
            json={"booking_id": "test-booking-id"}
        )
        
        # Verify booking step was added
        assert len(command_args.booking.steps) == 1
        step = command_args.booking.steps[0]
        assert step.service == "allocation_service"
        assert step.operation == "cancel_seat_allocation"
        assert step.status == "CANCELLED"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_undo_exception(self, mock_client, command_args):
        """Test exception handling during undo of the allocation command."""
        # Setup mock to raise exception
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(side_effect=Exception("Network error"))
        mock_client.return_value = mock_client_instance
        
        # Execute undo and expect exception
        command = AllocateCommand(command_args)
        with pytest.raises(Exception, match="Network error"):
            await command.undo()