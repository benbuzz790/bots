"""Centralized logging strategy for the bots framework.
This module provides a unified logging system that:
- Uses structured logging with consistent formats
- Supports multiple log levels and categories
- Integrates with the BOM-free file writing system
- Provides context-aware logging for different components
- Supports both file and console output
- Enables easy debugging and monitoring
"""

import json
import sys
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from bots.utils.file_utils import append_text_file


class LogLevel(Enum):
    """Log levels for the bots framework."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """Log categories for different framework components."""

    GENERAL = "GENERAL"
    BOT = "BOT"
    CONVERSATION = "CONVERSATION"
    TOOLS = "TOOLS"
    API = "API"
    CONFIG = "CONFIG"
    FUNCTIONAL_PROMPTS = "FUNCTIONAL_PROMPTS"
    TESTING = "TESTING"


class BotsLogger:
    """Centralized logger for the bots framework.
    Provides structured logging with support for:
    - Multiple output destinations (file, console)
    - Categorized logging for different components
    - Structured data logging (JSON format)
    - Context preservation across operations
    - Performance monitoring
    """

    def __init__(
        self,
        log_file: Optional[Union[str, Path]] = None,
        console_output: bool = True,
        min_level: LogLevel = LogLevel.INFO,
        structured_format: bool = True,
    ):
        """Initialize the logger.
        Args:
            log_file: Path to log file (default: logs/bots.log)
            console_output: Whether to output to console (default: True)
            min_level: Minimum log level to record (default: INFO)
            structured_format: Whether to use structured JSON format (default: True)
        """
        self.log_file = Path(log_file) if log_file else Path("logs") / "bots.log"
        self.console_output = console_output
        self.min_level = min_level
        self.structured_format = structured_format
        self.context_stack: List[Dict[str, Any]] = []
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        # Initialize with startup message
        self._log_startup()

    def _log_startup(self) -> None:
        """Log framework startup information."""
        startup_info = {
            "event": "framework_startup",
            "timestamp": datetime.now().isoformat(),
            "log_file": str(self.log_file),
            "min_level": self.min_level.value,
            "structured_format": self.structured_format,
        }
        self._write_log(LogLevel.INFO, LogCategory.GENERAL, "Framework startup", startup_info)

    def _should_log(self, level: LogLevel) -> bool:
        """Check if a message should be logged based on minimum level."""
        level_order = {LogLevel.DEBUG: 0, LogLevel.INFO: 1, LogLevel.WARNING: 2, LogLevel.ERROR: 3, LogLevel.CRITICAL: 4}
        return level_order[level] >= level_order[self.min_level]

    def _format_message(
        self, level: LogLevel, category: LogCategory, message: str, data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format a log message."""
        timestamp = datetime.now().isoformat()
        if self.structured_format:
            log_entry = {
                "timestamp": timestamp,
                "level": level.value,
                "category": category.value,
                "message": message,
            }
            # Add context from stack
            if self.context_stack:
                log_entry["context"] = self.context_stack.copy()
            # Add additional data
            if data:
                log_entry["data"] = data
            return json.dumps(log_entry, ensure_ascii=False)
        else:
            # Simple text format
            context_str = ""
            if self.context_stack:
                context_parts = []
                for ctx in self.context_stack:
                    for key, value in ctx.items():
                        context_parts.append(f"{key}={value}")
                context_str = f" [{', '.join(context_parts)}]"
            data_str = ""
            if data:
                data_str = f" | {json.dumps(data, ensure_ascii=False)}"
            return f"[{timestamp}] {level.value} {category.value}{context_str}: {message}{data_str}"

    def _write_log(self, level: LogLevel, category: LogCategory, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Write a log entry to configured outputs."""
        if not self._should_log(level):
            return
        formatted_message = self._format_message(level, category, message, data)
        # Write to file
        append_text_file(self.log_file, formatted_message + "\n")
        # Write to console if enabled
        if self.console_output:
            if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                print(formatted_message, file=sys.stderr)
            else:
                print(formatted_message)

    @contextmanager
    def context(self, **context_data):
        """Add context to all log messages within this block.
        Args:
            **context_data: Key-value pairs to add as context
        Example:
            with logger.context(bot_name="Claude", operation="respond"):
                logger.info("Processing request")
        """
        self.context_stack.append(context_data)
        try:
            yield
        finally:
            self.context_stack.pop()

    def debug(self, message: str, category: LogCategory = LogCategory.GENERAL, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a debug message."""
        self._write_log(LogLevel.DEBUG, category, message, data)

    def info(self, message: str, category: LogCategory = LogCategory.GENERAL, data: Optional[Dict[str, Any]] = None) -> None:
        """Log an info message."""
        self._write_log(LogLevel.INFO, category, message, data)

    def warning(
        self, message: str, category: LogCategory = LogCategory.GENERAL, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a warning message."""
        self._write_log(LogLevel.WARNING, category, message, data)

    def error(self, message: str, category: LogCategory = LogCategory.GENERAL, data: Optional[Dict[str, Any]] = None) -> None:
        """Log an error message."""
        self._write_log(LogLevel.ERROR, category, message, data)

    def critical(
        self, message: str, category: LogCategory = LogCategory.GENERAL, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a critical message."""
        self._write_log(LogLevel.CRITICAL, category, message, data)

    # Convenience methods for specific categories
    def bot_info(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log bot-related info."""
        self.info(message, LogCategory.BOT, data)

    def bot_error(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log bot-related error."""
        self.error(message, LogCategory.BOT, data)

    def conversation_info(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log conversation-related info."""
        self.info(message, LogCategory.CONVERSATION, data)

    def tool_info(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log tool-related info."""
        self.info(message, LogCategory.TOOLS, data)

    def tool_error(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log tool-related error."""
        self.error(message, LogCategory.TOOLS, data)

    def api_info(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log API-related info."""
        self.info(message, LogCategory.API, data)

    def api_error(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log API-related error."""
        self.error(message, LogCategory.API, data)

    def fp_info(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log functional prompt-related info."""
        self.info(message, LogCategory.FUNCTIONAL_PROMPTS, data)

    def fp_error(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log functional prompt-related error."""
        self.error(message, LogCategory.FUNCTIONAL_PROMPTS, data)

    def performance_log(
        self,
        operation: str,
        duration_ms: float,
        category: LogCategory = LogCategory.GENERAL,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log performance metrics."""
        perf_data = {"operation": operation, "duration_ms": duration_ms, "performance_metric": True}
        if additional_data:
            perf_data.update(additional_data)
        self.info(f"Performance: {operation} completed in {duration_ms:.2f}ms", category, perf_data)


# Global logger instance
_global_logger: Optional[BotsLogger] = None


def get_logger(
    log_file: Optional[Union[str, Path]] = None,
    console_output: bool = True,
    min_level: LogLevel = LogLevel.INFO,
    structured_format: bool = True,
) -> BotsLogger:
    """Get or create the global logger instance.
    Args:
        log_file: Path to log file (only used on first call)
        console_output: Whether to output to console (only used on first call)
        min_level: Minimum log level (only used on first call)
        structured_format: Whether to use structured format (only used on first call)
    Returns:
        Global BotsLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = BotsLogger(log_file, console_output, min_level, structured_format)
    return _global_logger


def configure_logging(
    log_file: Optional[Union[str, Path]] = None,
    console_output: bool = True,
    min_level: LogLevel = LogLevel.INFO,
    structured_format: bool = True,
) -> BotsLogger:
    """Configure the global logging system.
    Args:
        log_file: Path to log file
        console_output: Whether to output to console
        min_level: Minimum log level to record
        structured_format: Whether to use structured JSON format
    Returns:
        Configured BotsLogger instance
    """
    global _global_logger
    _global_logger = BotsLogger(log_file, console_output, min_level, structured_format)
    return _global_logger


# Convenience functions for global logging
def debug(message: str, category: LogCategory = LogCategory.GENERAL, data: Optional[Dict[str, Any]] = None) -> None:
    """Log a debug message using the global logger."""
    get_logger().debug(message, category, data)


def info(message: str, category: LogCategory = LogCategory.GENERAL, data: Optional[Dict[str, Any]] = None) -> None:
    """Log an info message using the global logger."""
    get_logger().info(message, category, data)


def warning(message: str, category: LogCategory = LogCategory.GENERAL, data: Optional[Dict[str, Any]] = None) -> None:
    """Log a warning message using the global logger."""
    get_logger().warning(message, category, data)


def error(message: str, category: LogCategory = LogCategory.GENERAL, data: Optional[Dict[str, Any]] = None) -> None:
    """Log an error message using the global logger."""
    get_logger().error(message, category, data)


def critical(message: str, category: LogCategory = LogCategory.GENERAL, data: Optional[Dict[str, Any]] = None) -> None:
    """Log a critical message using the global logger."""
    get_logger().critical(message, category, data)


@contextmanager
def log_context(**context_data):
    """Add context to all log messages within this block using the global logger.
    Args:
        **context_data: Key-value pairs to add as context
    Example:
        with log_context(bot_name="Claude", operation="respond"):
            info("Processing request")
    """
    with get_logger().context(**context_data):
        yield


@contextmanager
def log_performance(
    operation: str, category: LogCategory = LogCategory.GENERAL, additional_data: Optional[Dict[str, Any]] = None
):
    """Context manager for logging operation performance.
    Args:
        operation: Name of the operation being timed
        category: Log category for the performance metric
        additional_data: Additional data to include in the log
    Example:
        with log_performance("bot_response", LogCategory.BOT):
            response = bot.respond("Hello")
    """
    import time

    start_time = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        get_logger().performance_log(operation, duration_ms, category, additional_data)
