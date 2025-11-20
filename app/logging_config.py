"""Application-wide logging configuration."""
"""Logging configuration with JSON formatting and request ID tracking."""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Format log records as JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add request ID if present
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        # Add any extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def configure_logging(use_json: bool = True):
    """Configure application logging.
    
    Args:
        use_json: If True, use JSON formatter; otherwise use simple text format
    """
    logger = logging.getLogger("legit-search")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    handler = logging.StreamHandler(sys.stdout)
    
    if use_json:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
    
    logger.addHandler(handler)
    logger.propagate = False
