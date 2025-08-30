import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Set

from .config import ErrorContext, ErrorSeverity, ErrorCode, ERROR_CODE_TO_STATUS


class MiniflowException(Exception):
    __slots__ = ['message', 'error_code', 'severity', 'details', 'context', 'source_error', 'status_code',
                 'timestamp', '_stack_trace', '_error_info_cache', '_chain_cache', 'max_chain_depth']

    def __init__(self,
                 message: str,
                 error_code: Optional[ErrorCode] = None,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 details: Optional[str] = None,
                 context: Optional[ErrorContext] = None,
                 source_error: Optional[Exception] = None,
                 ):

        # Input validation
        if not message or not isinstance(message, str):
            raise ValueError("Message must be a non-empty string")
        
        if not isinstance(severity, ErrorSeverity):
            raise ValueError("Severity must be an ErrorSeverity enum value")

        # Initialize super class - base Exception
        super().__init__(message)

        self.message = message
        self.error_code = error_code or ErrorCode.UNKNOWN_ERROR
        self.severity = severity
        self.details = details
        self.context = context
        self.source_error = source_error

        # Status code belirleme: önce parametre, sonra mapping, son olarak default
        self.status_code = ERROR_CODE_TO_STATUS.get(self.error_code, 500)

        self.timestamp = datetime.now(timezone.utc)
        self.max_chain_depth = 10

        # Stack trace'i hemen yakala (exception oluşturulduğu anda)
        self._capture_stack_trace()

        # Lazy evaluation attributes
        self._error_info_cache = None
        self._chain_cache = None

    def _capture_stack_trace(self) -> None:
        """Exception oluşturulduğu anda stack trace'i yakalar"""
        try:
            current_trace = traceback.format_exc()
            # Eğer gerçek bir exception context'i varsa kullan, yoksa None
            if current_trace and current_trace.strip() != 'NoneType: None':
                self._stack_trace = current_trace
            else:
                # Exception yaratılırken eğer context yoksa, stack'i manuel oluştur
                self._stack_trace = ''.join(traceback.format_stack()[:-1])  # Son frame'i çıkar
        except Exception:
            self._stack_trace = "Stack trace capture failed"

    @property
    def stack_trace(self) -> Optional[str]:
        """Stack trace'i döndürür (readonly)"""
        return self._stack_trace

    def get_error_info(self) -> Dict[str, Any]:
        """Hata bilgilerini dictionary olarak döndürür (cached)"""
        if self._error_info_cache is None:
            error_info = {
                "error_code": self.error_code.value if self.error_code else "UNKNOWN",
                "message": self.message,
                "severity": self.severity.value if self.severity else "MEDIUM",
                "status_code": self.status_code,
                "timestamp": self.timestamp.isoformat() + "Z",
                "exception_type": self.__class__.__name__
            }

            if self.details is not None:
                error_info["details"] = self.details

            if self.context:
                try:
                    # to_dict metodunun varlığını kontrol et
                    if hasattr(self.context, 'to_dict') and callable(self.context.to_dict):
                        error_info["context"] = self.context.to_dict()
                    else:
                        # to_dict yoksa string representation kullan
                        error_info["context"] = str(self.context)
                except Exception as e:
                    error_info["context"] = f"Context serialization failed: {str(e)}"

            if self.source_error:
                error_info["source_error"] = {
                    "type": type(self.source_error).__name__,
                    "message": str(self.source_error)
                }

            if self.stack_trace:
                error_info["stack_trace"] = self.stack_trace

            self._error_info_cache = error_info

        return self._error_info_cache

    def get_error_chain(self) -> List[Dict[str, Any]]:
        """Hata zincirini döndürür (döngüsel referans korumalı)"""
        if self._chain_cache is not None:
            return self._chain_cache

        chain = [self.get_error_info()]
        seen_errors: Set[int] = {id(self)}  # Döngüsel referans koruması
        depth = 1

        current_error = self.source_error
        while current_error and depth < self.max_chain_depth:
            # Döngüsel referans kontrolü
            error_id = id(current_error)
            if error_id in seen_errors:
                chain.append({
                    "type": "CircularReference",
                    "message": f"Circular reference detected to {type(current_error).__name__}",
                    "timestamp": self.timestamp.isoformat() + "Z"
                })
                break

            seen_errors.add(error_id)

            if hasattr(current_error, 'get_error_info'):
                chain.append(current_error.get_error_info())
                # Bir sonraki hataya geç
                if hasattr(current_error, 'source_error'):
                    current_error = current_error.source_error
                else:
                    break
            else:
                # Standart exception
                chain.append({
                    "type": type(current_error).__name__,
                    "message": str(current_error),
                    "timestamp": self.timestamp.isoformat() + "Z"
                })
                # Standart exception'lar için source_error yoktur
                break

            depth += 1

        self._chain_cache = chain
        return chain

    def get_readable_chain(self) -> str:
        """İnsan tarafından okunabilir hata zinciri"""
        chain_parts = [f"{self.__class__.__name__}: {self.message}"]
        seen_errors: Set[int] = {id(self)}
        depth = 1

        current_error = self.source_error
        while current_error and depth < self.max_chain_depth:
            error_id = id(current_error)
            if error_id in seen_errors:
                chain_parts.append(f"[Circular Reference to {type(current_error).__name__}]")
                break

            seen_errors.add(error_id)

            if isinstance(current_error, MiniflowException):
                # DetailedException ise recursive olarak zincirini al
                nested_chain = current_error.get_readable_chain()
                chain_parts.append(nested_chain)
                break  # Nested chain zaten tüm alt zincirleri içeriyor
            else:
                # Standart exception
                chain_parts.append(f"{type(current_error).__name__}: {str(current_error)}")
                # Standart exception'lar için __cause__ veya __context__ kontrol edilebilir
                if hasattr(current_error, '__cause__') and current_error.__cause__:
                    current_error = current_error.__cause__
                elif hasattr(current_error, '__context__') and current_error.__context__:
                    current_error = current_error.__context__
                else:
                    break

            depth += 1

        return " <- ".join(chain_parts)

    def __str__(self) -> str:
        """String representation with error code"""
        error_code_str = self.error_code.value if self.error_code else "UNKNOWN"
        return f"[{error_code_str}] {self.message}"

    def __repr__(self) -> str:
        """Detailed representation"""
        error_code_str = self.error_code.value if self.error_code else "UNKNOWN"
        return f"{self.__class__.__name__}(message='{self.message}', error_code='{error_code_str}')"


def create_miniflow_exception(message: str,
                              error_code: Optional[ErrorCode] = None,
                              severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                              details: Optional[str] = None,
                              context: Optional[ErrorContext] = None,
                              source_error: Optional[Exception] = None,
                              status_code: Optional[int] = None
                              ) -> MiniflowException:
    """Create a detailed exception with full features

    Args:
        message: Ana hata mesajı
        error_code: Hata kodu (None ise UNKNOWN_ERROR kullanılır)
        severity: Hata önem derecesi
        details: Ek detaylar
        context: Hata bağlamı
        source_error: Kaynak hata (chaining için)
        status_code: HTTP durum kodu (None ise error_code'dan mapping yapılır)

    Returns:
        MiniflowException instance
    """
    exception = MiniflowException(
        message=message,
        error_code=error_code,
        severity=severity,
        details=details,
        context=context,
        source_error=source_error
    )
    
    # Eğer status_code parametre olarak verilmişse override et
    if status_code is not None:
        exception.status_code = status_code
        
    return exception