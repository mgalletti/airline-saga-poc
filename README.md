# Airline Saga Pattern POC

This project demonstrates a proof of concept implementation of the Saga pattern using a microservices architecture for an airline flight booking system.

## Architecture

The system consists of the following microservices:

1. **Seat Service**: Handles blocking and allocation of seats
2. **Payment Service**: Processes payment transactions
3. **Allocation Service**: Finalizes seat allocation
4. **Orchestrator**: Coordinates the saga pattern workflow


### 1. Seat Service
Handles seat availability, blocking, and releasing.

**Endpoints:**
- GET `/api/flights/{flight_number}` - Get flight information with optional seat status filtering
- POST `/api/seats/block` - Block a seat for a booking
- POST `/api/seats/release` - Release a blocked seat (compensating transaction)

### 2. Payment Service
Processes payments and refunds.

**Endpoints:**
- POST `/api/payments/process` - Process a payment for a booking
- POST `/api/payments/refund` - Refund a payment (compensating transaction)

### 3. Allocation Service
Finalizes seat allocations and generates boarding passes.

**Endpoints:**
- POST `/api/allocations/allocate` - Allocate a seat and generate a boarding pass
- POST `/api/allocations/cancel` - Cancel a seat allocation (compensating transaction)

### 4. Orchestrator Service
Coordinates the entire saga workflow.

**Endpoints:**
- POST `/api/bookings/start` - Start a new booking process
- GET `/api/bookings/{booking_id}` - Get booking details and status
- POST `/api/bookings/{booking_id}/cancel` - Cancel a booking

Each service implements:
- Exception handling with dedicated exception handler modules
- In-memory databases (for simplicity)
- Health check endpoints
- Typed function parameters and return values

## Saga Pattern Implementation

The orchestrator implements the saga pattern by:
1. Executing each step in sequence (block seat → process payment → allocate seat)
2. Implementing compensating transactions if any step fails
3. Tracking the status of each step
4. Providing a way to query the overall booking status

If a step fails, the orchestrator executes compensating transactions in reverse order:
- If allocation fails: refund payment, release seat
- If payment fails: release seat
- If seat blocking fails: no compensation needed


### Workflow

1. Block a seat (Seat Service)
2. Process payment (Payment Service)
3. Allocate the seat (Allocation Service)

If any step fails, the corresponding compensating transactions are executed in reverse order:

3. Cancel seat allocation (if needed)
2. Refund payment (if needed)
1. Release blocked seat (if needed)

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd airline-saga-poc

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package in development mode
pip install -e ".[dev]"
```

### Running the Services

Each service can be started individually:

```bash
# Start the seat service
uvicorn airline_saga.seat_service.main:app --host 0.0.0.0 --port 8001 --reload

# Start the payment service
uvicorn airline_saga.payment_service.main:app --host 0.0.0.0 --port 8002 --reload

# Start the allocation service
uvicorn airline_saga.allocation_service.main:app --host 0.0.0.0 --port 8003 --reload

# Start the orchestrator
uvicorn airline_saga.orchestrator.main:app --host 0.0.0.0 --port 8000 --reload
```

## Testing

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit

# Run integration tests only
pytest tests/integration
```

