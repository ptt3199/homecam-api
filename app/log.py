"""Common logging utilities."""

import logging
import sys


def get_logger(name: str, loglevel: int = logging.DEBUG) -> logging.Logger:
    """Return a configured logger.
    
    Args:
        name (str): Logger name, typically __name__
        loglevel (int): Logging level, defaults to DEBUG
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.getLevelName(loglevel))
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger 