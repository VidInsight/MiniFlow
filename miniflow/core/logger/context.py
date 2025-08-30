import uuid
import threading
import functools
from typing import Optional, Callable, Any
from contextlib import contextmanager


class CorrelationContext:
    """Thread-local correlation ID storage"""

    def __init__(self):
        self._local = threading.local()

    def get_id(self) -> Optional[str]:
        """Mevcut correlation ID'yi döndür"""
        try:
            return getattr(self._local, 'correlation_id', None)
        except AttributeError:
            return None

    def set_id(self, correlation_id: str) -> None:
        """Correlation ID'yi ayarla"""
        if not isinstance(correlation_id, str):
            raise ValueError("Correlation ID must be a string")
        if not correlation_id.strip():  # Empty/whitespace check
            raise ValueError("Correlation ID cannot be empty")
        self._local.correlation_id = correlation_id

    def clear(self) -> None:
        """Correlation ID'yi temizle"""
        try:
            delattr(self._local, 'correlation_id')
        except AttributeError:
            pass

    def has_id(self) -> bool:
        """Correlation ID'nin var olup olmadığını kontrol et"""
        return hasattr(self._local, 'correlation_id')


# Global context instance
_context = CorrelationContext()


def get_correlation_id() -> Optional[str]:
    """Mevcut thread'deki correlation ID'yi döndür"""
    return _context.get_id()


def set_correlation_id(correlation_id: str) -> None:
    """Correlation ID'yi ayarla"""
    _context.set_id(correlation_id)


def generate_correlation_id() -> str:
    """Yeni bir correlation ID oluştur"""
    return str(uuid.uuid4())


def has_correlation_id() -> bool:
    """Correlation ID'nin var olup olmadığını kontrol et"""
    return _context.has_id()


def with_correlation_id(func: Callable = None, *, preserve_changes: bool = False) -> Callable:
    """
    Decorator: Fonksiyona otomatik correlation ID atar

    Args:
        preserve_changes: True ise fonksiyon içindeki ID değişiklikleri korunur

    Usage:
        @with_correlation_id
        def handle_request():
            logger.info("Request started")  # Otomatik correlation ID

        @with_correlation_id(preserve_changes=True)
        def handle_with_changes():
            set_correlation_id("custom-id")  # Bu korunacak
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Mevcut correlation ID'yi sakla
            original_id = get_correlation_id()
            had_original_id = has_correlation_id()

            # Eğer correlation ID yoksa yeni oluştur
            if not had_original_id:
                set_correlation_id(generate_correlation_id())

            try:
                result = fn(*args, **kwargs)

                # preserve_changes=True ise mevcut ID'yi koru
                if preserve_changes and had_original_id:
                    return result

                return result
            finally:
                # Orijinal context'i geri yükle (preserve_changes=False ise)
                if not preserve_changes:
                    if had_original_id:
                        set_correlation_id(original_id)
                    else:
                        _context.clear()

        return wrapper

    # Decorator'ın hem @with_correlation_id hem de @with_correlation_id() şeklinde kullanımını destekle
    if func is None:
        return decorator
    else:
        return decorator(func)


@contextmanager
def correlation_context(correlation_id: Optional[str] = None):
    """
    Context manager: Belirli bir correlation ID ile çalışma

    Usage:
        with correlation_context("req-123"):
            logger.info("Processing")  # "req-123" correlation ID ile

        with correlation_context():  # Auto-generate
            logger.info("Processing")  # Auto-generated correlation ID ile
    """
    original_id = get_correlation_id()
    had_original_id = has_correlation_id()

    if correlation_id is None:
        correlation_id = generate_correlation_id()

    set_correlation_id(correlation_id)

    try:
        yield correlation_id
    finally:
        # Orijinal context'i geri yükle
        if had_original_id:
            set_correlation_id(original_id)
        else:
            _context.clear()

# Utility functions
def ensure_correlation_id() -> str:
    """Correlation ID'nin var olduğunu garanti et, yoksa oluştur"""
    correlation_id = get_correlation_id()
    if correlation_id is None:
        correlation_id = generate_correlation_id()
        set_correlation_id(correlation_id)
    return correlation_id