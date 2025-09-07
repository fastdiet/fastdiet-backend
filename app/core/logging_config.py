import logging
from logging.config import dictConfig
import sys

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(levelname)s:     %(asctime)s - %(name)s - %(message)s",
            "datefmt": "%d-%m-%Y %H:%M:%S",
        },
        "detailed": {
            "format": "%(asctime)s - %(levelname)s - %(name)s - [%(module)s:%(lineno)d] - %(message)s",
            "datefmt": "%d-%m-%Y %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": sys.stdout,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "fast_diet_app.log",
            "maxBytes": 10485760,  # 10 MB per file
            "backupCount": 5,  # Keep 5 backup files
            "encoding": "utf8",
        },
    },
    "loggers": {
        "root": {
            "level": "INFO",
            "handlers": ["console", "file"],
        },
        "uvicorn.error": {
            "level": "WARNING",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "WARNING",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}

def setup_logging():
    dictConfig(LOGGING_CONFIG)