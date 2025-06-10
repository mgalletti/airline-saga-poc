"""Orchestrator Service - Coordinates the saga pattern workflow."""

from airline_saga.common.logger import config_logger

SERVICE_NAME = "Orchestrator Service"

logger = config_logger(service_name=SERVICE_NAME)
