"""
MiniFlow Logging Module

Provides structured JSON logging with correlation ID support and async capabilities.
"""

from .logger import AsyncLogger
from .levels import LogLevel
from .context import (
    get_correlation_id,
    set_correlation_id,
    generate_correlation_id,
    with_correlation_id,
    correlation_context,
    ensure_correlation_id
)
from .formatters import JSONFormatter, PlainTextFormatter
from .handlers import RotatingFileHandler, ConsoleHandler
from .utils import handle_logging_error, get_context_mode, SimpleCircuitBreaker
from .registry import (
    LoggerConfig, ModuleLoggerConfig,  # For advanced configuration
    get_module_logger, register_module_config  # Registry functions
)
from .handler_factory import create_standard_handlers

__all__ = [
    'AsyncLogger',
    'LogLevel', 
    'JSONFormatter',
    'PlainTextFormatter',
    'RotatingFileHandler',
    'ConsoleHandler',
    'get_correlation_id',
    'set_correlation_id',
    'generate_correlation_id',
    'with_correlation_id',
    'correlation_context',
    'ensure_correlation_id',
    'get_logger',
    'setup_logging',
    'shutdown_logging',
    'handle_logging_error',
    'get_context_mode',
    'SimpleCircuitBreaker',
    'LoggerConfig',
    'ModuleLoggerConfig',
    'get_module_logger',
    'register_module_config'
]

# Simplified central logger - use registry for advanced features
_simple_logger = None


# LoggerConfig moved to registry.py to avoid duplication  
# Use ModuleLoggerConfig from registry for all configuration needs


# CentralLogger sınıfı kaldırıldı - kullanılmıyordu


def get_logger(name: str = None) -> AsyncLogger:
    """
    Simple logger instance - for advanced features use registry module
    
    Args:
        name: Logger adı (modül/servis adı)
        
    Returns:
        Logger instance
    """
    global _simple_logger
    
    if name:
        # Return named logger instance
        return AsyncLogger(name)
    
    # Return simple central logger
    if _simple_logger is None:
        _simple_logger = AsyncLogger("miniflow_simple")
    
    return _simple_logger


def setup_logging(
    level: str = "INFO",
    filename: str = "logs/miniflow.log",
    max_size_mb: int = 100,
    max_files: int = 5,
    console_output: bool = True,
    *,
    console_level: str = "ERROR",
    file_level: str = "INFO",
    console_formatter: str = "plain",  # "plain" | "json"
    file_formatter: str = "json"       # "json" | "plain"
) -> AsyncLogger:
    """
    Simple centralized logging setup
    
    Args:
        level: Log seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        filename: Log dosyası adı
        max_size_mb: Her dosyada maksimum dosya boyutu (MB) (min: 1)
        max_files: Maksimum dosya sayısı (min: 1)
        console_output: Terminal'e yazdırılsın mı?
        
    Returns:
        Simple logger instance
        
    Raises:
        ValueError: Geçersiz parametreler için
    """
    # Simple validation
    if not isinstance(level, str) or level.upper() not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        raise ValueError("level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("filename must be a non-empty string")
    
    if not isinstance(max_size_mb, int) or max_size_mb < 1:
        raise ValueError("max_size_mb must be a positive integer")
    
    if not isinstance(max_files, int) or max_files < 1:
        raise ValueError("max_files must be a positive integer")
    
    if not isinstance(console_output, bool):
        raise ValueError("console_output must be a boolean")
    
    if console_formatter not in ("plain", "json"):
        raise ValueError("console_formatter must be 'plain' or 'json'")
    
    if file_formatter not in ("plain", "json"):
        raise ValueError("file_formatter must be 'plain' or 'json'")
    
    max_tasks = 1000  # Default for simple logger
    
    global _simple_logger
    
    # Create or reuse simple logger
    if _simple_logger is None:
        _simple_logger = AsyncLogger("miniflow_setup", level=level, max_tasks=max_tasks)
    
    # Clear existing handlers
    _simple_logger.handlers.clear()
    
    # Use handler factory for consistent handler creation
    handlers = create_standard_handlers(
        filename=filename,
        file_level=file_level,
        file_formatter=file_formatter,
        console_output=console_output,
        console_level=console_level,
        console_formatter=console_formatter,
        max_size_mb=max_size_mb,
        max_files=max_files
    )
    
    # Add all handlers
    for handler in handlers:
        _simple_logger.add_handler(handler)
    
    return _simple_logger


# Varsayılan merkezi logger instance'ı kaldırıldı - kullanılmıyordu


def shutdown_logging() -> None:
    """Simplified logging system shutdown"""
    global _simple_logger
    
    if _simple_logger:
        try:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(_simple_logger.shutdown())
                else:
                    loop.run_until_complete(_simple_logger.shutdown())
            except RuntimeError:
                pass  # No event loop
        except Exception as e:
            handle_logging_error(e, "Logging shutdown error")
        finally:
            _simple_logger = None


# Python shutdown sırasında logging'i kapat
import atexit
atexit.register(shutdown_logging)
