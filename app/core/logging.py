"""Logging configuration."""

import logging


def configure_logging() -> None:
    """Configure a simple production-friendly log format."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
