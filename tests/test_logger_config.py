#!/usr/bin/env python3
"""Tests for logger configuration utilities."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path

import logger_config


def test_get_logger_returns_consistent_logger() -> None:
    """get_logger should always return the same logger instance for a name."""
    first = logger_config.get_logger("mcp.tests")
    second = logger_config.get_logger("mcp.tests")
    assert first is second
    assert first.name == "mcp.tests"


def test_logging_configuration_sets_handlers() -> None:
    """Root logger should be configured with file and stream handlers."""
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()
    root.setLevel(logging.NOTSET)

    importlib.reload(logger_config)
    root = logging.getLogger()
    assert root.getEffectiveLevel() == logging.INFO

    handler_types = {type(handler) for handler in root.handlers}
    assert logging.FileHandler in handler_types
    assert logging.StreamHandler in handler_types

    file_handlers = [
        handler for handler in root.handlers if isinstance(handler, logging.FileHandler)
    ]
    assert any(Path(handler.baseFilename).name == "mcp_server.log" for handler in file_handlers)
