import logging
import sys
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            # Use a UNIX timestamp
            log_record['timestamp'] = record.created
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

def setup_logging():
    """
    Configures the logging to output structured JSON to stdout.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    logHandler = logging.StreamHandler(sys.stdout)
    
    # Add our custom formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)

    # Also configure the uvicorn access logger to use our formatter
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.addHandler(logHandler)
    uvicorn_access_logger.propagate = False
