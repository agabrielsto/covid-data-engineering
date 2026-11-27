"""Logging helpers for pipeline execution and observability."""

import logging
import os
from contextlib import contextmanager
from time import perf_counter


def get_logger(name: str) -> logging.Logger:
    """Return a module logger with a consistent console configuration."""
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        ))
        root_logger.addHandler(handler)

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root_logger.setLevel(level)
    return logging.getLogger(name)


@contextmanager
def log_stage(logger: logging.Logger, stage_name: str):
    """Log stage start, duration, success, and exceptions before re-raising."""
    started_at = perf_counter()
    logger.info("event=stage_started stage=%s", stage_name)

    try:
        yield
    except Exception:
        duration = perf_counter() - started_at
        logger.exception(
            "event=stage_failed stage=%s duration_seconds=%.3f",
            stage_name,
            duration,
        )
        raise
    else:
        duration = perf_counter() - started_at
        logger.info(
            "event=stage_completed stage=%s duration_seconds=%.3f",
            stage_name,
            duration,
        )
