from logging import Logger
import sys
import logging
from fastapi import FastAPI


def config_logger(service_name: str, level: str = "INFO") -> Logger:
    # Validate logging level
    if level.upper() not in logging.getLevelNamesMapping():
        raise ValueError(f"Logging level unknown: {level}")

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger(service_name)

    return logger


def setup_request_logging(app: FastAPI, logger: logging.Logger) -> None:
    """
    Set up request logging middleware for a FastAPI application.
    The middleware will automatically log all incoming requests and outgoing responses,
    while you can add more specific logging within your route handlers and service logic.

    Args:
        app: The FastAPI application
        logger: The logger instance
    """

    @app.middleware("http")
    async def log_requests(request, call_next):
        """Log incoming requests and outgoing responses."""
        # Log the request
        logger.info(f"Request: {request.method} {request.url.path}")

        # Process the request
        response = await call_next(request)

        # Log the response
        logger.info(
            f"Response: {request.method} {request.url.path} - Status: {response.status_code}"
        )

        return response
