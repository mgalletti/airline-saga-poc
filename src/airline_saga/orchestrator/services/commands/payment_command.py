import httpx
from airline_saga.common.models import TransactionResult, BookingStep
from airline_saga.common.exceptions import OrchestratorException
from airline_saga.orchestrator.services.commands import OrchestratorCommand, OrchestratorCommandArgs
from airline_saga.orchestrator import logger


class PaymentCommand(OrchestratorCommand):
    """
    Command class for handling payment processing and refunds in the airline booking system.
    Inherits from OrchestratorCommand base class.
    """
    
    def __init__(
        self,
        command_args: OrchestratorCommandArgs,
    ):
        """
        Initialize PaymentCommand with booking and payment details.

        Args:
            command_args (OrchestratorCommandArgs): Command arguments containing:
                - booking: Booking object with booking details
                - flight_number: Flight number for the booking
                - seat_number: Selected seat number
                - payment_details: Payment information including amount, currency etc.
                - settings: Service configuration settings
        """
        super().__init__()
        self.booking = command_args.booking
        self.flight_number = command_args.flight_number
        self.seat_number = command_args.seat_number
        self.payment_details = command_args.payment_details
        self.settings = command_args.settings
        
    
    async def execute(self):
        """
        Execute payment processing for a booking.
        
        Makes HTTP request to payment service to process payment with provided details.
        Updates booking steps with payment status.
        
        Raises:
            OrchestratorException: If payment processing fails
        """
        booking_id = self.booking.booking_id
        async with httpx.AsyncClient() as client:
            logger.info(f"Processing payment for booking {booking_id}")
            
            payment_response = await client.post(
                f"{self.settings.payment_service_url}/api/payments/process",
                json={
                    "booking_id": self.booking.booking_id,
                    "amount": self.payment_details.amount,
                    "currency": self.payment_details.currency,
                    "payment_method_type": self.payment_details.payment_method_type,
                    "payment_metadata": self.payment_details.payment_metadata
                }
            )
            
            if payment_response.status_code != 200:
                logger.error("Payment service failed to process payment")
                error_data = payment_response.json()
                error_msg = error_data.get('message', 'Unknown error')
                
                self.booking.steps.append(
                    BookingStep(
                        service="payment_service",
                        operation="process_payment",
                        status="FAILED",
                        timestamp="",
                        message=error_msg,
                    )
                )
                raise OrchestratorException(
                    f"Failed to process payment: {error_msg}",
                    booking_id=booking_id
                )
            
            payment_result = TransactionResult(**payment_response.json())
            self.booking.steps.append(
                BookingStep(
                    service="payment_service",
                    operation="process_payment",
                    status=payment_result.status,
                    timestamp=payment_result.data.get("timestamp", "")
                )
            )
            logger.info("Payment processed successfully")
        
    
    async def undo(self):
        """
        Compensating transaction to refund a processed payment.
        
        Makes HTTP request to payment service to refund payment for a booking.
        Updates booking steps with refund status.
        
        Raises:
            Exception: If refund processing fails
        """
        booking_id = self.booking.booking_id
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Refunding payment for booking '{booking_id}")
                response = await client.post(
                    f"{self.settings.payment_service_url}/api/payments/refund",
                    json={"booking_id": booking_id}
                )
            
                refund_result = TransactionResult(**response.json())
                logger.info(f"Payment refund transaction result: {refund_result}")
                self.booking.steps.append(
                    BookingStep(
                        service="payment_service",
                        operation="refund_payment",
                        status=response.status,
                        timestamp=response.data.get("timestamp", ""),
                    )
                )
        except Exception as e:
            logger.error(f"Error while refunding payment '{booking_id}': {str(e)}")
            raise

