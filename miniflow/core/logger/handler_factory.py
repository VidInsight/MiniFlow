"""
Centralized handler creation to eliminate duplicate code
"""

from typing import Optional
from .handlers import RotatingFileHandler, ConsoleHandler
from .formatters import JSONFormatter, PlainTextFormatter
from .levels import LogLevel


def create_file_handler(
    filename: str,
    level: str = "INFO", 
    formatter_type: str = "json",
    max_size_mb: int = 100,
    max_files: int = 5,
    **kwargs
) -> RotatingFileHandler:
    """Create standardized file handler"""
    
    # Create formatter
    if formatter_type == "json":
        formatter = JSONFormatter()
    else:
        formatter = PlainTextFormatter()
    
    # Create handler
    handler = RotatingFileHandler(
        filename=filename,
        max_size_mb=max_size_mb,
        max_files=max_files,
        level=level,
        formatter=formatter,
        **kwargs
    )
    
    # For simplified API, use sync mode by default
    # The handler will auto-start when needed
    
    return handler


def create_console_handler(
    level: str = "ERROR",
    formatter_type: str = "plain"
) -> ConsoleHandler:
    """Create standardized console handler"""
    
    # Create formatter
    if formatter_type == "json":
        formatter = JSONFormatter()
    else:
        formatter = PlainTextFormatter()
    
    # Create handler
    handler = ConsoleHandler(
        level=level,
        formatter=formatter
    )
    
    return handler


def create_standard_handlers(
    filename: str,
    file_level: str = "INFO",
    file_formatter: str = "json",
    console_output: bool = True,
    console_level: str = "ERROR", 
    console_formatter: str = "plain",
    max_size_mb: int = 100,
    max_files: int = 5,
    **kwargs
) -> list:
    """Create standard set of handlers (file + optional console)"""
    
    handlers = []
    
    # File handler
    file_handler = create_file_handler(
        filename=filename,
        level=file_level,
        formatter_type=file_formatter,
        max_size_mb=max_size_mb,
        max_files=max_files,
        **kwargs
    )
    handlers.append(file_handler)
    
    # Optional console handler
    if console_output:
        console_handler = create_console_handler(
            level=console_level,
            formatter_type=console_formatter
        )
        handlers.append(console_handler)
    
    return handlers
