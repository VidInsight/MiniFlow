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
from .formatters import JSONFormatter, PlainTextFormatter
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
        try:
            with self._task_lock:
                if len(self._active_tasks) < self.max_tasks:
                    self._active_tasks.add(task)
                    task.add_done_callback(self._on_task_done)
                else:
                    # Too many tasks: cleanup old done tasks
                    done_tasks = {t for t in self._active_tasks if t.done()}
                    self._active_tasks.difference_update(done_tasks)
                    
                    # If still too many, drop this task (avoid memory leak)
                    if len(self._active_tasks) < self.max_tasks:
                        self._active_tasks.add(task)
                        task.add_done_callback(self._on_task_done)
                    else:
                        # Cancel to avoid leak
                        task.cancel()
        except Exception:
            # Fail-safe: avoid breaking logging
            pass

    async def _send_to_handler(self, handler, formatted_message: str) -> None:
        """Handler'a async mesaj gönder."""
        try:
            handler_lock = self._get_handler_lock(handler)
            async with handler_lock:
                # Use sync emit for thread safety
                if hasattr(handler, 'emit_sync'):
                    handler.emit_sync(formatted_message)
                elif hasattr(handler, 'emit'):
                    await handler.emit(formatted_message)
                else:
                    # Fallback
                    print(formatted_message)
        except Exception as e:
            handle_logging_error(e, f"Handler async ({handler.__class__.__name__})")

    def _on_task_done(self, task: asyncio.Task) -> None:
        """Task completion callback to remove from tracking."""
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
        
        # Console handler with PlainTextFormatter (fixed)
        console_handler = ConsoleHandler(formatter=PlainTextFormatter())
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
        """Create a log record with context information."""
        ensure_correlation_id()
        
        return LogRecord(
            level=level,
            message=message,
            logger_name=logger_name or self.name,
            extra_fields=extra_fields,
            exception_info=exception_info
        )

    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged (level filter + circuit breaker)."""
        # Level check
        if not self.is_enabled_for(level):
            return False
        
        # Circuit breaker check
        if not self._circuit_breaker.should_allow():
            return False
        
        return True

    def _send_to_handler_sync(self, handler, formatted_message: str) -> None:
        """Handler'a sync mesaj gönder (improved error handling)."""
        try:
            # Thread-safe sync emit
            if hasattr(handler, 'emit_sync'):
                handler.emit_sync(formatted_message)
            elif hasattr(handler, 'emit'):
                # Async emit in sync context (fallback)
                asyncio.create_task(handler.emit(formatted_message))
            else:
                # Final fallback
                print(formatted_message)

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
        """Async logging implementation (core method)."""
        try:
            if not self._should_log(level):
                return

            record = self._create_log_record(
                level=level,
                message=message,
                extra_fields=extra_fields,
                exception_info=exception_info,
                logger_name=logger_name
            )

            self._format_and_send_to_handlers(record, use_sync=False)
            
            # Circuit breaker success
            self._circuit_breaker.record_success()
            
        except Exception as e:
            # Circuit breaker failure
            self._circuit_breaker.record_failure()
            handle_logging_error(e, "AsyncLogger._log_async")

    def _log_sync(
        self,
        level: LogLevel,
        message: str,
        extra_fields: Optional[Dict[str, Any]] = None,
        exception_info: Optional[tuple] = None,
        logger_name: Optional[str] = None
    ) -> None:
        """Sync logging implementation (performance optimized)."""
        try:
            if not self._should_log(level):
                return

            record = self._create_log_record(
                level=level,
                message=message,
                extra_fields=extra_fields,
                exception_info=exception_info,
                logger_name=logger_name
            )

            self._format_and_send_to_handlers(record, use_sync=True)
            
            # Circuit breaker success
            self._circuit_breaker.record_success()
            
        except Exception as e:
            # Circuit breaker failure
            self._circuit_breaker.record_failure()
            handle_logging_error(e, "AsyncLogger._log_sync")

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Debug level log"""
        if get_context_mode() == "async":
            asyncio.create_task(self._log_async(LogLevel.DEBUG, message, extra))
        else:
            self._log_sync(LogLevel.DEBUG, message, extra)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Info level log"""
        if get_context_mode() == "async":
            asyncio.create_task(self._log_async(LogLevel.INFO, message, extra))
        else:
            self._log_sync(LogLevel.INFO, message, extra)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Warning level log"""
        if get_context_mode() == "async":
            asyncio.create_task(self._log_async(LogLevel.WARNING, message, extra))
        else:
            self._log_sync(LogLevel.WARNING, message, extra)

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: Optional[tuple] = None) -> None:
        """Error level log"""
        if get_context_mode() == "async":
            asyncio.create_task(self._log_async(LogLevel.ERROR, message, extra, exc_info))
        else:
            self._log_sync(LogLevel.ERROR, message, extra, exc_info)

    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: Optional[tuple] = None) -> None:
        """Critical level log"""
        if get_context_mode() == "async":
            asyncio.create_task(self._log_async(LogLevel.CRITICAL, message, extra, exc_info))
        else:
            self._log_sync(LogLevel.CRITICAL, message, extra, exc_info)

    def exception(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Exception level log (same as error but with automatic exception info)"""
        exc_info = sys.exc_info() if sys.exc_info()[0] is not None else None
        self.error(message, extra, exc_info)

    async def shutdown(self) -> None:
        """Async cleanup of resources."""
        try:
            # Wait for all pending tasks with timeout
            if self._active_tasks:
                await asyncio.wait_for(
                    asyncio.gather(*self._active_tasks, return_exceptions=True),
                    timeout=5.0
                )
        except asyncio.TimeoutError:
            # Cancel remaining tasks
            for task in self._active_tasks:
                task.cancel()
        finally:
            # Clear resources
            self._active_tasks.clear()
            self._handler_locks.clear()