import logging
from logging.config import dictConfig
import sys
import os

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(levelname)s: %(name)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "default",
            "stream": sys.stdout,
        },
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
        "uvicorn.error": { "level": "WARNING", "handlers": ["console"], "propagate": False },
        "uvicorn.access": { "level": "WARNING", "handlers": ["console"], "propagate": False },
    },
}

def setup_logging():
    dictConfig(LOGGING_CONFIG)