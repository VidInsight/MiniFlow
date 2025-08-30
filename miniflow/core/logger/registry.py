"""
Enhanced Logger Registry System for MiniFlow

Provides centralized logger management with module-specific configurations,
performance monitoring, and dynamic reconfiguration capabilities.
"""

import threading
import time
from typing import Dict, Optional, Set, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .logger import AsyncLogger
from .levels import LogLevel
from .handlers import RotatingFileHandler, ConsoleHandler
from .formatters import JSONFormatter, PlainTextFormatter
from .utils import handle_logging_error
from .handler_factory import create_standard_handlers, create_file_handler


class LoggerStrategy(Enum):
    """Logger yapılandırma stratejileri"""
    CENTRALIZED = "centralized"     # Tüm loglar merkezi dosyaya
    MODULE_BASED = "module_based"   # Her modül kendi dosyasına  
    HYBRID = "hybrid"               # Hem merkezi hem modül dosyalarına
    CUSTOM = "custom"               # Tamamen özel yapılandırma


@dataclass
class ModuleLoggerConfig:
    """Modül bazında logger yapılandırması"""
    module_name: str
    level: str = "INFO"
    filename: Optional[str] = None
    max_size_mb: int = 50
    max_files: int = 5
    console_output: bool = True
    console_level: str = "ERROR"
    file_formatter: str = "json"
    console_formatter: str = "plain"
    
    # Performance settings
    queue_size: int = 5000
    queue_timeout: float = 2.0
    worker_timeout: float = 0.5
    
    # Module-specific settings
    enabled: bool = True
    tags: Set[str] = field(default_factory=set)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.filename:
            self.filename = f"logs/{self.module_name}.log"


class LoggerRegistry:
    """
    Centralized logger registry with dynamic configuration management
    
    Features:
    - Module-based logger management
    - Dynamic reconfiguration
    - Performance monitoring
    - Strategy pattern for different logging approaches
    - Thread-safe operations
    """
    
    def __init__(self):
        self._loggers: Dict[str, AsyncLogger] = {}
        self._configs: Dict[str, ModuleLoggerConfig] = {}
        self._strategy: LoggerStrategy = LoggerStrategy.CENTRALIZED
        self._lock = threading.RLock()
        self._performance_stats: Dict[str, Dict[str, Any]] = {}
        self._hooks: Dict[str, Set[Callable]] = {
            "logger_created": set(),
            "config_changed": set(),
            "strategy_changed": set()
        }
        
        # Central logger for fallback
        self._central_logger: Optional[AsyncLogger] = None
        
    def set_strategy(self, strategy: LoggerStrategy) -> None:
        """Logging stratejisini değiştir"""
        with self._lock:
            old_strategy = self._strategy
            self._strategy = strategy
            
            # Notify hooks
            self._trigger_hooks("strategy_changed", {
                "old_strategy": old_strategy,
                "new_strategy": strategy
            })
            
            # Note: Reconfigure existing loggers would need async context
            # For now, skip auto-reconfigure on strategy change
    
    def register_module_config(self, config: ModuleLoggerConfig) -> None:
        """Modül yapılandırmasını kaydet - sync version"""
        with self._lock:
            self._configs[config.module_name] = config
            
            # Mark for lazy reconfiguration
            if config.module_name in self._loggers:
                # Just mark as dirty - will reconfigure on next access
                self._loggers[config.module_name]._needs_reconfig = True
                
        self._trigger_hooks("config_changed", {
            "module": config.module_name,
            "config": config
        })
    
    def get_logger(self, module_name: str) -> AsyncLogger:
        """Modül için logger al veya oluştur - sync version"""
        with self._lock:
            # Check if logger exists and is valid
            if module_name in self._loggers:
                logger = self._loggers[module_name]
                # Check if needs reconfiguration
                if hasattr(logger, '_needs_reconfig') and logger._needs_reconfig:
                    # Lazy reconfiguration
                    config = self._configs.get(module_name)
                    if config:
                        self._reconfigure_logger_sync(logger, config)
                        logger._needs_reconfig = False
                return logger
            
            # Yapılandırma var mı kontrol et
            config = self._configs.get(module_name)
            if not config:
                config = self._create_default_config(module_name)
                self._configs[module_name] = config
        
        # Logger oluştur (simplified sync version)
        logger = self._create_logger_sync(module_name, config)
        
        with self._lock:
            self._loggers[module_name] = logger
            
            # Performance tracking başlat
            self._init_performance_tracking(module_name)
            
            self._trigger_hooks("logger_created", {
                "module": module_name,
                "logger": logger,
                "config": config
            })
            
            return logger
    
    def _create_default_config(self, module_name: str) -> ModuleLoggerConfig:
        """Varsayılan modül yapılandırması oluştur"""
        return ModuleLoggerConfig(
            module_name=module_name,
            level="INFO",
            filename=f"logs/{module_name}.log"
        )
    
    def _create_logger_sync(self, module_name: str, config: ModuleLoggerConfig) -> AsyncLogger:
        """Yapılandırmaya göre logger oluştur - sync version"""
        if not config.enabled:
            # Disabled module - return no-op logger
            return self._create_noop_logger(module_name)
        
        logger = AsyncLogger(
            name=module_name,
            level=config.level,
            max_tasks=1000
        )
        
        # Clear default handlers
        logger.handlers.clear()
        
        # Configure based on strategy (sync version)
        self._configure_logger_by_strategy_sync(logger, config)
        
        return logger
    
    def _configure_logger_by_strategy_sync(self, logger: AsyncLogger, config: ModuleLoggerConfig) -> None:
        """Stratejiye göre logger yapılandır - sync version"""
        if self._strategy == LoggerStrategy.CENTRALIZED:
            self._configure_centralized(logger, config)
        elif self._strategy == LoggerStrategy.MODULE_BASED:
            self._configure_module_based_sync(logger, config)
        elif self._strategy == LoggerStrategy.HYBRID:
            self._configure_hybrid_sync(logger, config)
        else:  # CUSTOM
            self._configure_custom(logger, config)
    
    def _configure_centralized(self, logger: AsyncLogger, config: ModuleLoggerConfig) -> None:
        """Merkezi logging yapılandırması"""
        if not self._central_logger:
            self._central_logger = self._create_central_logger()
        
        # Copy central handlers
        for handler in self._central_logger.handlers:
            logger.add_handler(handler)
    
    def _configure_module_based_sync(self, logger: AsyncLogger, config: ModuleLoggerConfig) -> None:
        """Modül bazında logging yapılandırması - sync version using factory"""
        # Use handler factory to create standard handlers
        handlers = create_standard_handlers(
            filename=config.filename,
            file_level=config.level,
            file_formatter=config.file_formatter,
            console_output=config.console_output,
            console_level=config.console_level,
            console_formatter=config.console_formatter,
            max_size_mb=config.max_size_mb,
            max_files=config.max_files,
            queue_size=config.queue_size,
            queue_timeout=config.queue_timeout,
            worker_timeout=config.worker_timeout
        )
        
        # Add all handlers to logger
        for handler in handlers:
            logger.add_handler(handler)
    
    def _configure_hybrid_sync(self, logger: AsyncLogger, config: ModuleLoggerConfig) -> None:
        """Hibrit logging yapılandırması - sync version"""
        # First add central handlers
        self._configure_centralized(logger, config)
        
        # Then add module-specific handlers
        self._configure_module_based_sync(logger, config)
    
    def _configure_custom(self, logger: AsyncLogger, config: ModuleLoggerConfig) -> None:
        """Özel yapılandırma - hook sistemini kullan"""
        # Custom configuration through hooks
        self._trigger_hooks("custom_config", {
            "logger": logger,
            "config": config
        })
    
    def _create_central_logger(self) -> AsyncLogger:
        """Merkezi logger oluştur"""
        logger = AsyncLogger("miniflow_central")
        logger.handlers.clear()
        
        # Central file handler
        file_handler = RotatingFileHandler(
            filename="logs/miniflow.log",
            max_size_mb=100,
            max_files=10,
            level="INFO",
            formatter=JSONFormatter()
        )
        logger.add_handler(file_handler)
        
        # Central console handler
        console_handler = ConsoleHandler(
            level="ERROR",
            formatter=PlainTextFormatter()
        )
        logger.add_handler(console_handler)
        
        return logger
    
    def _create_noop_logger(self, module_name: str) -> AsyncLogger:
        """No-operation logger for disabled modules"""
        logger = AsyncLogger(f"{module_name}_disabled")
        logger.handlers.clear()  # No handlers = no output
        return logger
    
    def _reconfigure_logger_sync(self, logger: AsyncLogger, config: ModuleLoggerConfig) -> None:
        """Mevcut logger'ı yeniden yapılandır - sync version"""
        logger.handlers.clear()
        self._configure_logger_by_strategy_sync(logger, config)
    
    async def _reconfigure_all_loggers(self) -> None:
        """Tüm logger'ları yeniden yapılandır"""
        for module_name, logger in self._loggers.items():
            config = self._configs.get(module_name)
            if config:
                await self._configure_logger(module_name, config)
    
    def _init_performance_tracking(self, module_name: str) -> None:
        """Performance tracking başlat"""
        self._performance_stats[module_name] = {
            "created_at": time.time(),
            "log_count": 0,
            "error_count": 0,
            "last_log_time": None
        }
    
    def add_hook(self, event: str, callback: Callable) -> None:
        """Event hook ekle"""
        if event in self._hooks:
            self._hooks[event].add(callback)
    
    def remove_hook(self, event: str, callback: Callable) -> None:
        """Event hook kaldır"""
        if event in self._hooks:
            self._hooks[event].discard(callback)
    
    def _trigger_hooks(self, event: str, data: Dict[str, Any]) -> None:
        """Event hook'larını tetikle"""
        for callback in self._hooks.get(event, set()):
            try:
                callback(data)
            except Exception as e:
                # Don't let hook errors break logging
                handle_logging_error(e, f"Logger hook ({event})")
    
    def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        """Performance istatistiklerini al"""
        with self._lock:
            return self._performance_stats.copy()
    
    def enable_module(self, module_name: str) -> None:
        """Modül logging'ini etkinleştir"""
        with self._lock:
            if module_name in self._configs:
                self._configs[module_name].enabled = True
                self._configure_logger(module_name, self._configs[module_name])
    
    def disable_module(self, module_name: str) -> None:
        """Modül logging'ini devre dışı bırak"""
        with self._lock:
            if module_name in self._configs:
                self._configs[module_name].enabled = False
                self._configure_logger(module_name, self._configs[module_name])
    
    def list_modules(self) -> Dict[str, bool]:
        """Tüm modülleri ve durumlarını listele"""
        with self._lock:
            return {
                name: config.enabled 
                for name, config in self._configs.items()
            }
    
    async def shutdown_all(self) -> None:
        """Tüm logger'ları kapat"""
        with self._lock:
            loggers = list(self._loggers.values())
        
        for logger in loggers:
            try:
                await logger.shutdown()
            except Exception as e:
                handle_logging_error(e, "Logger shutdown")
        
        if self._central_logger:
            try:
                await self._central_logger.shutdown()
            except Exception as e:
                handle_logging_error(e, "Central logger shutdown")


# Global registry instance
_registry = LoggerRegistry()

# Alias for backward compatibility
LoggerConfig = ModuleLoggerConfig


# Public API functions
def set_logging_strategy(strategy: LoggerStrategy) -> None:
    """Global logging stratejisini ayarla"""
    _registry.set_strategy(strategy)


def register_module_config(config: ModuleLoggerConfig) -> None:
    """Modül yapılandırmasını kaydet"""
    _registry.register_module_config(config)


def get_module_logger(module_name: str) -> AsyncLogger:
    """Modül logger'ını al"""
    return _registry.get_logger(module_name)


def add_logger_hook(event: str, callback: Callable) -> None:
    """Logger event hook'u ekle"""
    _registry.add_hook(event, callback)


def get_logger_performance_stats() -> Dict[str, Dict[str, Any]]:
    """Logger performance istatistiklerini al"""
    return _registry.get_performance_stats()


def enable_module_logging(module_name: str) -> None:
    """Modül logging'ini etkinleştir"""
    _registry.enable_module(module_name)


def disable_module_logging(module_name: str) -> None:
    """Modül logging'ini devre dışı bırak"""
    _registry.disable_module(module_name)


async def shutdown_all_loggers() -> None:
    """Tüm logger'ları kapat"""
    await _registry.shutdown_all()
