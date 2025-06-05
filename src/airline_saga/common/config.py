"""Configuration settings for the airline saga pattern implementation."""

from pydantic_settings import BaseSettings


class ServiceSettings(BaseSettings):
    """Base settings for all services."""
    
    # Service identification
    service_name: str
    
    # API settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Service URLs
    seat_service_url: str = "http://localhost:8001"
    payment_service_url: str = "http://localhost:8002"
    allocation_service_url: str = "http://localhost:8003"
    orchestrator_url: str = "http://localhost:8000"
    
    class Config:
        """Pydantic configuration."""
        
        env_file = ".env"
        env_file_encoding = "utf-8"


class SeatServiceSettings(ServiceSettings):
    """Settings for the seat service."""
    
    service_name: str = "seat_service"
    port: int = 8001


class PaymentServiceSettings(ServiceSettings):
    """Settings for the payment service."""
    
    service_name: str = "payment_service"
    port: int = 8002


class AllocationServiceSettings(ServiceSettings):
    """Settings for the allocation service."""
    
    service_name: str = "allocation_service"
    port: int = 8003


class OrchestratorSettings(ServiceSettings):
    """Settings for the orchestrator."""
    
    service_name: str = "orchestrator"
    port: int = 8000
