import httpx
from airline_saga.common.models import TransactionResult, BookingStep
from airline_saga.common.exceptions import OrchestratorException
from airline_saga.orchestrator.services.commands import (
    OrchestratorCommand,
    OrchestratorCommandArgs,
)
from airline_saga.orchestrator import logger


class AllocateCommand(OrchestratorCommand):
    """Command to allocate a seat for a booking.

    This command handles seat allocation by making requests to the allocation service.
    It can allocate a seat for a booking and undo the allocation if needed.
    """

    def __init__(
        self,
        command_args: OrchestratorCommandArgs,
    ):
        """Initialize the AllocateCommand.

        Args:
            command_args (OrchestratorCommandArgs): Command arguments containing:
                - booking: The booking object
                - flight_number: Flight number for the allocation
                - seat_number: Seat number to allocate
                - passenger_name: Name of the passenger
                - settings: Application settings
        """
        super().__init__()
        self.booking = command_args.booking
        self.flight_number = command_args.flight_number
        self.seat_number = command_args.seat_number
        self.passenger_name = command_args.passenger_name
        self.settings = command_args.settings

    async def execute(self):
        """Execute the seat allocation.

        Makes a POST request to the allocation service to allocate a seat.
        Updates the booking with allocation details and boarding pass.

        Raises:
            OrchestratorException: If the allocation service fails to process the request
        """
        booking_id = self.booking.booking_id
        async with httpx.AsyncClient() as client:
            logger.info(f"Allocating seat for booking '{booking_id}'")
            allocation_response = await client.post(
                f"{self.settings.allocation_service_url}/api/allocations/allocate",
                json={
                    "booking_id": booking_id,
                    "flight_number": self.flight_number,
                    "seat_number": self.seat_number,
                    "passenger_name": self.passenger_name,
                },
            )
            if allocation_response.status_code != 200:
                error_data = allocation_response.json()
                logger.error(
                    f"Allocation service failed to process allocation: {error_data}"
                )
                raise OrchestratorException(
                    f"Failed to allocate seat: {error_data.get('message', 'Unknown error')}",
                    booking_id=booking_id,
                )

            allocation_result = TransactionResult(**allocation_response.json())
            self.booking.steps.append(
                BookingStep(
                    service="allocation_service",
                    operation="allocate_seat",
                    status=allocation_result.status,
                    timestamp=allocation_result.data.get("timestamp", ""),
                )
            )
            # Store boarding pass
            if allocation_result.data and "boarding_pass" in allocation_result.data:
                self.booking.boarding_pass = allocation_result.data["boarding_pass"]
            logger.info(f"Seat allocated successfully for booking '{booking_id}'")

    async def undo(self):
        """Undo the seat allocation.

        Makes a POST request to cancel the seat allocation.
        Updates the booking with cancellation details.

        Raises:
            Exception: If there is an error during cancellation
        """
        try:
            async with httpx.AsyncClient() as client:
                logger.info(
                    f"Cancelling seat allocation for booking: {self.booking.booking_id}"
                )
                response = await client.post(
                    f"{self.settings.payment_service_url}/api/allocations/cancel",
                    json={"booking_id": self.booking.booking_id},
                )

                cancel_result = TransactionResult(**response.json())
                logger.info(
                    f"Cancel seat allocation transaction result: {cancel_result}"
                )
                self.booking.steps.append(
                    BookingStep(
                        service="allocation_service",
                        operation="cancel_seat_allocation",
                        status=response.status,
                        timestamp=response.data.get("timestamp", ""),
                    )
                )
        except Exception as e:
            logger.error(f"Error while cancelling the allocation: {str(e)}")
            raise
