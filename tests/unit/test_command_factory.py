"""Tests for the OrchestratorCommandFactory class."""

import pytest
from unittest.mock import MagicMock

from airline_saga.orchestrator.services.commands import OrchestratorCommandArgs
from airline_saga.orchestrator.services.commands.command_factory import (
    OrchestratorCommandFactory,
    OrchestratorCommandType,
)
from airline_saga.orchestrator.models import BookingDetails, PaymentDetails
from airline_saga.orchestrator.services.commands.seat_command import SeatCommand
from airline_saga.orchestrator.services.commands.payment_command import PaymentCommand
from airline_saga.orchestrator.services.commands.allocation_command import (
    AllocateCommand,
)
from airline_saga.common.config import OrchestratorSettings


@pytest.fixture
def command_args():
    """Create mock command args for testing."""
    # return MagicMock(spec=OrchestratorCommandArgs)
    return OrchestratorCommandArgs(
        MagicMock(spec=BookingDetails),
        passenger_name="bob",
        flight_number="A123",
        seat_number="1A",
        payment_details=MagicMock(spec=PaymentDetails),
        settings=OrchestratorSettings(),
    )


class TestOrchestratorCommandFactory:
    """Tests for the OrchestratorCommandFactory class."""

    def test_get_seat_command(self, command_args):
        """Test getting a seat command."""
        factory = OrchestratorCommandFactory(command_args)
        command = factory.get_command("SEAT")
        assert isinstance(command, SeatCommand)

    def test_get_payment_command(self, command_args):
        """Test getting a payment command."""
        factory = OrchestratorCommandFactory(command_args)
        command = factory.get_command("PAYMENT")
        assert isinstance(command, PaymentCommand)

    def test_get_allocation_command(self, command_args):
        """Test getting an allocation command."""
        factory = OrchestratorCommandFactory(command_args)
        command = factory.get_command("ALLOCATION")
        assert isinstance(command, AllocateCommand)

    def test_get_invalid_command(self, command_args):
        """Test getting an invalid command."""
        factory = OrchestratorCommandFactory(command_args)
        with pytest.raises(ValueError, match="Command 'INVALID' is not supported"):
            factory.get_command("INVALID")

    def test_custom_registry(self, command_args):
        """Test using a custom command registry."""
        mock_command = MagicMock()
        custom_registry = {OrchestratorCommandType.SEAT: mock_command}

        factory = OrchestratorCommandFactory(command_args, custom_registry)
        command = factory.get_command("SEAT")

        assert command == mock_command.return_value
        mock_command.assert_called_once_with(command_args)
