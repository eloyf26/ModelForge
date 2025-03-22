"""
ModelForge AI - AutoML platform that transforms plain-language requirements into production-ready ML models.
"""

__version__ = "1.0.0"

import os
import logging.config

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": "logs/modelforge.log"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
})