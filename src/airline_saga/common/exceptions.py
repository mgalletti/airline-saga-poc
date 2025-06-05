"""Common exceptions for the airline saga pattern implementation."""


class SagaException(Exception):
    """Base exception for saga pattern errors."""
    
    def __init__(self, message: str, booking_id: str = None):
        self.message = message
        self.booking_id = booking_id
        super().__init__(self.message)


class SeatServiceException(SagaException):
    """Exception raised by the seat service."""
    pass


class PaymentServiceException(SagaException):
    """Exception raised by the payment service."""
    pass


class AllocationServiceException(SagaException):
    """Exception raised by the allocation service."""
    pass


class OrchestratorException(SagaException):
    """Exception raised by the orchestrator."""
    pass


class SeatNotAvailableException(SeatServiceException):
    """Exception raised when a seat is not available."""
    pass


class SeatNotFoundException(SeatServiceException):
    """Exception raised when a seat is not found."""
    pass


class FlightNotFoundException(SeatServiceException):
    """Exception raised when a flight is not found."""
    pass


class PaymentFailedException(PaymentServiceException):
    """Exception raised when a payment fails."""
    pass


class RefundFailedException(PaymentServiceException):
    """Exception raised when a refund fails."""
    pass


class AllocationFailedException(AllocationServiceException):
    """Exception raised when a seat allocation fails."""
    pass


class BookingNotFoundException(OrchestratorException):
    """Exception raised when a booking is not found."""
    pass
