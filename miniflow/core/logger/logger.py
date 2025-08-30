"""
Async JSON Logger for MiniFlow with correlation ID support.
Optimized for large-scale production use.
"""

import asyncio
import threading
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional, Union, Set

from .context import get_correlation_id, ensure_correlation_id
from .formatters import JSONFormatter
from .utils import handle_logging_error, get_context_mode, SimpleCircuitBreaker
from .levels import LogLevel


class LogRecord:
    """Log record - JSON formatında log mesajını temsil eder"""
    
    def __init__(
        self,
        level: Union[LogLevel, str],
        message: str,
        logger_name: str,
        timestamp: Optional[datetime] = None,
        thread_id: Optional[int] = None,
        correlation_id: Optional[str] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
        exception_info: Optional[tuple] = None
    ):
        self.level = LogLevel.from_string(level) if isinstance(level, str) else level
        self.message = message
        self.timestamp = timestamp or datetime.utcnow()
        self.logger_name = logger_name
        self.thread_id = thread_id or threading.get_ident()
        self.correlation_id = correlation_id or get_correlation_id()
        self.extra_fields = extra_fields or {}
        self.exception_info = exception_info
    
    def to_dict(self) -> Dict[str, Any]:
        """Log record'ı dict'e çevir"""
        record = {
            'level': self.level.name,
            'level_value': self.level.value,
            'message': self.message,
            'timestamp': self.timestamp,
            'logger_name': self.logger_name,
            'thread_id': self.thread_id,
            'correlation_id': self.correlation_id,
            **self.extra_fields
        }
        
        # Exception bilgilerini ekle
        if self.exception_info:
            formatter = JSONFormatter()
            exception_data = formatter.format_exception(self.exception_info)
            record.update(exception_data)
        
        return record





class AsyncLogger:
    """
    Asenkron JSON logger with correlation ID support
    Optimized for large-scale production use
    
    Features:
    - JSON structured logging
    - Correlation ID integration
    - Async file writing
    - Rotating file handler
    - Configurable log levels
    - Thread-safe context detection
    - Memory leak prevention
    - Circuit breaker pattern
    """
    
    def __init__(
        self,
        name: str,
        level: Union[LogLevel, str] = LogLevel.INFO,
        handlers: Optional[list] = None,
        formatter: Optional[JSONFormatter] = None,
        max_tasks: int = 1000
    ):
        """
        Args:
            name: Logger adı
            level: Minimum log seviyesi
            handlers: Log handler'ları listesi
            formatter: Log formatter
        """
        self.name = name
        self.level = LogLevel.from_string(level) if isinstance(level, str) else level
        self.handlers = handlers if handlers is not None else []
        self.formatter = formatter or JSONFormatter()
        self.max_tasks = max_tasks

        # Per-handler async locks to reduce contention
        self._handler_locks: Dict[Any, asyncio.Lock] = {}

        # Track background tasks to avoid leaks
        self._active_tasks: Set[asyncio.Task] = set()
        self._task_lock = threading.Lock()
        
        # Circuit breaker for resilience
        self._circuit_breaker = SimpleCircuitBreaker()
        
        # Default handler ekle (sadece handlers=None olduğunda ve miniflow_central değilse)
        if handlers is None and not name.startswith("miniflow_central"):
            self._add_default_handlers(name)
    
    def _get_handler_lock(self, handler) -> asyncio.Lock:
        """Get or create an async lock for a specific handler."""
        if handler not in self._handler_locks:
            self._handler_locks[handler] = asyncio.Lock()
        return self._handler_locks[handler]

    def _track_task(self, task: asyncio.Task) -> None:
        """Robust task tracking with fallback strategies to prevent memory leaks."""
        if self.max_tasks <= 0:
            return
        
        # Strategy 1: Try immediate tracking
        acquired = self._task_lock.acquire(False)
        if acquired:
            try:
                self._cleanup_completed_tasks()
                if len(self._active_tasks) < self.max_tasks:
                    self._active_tasks.add(task)
                    task.add_done_callback(self._on_task_done)
                else:
                    # Strategy 2: Force cleanup oldest tasks
                    self._force_cleanup_old_tasks(10)
                    self._active_tasks.add(task)
                    task.add_done_callback(self._on_task_done)
            finally:
                self._task_lock.release()
        else:
            # Strategy 3: Defer tracking to background
            self._defer_task_tracking(task)

    def _cleanup_completed_tasks(self):
        """Efficient cleanup of completed tasks."""
        self._active_tasks = {t for t in self._active_tasks if not t.done()}

    def _force_cleanup_old_tasks(self, count: int):
        """Forcefully cancel oldest tasks to prevent memory leaks."""
        tasks_to_cancel = list(self._active_tasks)[:count]
        for task in tasks_to_cancel:
            task.cancel()
            self._active_tasks.discard(task)

    def _defer_task_tracking(self, task: asyncio.Task):
        """Fallback: minimal tracking without lock to prevent memory leaks."""
        # Best effort cleanup callback to prevent basic leak
        task.add_done_callback(lambda t: None)

    def _on_task_done(self, task: asyncio.Task) -> None:
        """Cleanup callback when a tracked task finishes."""
        with self._task_lock:
            self._active_tasks.discard(task)
    
    def add_handler(self, handler) -> None:
        """Handler ekle"""
        if handler not in self.handlers:
            self.handlers.append(handler)
    
    def remove_handler(self, handler) -> None:
        """Handler kaldır"""
        if handler in self.handlers:
            self.handlers.remove(handler)
        # Remove per-handler lock if exists
        self._handler_locks.pop(handler, None)
    
    def clear_handlers(self) -> None:
        """Tüm handler'ları temizle"""
        self.handlers.clear()
        # Clear all per-handler locks
        self._handler_locks.clear()
    
    def set_level(self, level: Union[LogLevel, str]) -> None:
        """Log seviyesini ayarla"""
        self.level = LogLevel.from_string(level) if isinstance(level, str) else level
    
    def is_enabled_for(self, level: LogLevel) -> bool:
        """Belirli seviye için logging aktif mi?"""
        return level.value >= self.level.value
    
    def _add_default_handlers(self, name: str) -> None:
        """Default handler'ları ekle"""
        # Import'ları burada yap (circular import'u önlemek için)
        from .handlers import ConsoleHandler, RotatingFileHandler
        
        # Console handler
        console_handler = ConsoleHandler()
        self.add_handler(console_handler)
        
        # File handler (size-based rotation)
        file_handler = RotatingFileHandler(
            filename=f"logs/miniflow_{name}.log",
            max_size_mb=100,
            max_files=5
        )
        self.add_handler(file_handler)
    
    def _create_log_record(
        self,
        level: LogLevel,
        message: str,
        extra_fields: Optional[Dict[str, Any]] = None,
        exception_info: Optional[tuple] = None,
        logger_name: Optional[str] = None
    ) -> LogRecord:
        """Ortak log record oluşturma metodu"""
        if not self.is_enabled_for(level):
            return None
        
        # Correlation ID'yi garanti et
        ensure_correlation_id()
        
        # Log record oluştur (logger_name override edilebilir)
        return LogRecord(
            level=level,
            message=message,
            logger_name=logger_name or self.name,
            extra_fields=extra_fields,
            exception_info=exception_info
        )
    

    
    async def _send_to_handler(self, handler, formatted_message: str) -> None:
        """Send message with robust error handling and lock management."""
        lock = self._get_handler_lock(handler)
        timeout = getattr(handler, 'emit_timeout', 2.0)
        
        try:
            # Use wait_for for Python 3.10 compatibility
            async with lock:
                await asyncio.wait_for(
                    handler.emit(formatted_message), 
                    timeout=timeout
                )
        except asyncio.TimeoutError:
            # Lock automatically released by context manager
            handle_logging_error(
                TimeoutError(f"Handler timeout: {timeout}s"), 
                f"Handler ({handler.__class__.__name__})"
            )
            # Consider marking handler as failed
            self._mark_handler_failed(handler)
        except Exception as e:
            handle_logging_error(e, f"Handler ({handler.__class__.__name__})")
            self._mark_handler_failed(handler)

    def _mark_handler_failed(self, handler):
        """Mark handler as temporarily failed."""
        if not hasattr(self, '_failed_handlers'):
            self._failed_handlers = {}
        
        self._failed_handlers[handler] = time.time()
        
        # Auto-recovery after 60 seconds
        asyncio.create_task(self._recover_handler(handler, 60))

    async def _recover_handler(self, handler, delay: float):
        """Attempt to recover a failed handler."""
        await asyncio.sleep(delay)
        self._failed_handlers.pop(handler, None)

    def _send_to_handler_sync(self, handler, formatted_message: str) -> None:
        """Send a formatted message to a handler synchronously (best-effort)."""
        try:
            if hasattr(handler, 'emit_sync'):
                handler.emit_sync(formatted_message)
            else:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(handler.emit(formatted_message))
                    else:
                        loop.run_until_complete(handler.emit(formatted_message))
                except RuntimeError:
                    pass
        except Exception as e:
            handle_logging_error(e, f"Handler sync ({handler.__class__.__name__})")

    def _format_and_send_to_handlers(self, record: LogRecord, use_sync: bool = False) -> None:
        """Log record'ı formatla ve handler'lara gönder (reduced contention)."""
        if record is None:
            return
        
        # Tüm handler'lara gönder
        for handler in self.handlers:
            try:
                # Handler level filtresi
                handler_level = getattr(handler, 'level', None)
                if handler_level is not None and record.level.value < handler_level.value:
                    continue

                # Handler bazlı formatter seçimi
                formatter = getattr(handler, 'formatter', None) or self.formatter
                formatted_message = formatter.format(record.to_dict())

                if use_sync:
                    self._send_to_handler_sync(handler, formatted_message)
                else:
                    # Async: schedule and track to avoid leaks
                    try:
                        loop = asyncio.get_running_loop()
                        task = loop.create_task(self._send_to_handler(handler, formatted_message))
                        self._track_task(task)
                    except RuntimeError:
                        # No loop: fallback to sync path
                        self._send_to_handler_sync(handler, formatted_message)
            except Exception as e:
                # Robust error handling
                handle_logging_error(e, f"Handler ({handler.__class__.__name__})")
    
    async def _log_async(
        self,
        level: LogLevel,
        message: str,
        extra_fields: Optional[Dict[str, Any]] = None,
        exception_info: Optional[tuple] = None,
        logger_name: Optional[str] = None
    ) -> None:
        """Async log metodu"""
        record = self._create_log_record(level, message, extra_fields, exception_info, logger_name)
        if record:
            # No global lock: reduce contention
            self._format_and_send_to_handlers(record, use_sync=False)
    
    def _log_sync(
        self,
        level: LogLevel,
        message: str,
        extra_fields: Optional[Dict[str, Any]] = None,
        exception_info: Optional[tuple] = None,
        logger_name: Optional[str] = None
    ) -> None:
        """Sync log metodu"""
        record = self._create_log_record(level, message, extra_fields, exception_info, logger_name)
        if record:
            self._format_and_send_to_handlers(record, use_sync=True)
    


    # Simplified logging methods - dynamic context detection
    def _create_log_method(self, level: LogLevel):
        """Log seviyesi için metod oluştur - optimized context detection with circuit breaker"""
        def log_func(message: str, **kwargs):
            # Circuit breaker check
            if not self._circuit_breaker.should_allow():
                return  # Skip logging if circuit is open
            
            # Extract special kwargs
            logger_name = kwargs.pop('logger_name', None)
            exception_info = kwargs.pop('exception_info', None)
            
            try:
                # Optimized context detection with thread-local caching
                if get_context_mode():
                    try:
                        loop = asyncio.get_running_loop()
                        task = loop.create_task(self._log_async(level, message, kwargs, exception_info, logger_name))
                        self._track_task(task)
                        self._circuit_breaker.record_success()
                    except Exception as e:
                        # Fallback to sync on error
                        handle_logging_error(e, "Async logging fallback")
                        self._log_sync(level, message, kwargs, exception_info, logger_name)
                        self._circuit_breaker.record_failure()
                else:
                    # Sync context
                    self._log_sync(level, message, kwargs, exception_info, logger_name)
                    self._circuit_breaker.record_success()
            except Exception as e:
                self._circuit_breaker.record_failure()
                handle_logging_error(e, "Logging failed")
        return log_func

    # Log metodları - simplified
    @property
    def debug(self):
        return self._create_log_method(LogLevel.DEBUG)
    
    @property
    def info(self):
        return self._create_log_method(LogLevel.INFO)
    
    @property
    def warning(self):
        return self._create_log_method(LogLevel.WARNING)
    
    @property
    def error(self):
        return self._create_log_method(LogLevel.ERROR)
    
    @property
    def critical(self):
        return self._create_log_method(LogLevel.CRITICAL)

    # Exception metodları
    def exception(self, message: str, **kwargs) -> None:
        # Circuit breaker check
        if not self._circuit_breaker.should_allow():
            return  # Skip logging if circuit is open
        
        exc_info = sys.exc_info()
        kwargs['exception_info'] = exc_info
        
        try:
            # Use the same optimized context detection logic
            if get_context_mode():
                try:
                    loop = asyncio.get_running_loop()
                    task = loop.create_task(self._log_async(LogLevel.ERROR, message, kwargs))
                    self._track_task(task)
                    self._circuit_breaker.record_success()
                except Exception as e:
                    handle_logging_error(e, "Exception logging fallback")
                    self._log_sync(LogLevel.ERROR, message, kwargs)
                    self._circuit_breaker.record_failure()
            else:
                self._log_sync(LogLevel.ERROR, message, kwargs)
                self._circuit_breaker.record_success()
        except Exception as e:
            self._circuit_breaker.record_failure()
            handle_logging_error(e, "Exception logging failed")
    
    async def shutdown(self) -> None:
        """Logger'ı kapat - tüm handler'ları durdur"""
        # Cancel and await tracked tasks
        with self._task_lock:
            tasks = list(self._active_tasks)
            self._active_tasks.clear()
        if tasks:
            for t in tasks:
                if not t.done():
                    t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

        # Stop handlers
        for handler in self.handlers:
            try:
                await handler.stop()
            except Exception as e:
                handle_logging_error(e, f"Handler shutdown ({handler.__class__.__name__})")
    
    def __del__(self):
        """Destructor - cleanup"""
        try:
            # Python shutdown sırasında asyncio kullanma
            if not sys.meta_path:  # Python shutting down
                return
                
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.shutdown())
        except (RuntimeError, ImportError):
            pass  # Event loop yok veya Python shutting down
