"""Lightweight logging helpers for the city simulation."""

from __future__ import annotations

import logging
from typing import Final

_LOGGER_NAME: Final[str] = "cityforge"

_configured: Final[bool] = False


def get_logger(name: str) -> logging.Logger:
    """Return a child logger of the ``cityforge`` root logger."""
    return logging.getLogger(f"{_LOGGER_NAME}.{name}")


def setup_logging(level: int = logging.INFO, log_file: str | None = None) -> logging.Logger:
    """Configure the ``cityforge`` logger hierarchy.

    Args:
        level: ``logging`` level such as ``logging.INFO`` or ``logging.DEBUG``.
        log_file: Optional path of a file the root city logger writes to.

    Returns:
        The configured root ``cityforge`` logger.
    """
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False
    if log_file:
        _add_file_handler(logger, log_file)
    return logger


def _add_file_handler(logger: logging.Logger, log_file: str) -> None:
    try:
        from pathlib import Path

        handler = logging.FileHandler(str(Path(log_file)))
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        logger.addHandler(handler)
    except OSError:  # pragma: no cover - defensive, never crash over logging setup
        logger.warning("Could not attach file handler to %s", log_file)
