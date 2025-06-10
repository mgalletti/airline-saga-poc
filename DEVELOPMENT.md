# Development Guide

This document provides information about the development environment, tools, and best practices for working with the Airline Saga Pattern POC.


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


## Technology Stack

This project uses FastAPI with Uvicorn as the ASGI server for implementing microservices.

### Uvicorn

Uvicorn is an ASGI (Asynchronous Server Gateway Interface) server implementation for Python. It's specifically designed to work with asynchronous frameworks like FastAPI, and it's what actually runs your FastAPI application.

#### Key Features of Uvicorn:

1. **ASGI-compatible**: Implements the ASGI specification, which allows asynchronous Python web applications to communicate with web servers.

2. **High Performance**: Built on uvloop and httptools (optional dependencies) for extremely fast HTTP processing.

3. **Hot Reload**: Supports automatic reloading when code changes are detected, which is great for development.

4. **Production-Ready**: Can be used in production environments, especially when combined with Gunicorn as a process manager.

#### How to Use Uvicorn:

##### 1. Basic Usage:

To run a FastAPI application with Uvicorn, you can use the command line:

```bash
uvicorn airline_saga.seat_service.main:app --host 0.0.0.0 --port 8001 --reload
```

Where:
- `airline_saga.seat_service.main:app` is the import path to your FastAPI application instance
- `--host 0.0.0.0` makes the server accessible from any network interface
- `--port 8001` sets the port number
- `--reload` enables auto-reload when code changes (for development)

##### 2. Programmatic Usage:

You can also run Uvicorn programmatically from within your Python code:

```python
if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "airline_saga.seat_service.main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=True
    )
```

This allows you to run the application directly with `python -m airline_saga.seat_service.main`.

##### 3. Production Deployment:

For production, it's recommended to use Gunicorn as a process manager with Uvicorn workers:

```bash
gunicorn airline_saga.seat_service.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

Where:
- `-w 4` specifies 4 worker processes
- `-k uvicorn.workers.UvicornWorker` uses Uvicorn's worker class

##### 4. Common Options:

- `--log-level`: Set the log level (debug, info, warning, error, critical)
- `--workers`: Number of worker processes (for multi-process server)
- `--limit-concurrency`: Maximum number of concurrent connections
- `--timeout-keep-alive`: Seconds to keep idle connections open

### FastAPI + Uvicorn vs Django

The uvicorn+FastAPI stack offers several key advantages compared to Django, particularly in specific use cases:

#### Performance and Speed
- **FastAPI** is significantly faster than Django due to its asynchronous nature and Starlette foundation
- **Uvicorn** as an ASGI server provides high-performance request handling compared to Django's traditional WSGI approach
- Benchmarks typically show FastAPI handling 2-3x more requests per second than Django

#### Asynchronous Support
- **Native async/await**: FastAPI is built from the ground up for asynchronous programming
- Better handling of concurrent connections without blocking threads
- Ideal for microservices that need to make multiple external API calls

#### API-First Design
- FastAPI is specifically optimized for building APIs, with automatic OpenAPI documentation
- Automatic request validation and serialization through Pydantic
- Interactive API documentation with Swagger UI and ReDoc built-in

#### Lightweight and Modular
- FastAPI is minimalist by design - you add only what you need
- Lower memory footprint than Django's full-stack approach
- Better suited for microservices and containerized deployments

#### Type Checking
- FastAPI leverages Python's type hints for runtime validation
- Provides better IDE support and catches errors earlier
- Reduces the need for extensive testing of input validation

#### When to Choose FastAPI+Uvicorn over Django
- Building microservices architecture
- Performance-critical APIs
- Real-time applications with WebSockets
- Services that need to handle many concurrent connections
- When you need a lightweight, focused API framework

Django remains better for full-stack web applications, content management systems, or when you need its rich ecosystem of built-in features like admin interface, ORM, and authentication system out of the box.

## Development Workflow

### Setting Up the Development Environment

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the package in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

### Running the Services

Each microservice can be started individually:

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

### API Documentation

FastAPI automatically generates interactive API documentation:

- Swagger UI: `http://localhost:{port}/docs`
- ReDoc: `http://localhost:{port}/redoc`

These interfaces allow you to explore and test the API endpoints directly from your browser.

## Linting and formatting

This project uses [Ruff](https://docs.astral.sh/ruff/) as linter and formatter, 10-100x faster than other ones such Flake8 and Black.
Ruff combines the functionality of multiple tools (flake8, black, isort, etc.) into a single, fast tool. The configuration in your pyproject.toml already sets up rules from various categories:

- E: pycodestyle errors
- F: Pyflakes
- I: isort
- N: naming conventions
- B: flake8-bugbear
- COM: flake8-commas
- C4: flake8-comprehensions
- UP: pyupgrade
- SIM: flake8-simplify
- ARG: flake8-unused-arguments
- PTH: flake8-use-pathlib

You can run Ruff as part of your CI/CD pipeline or as a pre-commit hook for consistent code quality across your project.


### For linting:
```bash
# Run Ruff linter on your entire project
ruff check .

# Run Ruff linter on a specific directory
ruff check src/

# Run Ruff linter on a specific file
ruff check src/airline_saga/orchestrator/main.py
```

### For formatting:
```bash
# Format your entire project
ruff format .

# Format a specific directory
ruff format src/

# Format a specific file
ruff format src/airline_saga/orchestrator/main.py
```

### For checking and fixing issues automatically:
```bash
# Check and fix issues where possible
ruff check --fix .
```

### Common options:
```bash
# Show detailed error information
ruff check --verbose .

# Show statistics about found issues
ruff check --statistics .

# Select specific rule categories
ruff check --select E,F,I .
```


## API Definitions

### Seat Service API

#### 1. Get Flight Seats
- **Method**: GET
- **URL**: `/api/flights/{flight_number}?status={status}`
- **Response**:
```json
{
  "flight_number": "FL001",
  "seats": [
    {
      "seat_number": "1A",
      "status": "available",
      "booking_id": null,
      "metadata": null
    },
    {
      "seat_number": "1B",
      "status": "blocked",
      "booking_id": "b8f9c1d2-e3f4-5a6b-7c8d-9e0f1a2b3c4d",
      "metadata": null
    },
    {
      "seat_number": "2A",
      "status": "booked",
      "booking_id": "a7b8c9d0-e1f2-3a4b-5c6d-7e8f9a0b1c2d",
      "metadata": null
    }
  ]
}
```

#### 2. Block Seat
- **Method**: POST
- **URL**: `/api/seats/block`
- **Request**:
```json
{
  "booking_id": "b8f9c1d2-e3f4-5a6b-7c8d-9e0f1a2b3c4d",
  "flight_number": "FL001",
  "seat_number": "1A"
}
```
- **Response**:
```json
{
  "success": true,
  "booking_id": "b8f9c1d2-e3f4-5a6b-7c8d-9e0f1a2b3c4d",
  "status": "COMPLETED",
  "message": "Seat 1A on flight FL001 blocked successfully",
  "data": {
    "flight_number": "FL001",
    "seat_number": "1A"
  }
}
```

#### 3. Release Seat (Compensating Transaction)
- **Method**: POST
- **URL**: `/api/seats/release`
- **Request**:
```json
{
  "booking_id": "b8f9c1d2-e3f4-5a6b-7c8d-9e0f1a2b3c4d"
}
```
- **Response**:
```json
{
  "success": true,
  "booking_id": "b8f9c1d2-e3f4-5a6b-7c8d-9e0f1a2b3c4d",
  "status": "RELEASED",
  "message": "Seat 1A on flight FL001 released successfully"
}
```

### Payment Service API

#### 1. Process Payment
- **Method**: POST
- **URL**: `/api/payments/process`
- **Request**:
```json
{
  "booking_id": "b8f9c1d2-e3f4-5a6b-7c8d-9e0f1a2b3c4d",
  "amount": 299.99,
  "currency": "USD",
  "payment_method_type": "credit_card",
  "payment_metadata": {
    "card_number": "XXXX-XXXX-XXXX-1234",
    "expiry": "12/25",
    "name": "John Doe"
  }
}
```
- **Response**:
```json
{
  "success": true,
  "booking_id": "b8f9c1d2-e3f4-5a6b-7c8d-9e0f1a2b3c4d",
  "status": "COMPLETED",
  "message": "Payment processed successfully",
  "data": {
    "payment_id": "pay_28f9c1d2e3f4",
    "amount": 299.99,
    "currency": "USD"
  }
}
```

#### 2. Refund Payment (Compensating Transaction)
- **Method**: POST
- **URL**: `/api/payments/refund`
- **Request**:
```json
{
  "booking_id": "b8f9c1d2-e3f4-5a6b-7c8d-9e0f1a2b3c4d"
}
```
- **Response**:
```json
{
  "success": true,
  "booking_id": "b8f9c1d2-e3f4-5a6b-7c8d-9e0f1a2b3c4d",
  "status": "REFUNDED",
  "message": "Payment refunded successfully",
  "data": {
    "payment_id": "pay_28f9c1d2e3f4",
    "refund_id": "ref_38f9c1d2e3f4"
  }
}
```

### Allocation Service API

#### 1. Allocate Seat
- **Method**: POST
- **URL**: `/api/allocations/allocate`
- **Request**:
```json
{
  "booking_id": "b8f9c1d2-e3f4-5a6b-7c8d-9e0f1a2b3c4d",
  "flight_number": "FL001",
  "seat_number": "1A",
  "passenger_name": "John Doe"
}
```
- **Response**:
```json
{
  "success": true,
  "booking_id": "b8f9c1d2-e3f4-5a6b-7c8d-9e0f1a2b3c4d",
  "status": "COMPLETED",
  "message": "Seat allocated successfully",
  "data": {
    "allocation_id": "alloc_48f9c1d2e3f4",
    "boarding_pass": {
      "passenger": "John Doe",
      "flight": "FL001",
      "seat": "1A",
      "gate": "B12",
      "boarding_time": "2025-06-15T14:30:00Z"
    }
  }
}
```

#### 2. Cancel Allocation (Compensating Transaction)
- **Method**: POST
- **URL**: `/api/allocations/cancel`
- **Request**:
```json
{
  "booking_id": "b8f9c1d2-e3f4-5a6b-7c8d-9e0f1a2b3c4d"
}
```
- **Response**:
```json
{
  "success": true,
  "booking_id": "b8f9c1d2-e3f4-5a6b-7c8d-9e0f1a2b3c4d",
  "status": "RELEASED",
  "message": "Allocation cancelled successfully"
}
```

### Orchestrator API

#### 1. Start Booking Process
- **Method**: POST
- **URL**: `/api/bookings/start`
- **Request**:
```json
{
  "passenger_name": "John Doe",
  "flight_number": "FL001",
  "seat_number": "1A",
  "payment_details": {
    "amount": 299.99,
    "currency": "USD",
    "payment_method_type": "credit_card",
    "payment_metadata": {
      "card_number": "XXXX-XXXX-XXXX-1234",
      "expiry": "12/25",
      "name": "John Doe"
    }
  }
}
```
- **Response**:
```json
{
  "booking_id": "b8f9c1d2-e3f4-5a6b-7c8d-9e0f1a2b3c4d",
  "status": "PENDING",
  "message": "Booking process started"
}
```

#### 2. Get Booking Status
- **Method**: GET
- **URL**: `/api/bookings/{booking_id}`
- **Response**:
```json
{
  "booking_id": "b8f9c1d2-e3f4-5a6b-7c8d-9e0f1a2b3c4d",
  "status": "COMPLETED",
  "passenger_name": "John Doe",
  "flight_number": "FL001",
  "seat_number": "1A",
  "steps": [
    {
      "service": "seat_service",
      "operation": "block_seat",
      "status": "COMPLETED",
      "timestamp": "2025-06-03T08:05:23Z"
    },
    {
      "service": "payment_service",
      "operation": "process_payment",
      "status": "COMPLETED",
      "timestamp": "2025-06-03T08:05:25Z"
    },
    {
      "service": "allocation_service",
      "operation": "allocate_seat",
      "status": "COMPLETED",
      "timestamp": "2025-06-03T08:05:27Z"
    }
  ],
  "boarding_pass": {
    "passenger": "John Doe",
    "flight": "FL001",
    "seat": "1A",
    "gate": "B12",
    "boarding_time": "2025-06-15T14:30:00Z"
  }
}
```

#### 3. Cancel Booking
- **Method**: POST
- **URL**: `/api/bookings/{booking_id}/cancel`
- **Response**:
```json
{
  "booking_id": "b8f9c1d2-e3f4-5a6b-7c8d-9e0f1a2b3c4d",
  "status": "CANCELLED",
  "message": "Booking cancelled successfully",
  "compensation_steps": [
    {
      "service": "allocation_service",
      "operation": "cancel_allocation",
      "status": "RELEASED",
      "timestamp": "2025-06-03T09:15:23Z"
    },
    {
      "service": "payment_service",
      "operation": "refund_payment",
      "status": "REFUNDED",
      "timestamp": "2025-06-03T09:15:25Z"
    },
    {
      "service": "seat_service",
      "operation": "release_seat",
      "status": "RELEASED",
      "timestamp": "2025-06-03T09:15:27Z"
    }
  ]
}
```
