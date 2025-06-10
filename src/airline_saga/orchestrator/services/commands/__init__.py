from abc import ABC, abstractmethod
from dataclasses import dataclass
from airline_saga.orchestrator.models import PaymentDetails, BookingDetails
from airline_saga.common.config import OrchestratorSettings

class OrchestratorCommand(ABC):
    
    @abstractmethod
    async def execute(self):
        raise NotImplementedError(f"Class {self.__class__.__name__}' must implement method 'execute'")
    
    @abstractmethod
    async def undo(self):
        raise NotImplementedError(f"Class {self.__class__.__name__}' must implement method 'undo'")
    
    
@dataclass(frozen=True)
class OrchestratorCommandArgs:
    booking: BookingDetails
    passenger_name: str
    flight_number: str
    seat_number: str
    payment_details: PaymentDetails
    settings: OrchestratorSettings

