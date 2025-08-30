"""
MiniFlow Logger initialization module
Simplified interface for logger setup and access
"""

from typing import Optional, Dict, Any
from .logger import AsyncLogger
from .handler_factory import create_standard_handlers


# Global logger registry to avoid duplicate handlers
_logger_registry: Dict[str, AsyncLogger] = {}
_simple_logger: Optional[AsyncLogger] = None


def clear_registry():
    """Clear the global logger registry"""
    global _logger_registry, _simple_logger
    _logger_registry.clear()
    _simple_logger = None


async def shutdown_all_loggers():
    """Shutdown all registered loggers"""
    for logger in _logger_registry.values():
        await logger.shutdown()
    
    if _simple_logger:
        await _simple_logger.shutdown()
    
    clear_registry()


def list_loggers() -> list:
    """Get list of registered logger names"""
    names = list(_logger_registry.keys())
    if _simple_logger:
        names.append("miniflow_simple")
    return names


def get_logger_info(name: str) -> Optional[Dict[str, Any]]:
    """Get logger information"""
    logger = _logger_registry.get(name) or (_simple_logger if name == "miniflow_simple" else None)
    
    if not logger:
        return None
    
    return {
        "name": logger.name,
        "level": logger.level.name,
        "handler_count": len(logger.handlers),
        "enabled": True
    }


def get_logger(name: str = None) -> AsyncLogger:
    """
    Get logger instance - reuses existing configured loggers
    
    Args:
        name: Logger adı (modül/servis adı)
        
    Returns:
        Logger instance
    """
    global _simple_logger
    
    if name:
        # Check if we already have a configured logger
        if name in _logger_registry:
            return _logger_registry[name]
        
        # Create new logger without default handlers (will be configured by setup_logging)
        return AsyncLogger(name, handlers=[])
    
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
        Configured logger instance
        
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
    
    # Extract logger name from filename
    import os
    logger_name = os.path.splitext(os.path.basename(filename))[0]
    
    # Check if we already have this logger
    if logger_name in _logger_registry:
        configured_logger = _logger_registry[logger_name]
    else:
        # Create new logger without default handlers
        configured_logger = AsyncLogger(logger_name, level=level, max_tasks=max_tasks, handlers=[])
        _logger_registry[logger_name] = configured_logger
    
    # Clear existing handlers
    configured_logger.handlers.clear()
    
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
        configured_logger.add_handler(handler)
    
    return configured_logger


# Varsayılan merkezi logger instance'ı kaldırıldı - kullanılmıyordu


def shutdown_logging() -> None:
    """Simplified logging system shutdown"""
    global _logger_registry, _simple_logger
    
    # Clear handlers from all loggers
    for logger in _logger_registry.values():
        logger.clear_handlers()
    
    if _simple_logger:
        _simple_logger.clear_handlers()
    
    clear_registry()