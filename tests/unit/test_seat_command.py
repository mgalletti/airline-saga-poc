"""Tests for the SeatCommand class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from airline_saga.orchestrator.services.commands.seat_command import SeatCommand
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
    args.settings = MagicMock()
    args.settings.seat_service_url = "http://seat-service"
    return args


class TestSeatCommand:
    """Tests for the SeatCommand class."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_execute_success(self, mock_client, command_args):
        """Test successful execution of the seat command."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "booking_id": "test-booking-id",
            "status": "COMPLETED",
            "message": "Seat blocked successfully",
            "data": {"timestamp": "2023-01-01T12:00:00Z"}
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance
        
        # Execute command
        command = SeatCommand(command_args)
        await command.execute()
        
        # Verify API call
        mock_client_instance.__aenter__.return_value.post.assert_called_once_with(
            "http://seat-service/api/seats/block",
            json={
                "booking_id": "test-booking-id",
                "flight_number": "FL123",
                "seat_number": "12A"
            }
        )
        
        # Verify booking step was added
        assert len(command_args.booking.steps) == 1
        step = command_args.booking.steps[0]
        assert step.service == "seat_service"
        assert step.operation == "block_seat"
        assert step.status == TransactionStatus.COMPLETED
        assert step.timestamp == "2023-01-01T12:00:00Z"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_execute_failure(self, mock_client, command_args):
        """Test failed execution of the seat command."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "success": False,
            "message": "Seat not available"
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance
        
        # Execute command and expect exception
        command = SeatCommand(command_args)
        with pytest.raises(OrchestratorException, match="Failed to block seat"):
            await command.execute()
        
        # Verify booking step was added with FAILED status
        assert len(command_args.booking.steps) == 1
        step = command_args.booking.steps[0]
        assert step.service == "seat_service"
        assert step.operation == "block_seat"
        assert step.status == "FAILED"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_undo_success(self, mock_client, command_args):
        """Test successful undo of the seat command."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "booking_id": "test-booking-id",
            "status": "RELEASED",
            "message": "Seat released successfully",
            "data": {"timestamp": "2023-01-01T12:30:00Z"}
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance
        
        # Execute undo
        command = SeatCommand(command_args)
        await command.undo()
        
        # Verify API call
        mock_client_instance.__aenter__.return_value.post.assert_called_once_with(
            "http://seat-service/api/seats/release",
            json={"booking_id": "test-booking-id"}
        )
        
        # Verify booking step was added
        assert len(command_args.booking.steps) == 1
        step = command_args.booking.steps[0]
        assert step.service == "seat_service"
        assert step.operation == "release_seat"
        assert step.status == "RELEASED"
        assert step.timestamp == "2023-01-01T12:30:00Z"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_undo_exception(self, mock_client, command_args):
        """Test exception handling during undo of the seat command."""
        # Setup mock to raise exception
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(side_effect=Exception("Network error"))
        mock_client.return_value = mock_client_instance
        
        # Execute undo and expect exception
        command = SeatCommand(command_args)
        with pytest.raises(Exception, match="Network error"):
            await command.undo()