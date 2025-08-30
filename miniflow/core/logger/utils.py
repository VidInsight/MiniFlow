"""
Logger utilities - Common functions and error handling
"""

import sys
import asyncio
import threading
import time
from typing import Optional


def handle_logging_error(error: Exception, context: str) -> None:
    """Centralized error handling for logger operations"""
    try:
        print(f"[LOGGER ERROR] {context}: {error}", file=sys.stderr, flush=True)
    except Exception:
        # Last resort - don't crash the app
        pass


def get_context_mode() -> bool:
    """Simplified async context detection with thread-local caching"""
    thread_local = threading.local()
    
    # Check cache
    if hasattr(thread_local, 'is_async'):
        return thread_local.is_async
    
    # Detect and cache
    try:
        asyncio.get_running_loop()
        thread_local.is_async = True
        return True
    except RuntimeError:
        thread_local.is_async = False
        return False


def reset_context_cache():
    """Reset context cache for current thread"""
    thread_local = threading.local()
    if hasattr(thread_local, 'is_async'):
        delattr(thread_local, 'is_async')


class SimpleCircuitBreaker:
    """Simplified circuit breaker for logger resilience"""
    
    def __init__(self, failure_threshold: int = 10, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN
        self._lock = threading.Lock()
    
    def should_allow(self) -> bool:
        """Check if operation should be allowed"""
        with self._lock:
            if self.state == "CLOSED":
                return True
            elif self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "CLOSED"
                    self.failure_count = 0
                    return True
                return False
    
    def record_success(self):
        """Record successful operation"""
        with self._lock:
            if self.state == "OPEN":
                self.state = "CLOSED"
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed operation"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
