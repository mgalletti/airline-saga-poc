"""Allocation Service API implementation."""

from typing import Dict
import uuid
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends

from airline_saga.common.models import TransactionStatus, TransactionResult
from airline_saga.common.config import AllocationServiceSettings
from airline_saga.common.exceptions import (
    AllocationFailedException,
    BookingNotFoundException
)
from airline_saga.allocation_service.models import (
    Allocation, AllocateSeatRequest, CancelAllocationRequest, 
    AllocationStatus, BoardingPass
)
from airline_saga.allocation_service.exception_handlers import register_exception_handlers

app: FastAPI = FastAPI(title="Allocation Service", description="Service for allocating seats")

# Register exception handlers
register_exception_handlers(app)

# In-memory database for simplicity
allocations_db: Dict[str, Allocation] = {}
allocation_by_booking_id: Dict[str, str] = {}  # booking_id -> allocation_id

# Sample gate assignments
gates = {
    "FL001": "B12",
    "FL002": "C05",
    "FL003": "A22",
}

# Sample boarding times (2 hours from now)
boarding_times = {
    "FL001": (datetime.now() + timedelta(hours=2)).isoformat(),
    "FL002": (datetime.now() + timedelta(hours=3)).isoformat(),
    "FL003": (datetime.now() + timedelta(hours=4)).isoformat(),
}


def get_settings() -> AllocationServiceSettings:
    """Get service settings."""
    return AllocationServiceSettings()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/allocations/allocate")
async def allocate_seat(request: AllocateSeatRequest):
    """
    Allocate a seat for a booking.
    
    Args:
        request: The allocation request
        
    Returns:
        Transaction result
    """
    booking_id = request.booking_id
    
    # Check if allocation already exists for this booking
    if booking_id in allocation_by_booking_id:
        existing_allocation_id = allocation_by_booking_id[booking_id]
        existing_allocation = allocations_db[existing_allocation_id]
        
        # If allocation is already completed, return success
        if existing_allocation.status == AllocationStatus.ALLOCATED:
            return TransactionResult(
                success=True,
                booking_id=booking_id,
                status=TransactionStatus.COMPLETED,
                message="Seat already allocated",
                data={
                    "allocation_id": existing_allocation_id,
                    "boarding_pass": existing_allocation.boarding_pass.dict() if existing_allocation.boarding_pass else None
                }
            )
    
    # Generate an allocation ID
    allocation_id = f"alloc_{str(uuid.uuid4())[:8]}"
    
    # Get gate and boarding time for the flight
    gate = gates.get(request.flight_number, "Gate TBD")
    boarding_time = boarding_times.get(request.flight_number, datetime.utcnow().isoformat())
    
    # Create boarding pass
    boarding_pass = BoardingPass(
        passenger=request.passenger_name,
        flight=request.flight_number,
        seat=request.seat_number,
        gate=gate,
        boarding_time=boarding_time
    )
    
    # Create allocation record
    allocation = Allocation(
        allocation_id=allocation_id,
        booking_id=booking_id,
        flight_number=request.flight_number,
        seat_number=request.seat_number,
        passenger_name=request.passenger_name,
        status=AllocationStatus.ALLOCATED,
        boarding_pass=boarding_pass
    )
    
    # Store allocation
    allocations_db[allocation_id] = allocation
    allocation_by_booking_id[booking_id] = allocation_id
    
    return TransactionResult(
        success=True,
        booking_id=booking_id,
        status=TransactionStatus.COMPLETED,
        message="Seat allocated successfully",
        data={
            "allocation_id": allocation_id,
            "boarding_pass": boarding_pass.dict()
        }
    )


@app.post("/api/allocations/cancel")
async def cancel_allocation(request: CancelAllocationRequest):
    """
    Cancel a seat allocation.
    
    Args:
        request: The cancellation request
        
    Returns:
        Transaction result
    """
    booking_id = request.booking_id
    
    # Check if allocation exists for this booking
    if booking_id not in allocation_by_booking_id:
        raise BookingNotFoundException(
            f"No allocation found for booking {booking_id}",
            booking_id=booking_id
        )
    
    allocation_id = allocation_by_booking_id[booking_id]
    allocation = allocations_db[allocation_id]
    
    # Check if allocation can be cancelled
    if allocation.status == AllocationStatus.CANCELLED:
        return TransactionResult(
            success=True,
            booking_id=booking_id,
            status=TransactionStatus.RELEASED,
            message="Allocation already cancelled"
        )
    
    # Update allocation status
    allocation.status = AllocationStatus.CANCELLED
    allocations_db[allocation_id] = allocation
    
    return TransactionResult(
        success=True,
        booking_id=booking_id,
        status=TransactionStatus.RELEASED,
        message="Allocation cancelled successfully"
    )


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "airline_saga.allocation_service.main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=True
    )
