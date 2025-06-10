import httpx
from airline_saga.common.models import TransactionResult, BookingStep
from airline_saga.common.exceptions import OrchestratorException
from airline_saga.orchestrator.services.commands import (
    OrchestratorCommand,
    OrchestratorCommandArgs,
)
from airline_saga.orchestrator import logger


class SeatCommand(OrchestratorCommand):
    """
    Command class for handling seat booking operations in the airline booking system.
    Handles blocking and releasing seats as part of the booking saga pattern.
    """

    def __init__(
        self,
        command_args: OrchestratorCommandArgs,
    ):
        """
        Initialize the SeatCommand.

        Args:
            command_args (OrchestratorCommandArgs): Command arguments containing:
                - booking: The booking object
                - flight_number: Flight number for the allocation
                - seat_number: Seat number to allocate
                - settings: Application settings
        """
        super().__init__()
        self.booking = command_args.booking
        self.flight_number = command_args.flight_number
        self.seat_number = command_args.seat_number
        self.settings = command_args.settings

    async def execute(self):
        """
        Execute the seat blocking operation.

        Makes an HTTP request to block the specified seat for the booking.
        Updates the booking steps with the result.

        Raises:
            OrchestratorException: If the seat blocking operation fails
        """
        # Step 1: Block seat
        async with httpx.AsyncClient() as client:
            logger.info("Invoking Seat service: block seat")
            block_response = await client.post(
                f"{self.settings.seat_service_url}/api/seats/block",
                json={
                    "booking_id": self.booking.booking_id,
                    "flight_number": self.flight_number,
                    "seat_number": self.seat_number,
                },
            )

            if block_response.status_code != 200:
                error_data = block_response.json()
                logger.error(f"Cannot block seat: {error_data}")
                error_msg = error_data.get("message", "Unknown error")
                self.booking.steps.append(
                    BookingStep(
                        service="seat_service",
                        operation="block_seat",
                        status="FAILED",
                        timestamp="",
                        message=error_msg,
                    )
                )
                raise OrchestratorException(
                    f"Failed to block seat: {error_data.get('message', 'Unknown error')}",
                    booking_id=self.booking.booking_id,
                )

            logger.info("Seat blocked successfully")
            block_result = TransactionResult(**block_response.json())
            self.booking.steps.append(
                BookingStep(
                    service="seat_service",
                    operation="block_seat",
                    status=block_result.status,
                    timestamp=block_result.data.get("timestamp", ""),
                )
            )

    async def undo(self):
        """
        Compensating transaction to release a previously blocked seat.

        Makes an HTTP request to release the seat associated with the booking.
        Updates the booking steps with the result.

        Raises:
            Exception: If the seat release operation fails
        """
        logger.info(f"Releasing the seat for booking: {self.booking.booking_id}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.settings.seat_service_url}/api/seats/release",
                    json={"booking_id": self.booking.booking_id},
                )
                release_seat_result = TransactionResult(**response.json())
                logger.info(f"Release seat transaction result: {release_seat_result}")
                self.booking.steps.append(
                    BookingStep(
                        service="seat_service",
                        operation="release_seat",
                        status=release_seat_result.status,
                        timestamp=release_seat_result.data.get("timestamp", ""),
                    )
                )
        except Exception as e:
            logger.error(f"Error while releasing the seat: {str(e)}")
            raise
