from typing import Dict
from enum import Enum
from airline_saga.orchestrator.services.commands import OrchestratorCommand, OrchestratorCommandArgs
from airline_saga.orchestrator.services.commands.allocation_command import AllocateCommand
from airline_saga.orchestrator.services.commands.payment_command import PaymentCommand
from airline_saga.orchestrator.services.commands.seat_command import SeatCommand
from airline_saga.orchestrator import logger


# Enum defining the supported command types in the orchestrator
class OrchestratorCommandType(Enum):
    ALLOCATION = "ALLOCATION"
    PAYMENT = "PAYMENT"      
    SEAT = "SEAT"            


# Registry mapping command types to their implementing classes
ORCHESTRATOR_COMMAND_REGISTRY = {
    OrchestratorCommandType.ALLOCATION: AllocateCommand,
    OrchestratorCommandType.PAYMENT: PaymentCommand,
    OrchestratorCommandType.SEAT: SeatCommand,
}

class OrchestratorCommandFactory:
    """
    Factory class for creating orchestrator command instances.
    Handles command instantiation based on command type.
    """
    
    def __init__(
        self,
        command_args: OrchestratorCommandArgs,
        command_registry: Dict[OrchestratorCommandType, OrchestratorCommand] = ORCHESTRATOR_COMMAND_REGISTRY
    ):
        """
        Initialize the command factory.
        
        Args:
            command_args: Arguments required to instantiate commands
            command_registry: Registry mapping command types to command classes
        """
        self._registry = command_registry
        self._command_args = command_args
        
    def get_command(
        self, 
        command_name: str,
    ) -> OrchestratorCommand:
        """
        Get a command instance based on the command name.
        
        Args:
            command_name: Name of the command to instantiate
            
        Returns:
            An instance of the requested command
            
        Raises:
            ValueError: If command name is invalid or not found in registry
        """
        try:
            command_type = OrchestratorCommandType(command_name)
        except ValueError as e:
            logger.exception(f"Invalid command name: {command_name}. Error: {e}")
            raise ValueError(f"Command '{command_name}' is not supported")
        
        command_class = self._registry.get(command_type, None)
        if not command_class:
            raise ValueError(f"No command found for type: {command_name}")
        
        return command_class(self._command_args)
