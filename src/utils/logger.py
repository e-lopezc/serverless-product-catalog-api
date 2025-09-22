import logging
import json
import os
from typing import Any, Dict

def setup_logger(name: str) -> logging.Logger:
    """Set up structured logger for Lambda functions"""
    logger = logging.getLogger(name)

    # Avoid adding multiple handlers
    if logger.handlers:
        return logger

    # Set log level from environment variable
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logger.setLevel(getattr(logging, log_level))

    # Create handler
    handler = logging.StreamHandler()

    # Create formatter for structured logging
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

def log_request_info(logger: logging.Logger, event: Dict[str, Any]) -> None:
    """Log structured request information"""
    request_info = {
        'http_method': event.get('httpMethod'),
        'resource_path': event.get('resource'),
        'path_parameters': event.get('pathParameters'),
        'query_parameters': event.get('queryStringParameters'),
        'request_id': event.get('requestContext', {}).get('requestId')
    }
    logger.info(f"Processing request: {json.dumps(request_info)}")
