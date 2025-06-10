"""Tests for the PaymentCommand class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from airline_saga.orchestrator.services.commands.payment_command import PaymentCommand
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
    args.payment_details = MagicMock()
    args.payment_details.amount = 100.0
    args.payment_details.currency = "USD"
    args.payment_details.payment_method_type = "credit_card"
    args.payment_details.payment_metadata = {"card_last4": "1234"}
    args.settings = MagicMock()
    args.settings.payment_service_url = "http://payment-service"
    return args


class TestPaymentCommand:
    """Tests for the PaymentCommand class."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_execute_success(self, mock_client, command_args):
        """Test successful execution of the payment command."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "booking_id": "test-booking-id",
            "status": "COMPLETED",
            "message": "Payment processed successfully",
            "data": {"timestamp": "2023-01-01T12:00:00Z"}
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance
        
        # Execute command
        command = PaymentCommand(command_args)
        await command.execute()
        
        # Verify API call
        mock_client_instance.__aenter__.return_value.post.assert_called_once_with(
            "http://payment-service/api/payments/process",
            json={
                "booking_id": "test-booking-id",
                "amount": 100.0,
                "currency": "USD",
                "payment_method_type": "credit_card",
                "payment_metadata": {"card_last4": "1234"}
            }
        )
        
        # Verify booking step was added
        assert len(command_args.booking.steps) == 1
        step = command_args.booking.steps[0]
        assert step.service == "payment_service"
        assert step.operation == "process_payment"
        assert step.status == TransactionStatus.COMPLETED
        assert step.timestamp == "2023-01-01T12:00:00Z"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_execute_failure(self, mock_client, command_args):
        """Test failed execution of the payment command."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "success": False,
            "message": "Payment declined"
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance
        
        # Execute command and expect exception
        command = PaymentCommand(command_args)
        with pytest.raises(OrchestratorException, match="Failed to process payment"):
            await command.execute()
        
        # Verify booking step was added with FAILED status
        assert len(command_args.booking.steps) == 1
        step = command_args.booking.steps[0]
        assert step.service == "payment_service"
        assert step.operation == "process_payment"
        assert step.status == "FAILED"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_undo_success(self, mock_client, command_args):
        """Test successful undo of the payment command."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status = "REFUNDED"
        mock_response.data = {"timestamp": "2023-01-01T12:30:00Z"}
        mock_response.json.return_value = {
            "success": True,
            "booking_id": "test-booking-id",
            "status": "REFUNDED",
            "message": "Payment refunded successfully",
            "data": {"timestamp": "2023-01-01T12:30:00Z"}
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance
        
        # Execute undo
        command = PaymentCommand(command_args)
        await command.undo()
        
        # Verify API call
        mock_client_instance.__aenter__.return_value.post.assert_called_once_with(
            "http://payment-service/api/payments/refund",
            json={"booking_id": "test-booking-id"}
        )
        
        # Verify booking step was added
        assert len(command_args.booking.steps) == 1
        step = command_args.booking.steps[0]
        assert step.service == "payment_service"
        assert step.operation == "refund_payment"
        assert step.status == "REFUNDED"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_undo_exception(self, mock_client, command_args):
        """Test exception handling during undo of the payment command."""
        # Setup mock to raise exception
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(side_effect=Exception("Network error"))
        mock_client.return_value = mock_client_instance
        
        # Execute undo and expect exception
        command = PaymentCommand(command_args)
        with pytest.raises(Exception, match="Network error"):
            await command.undo()