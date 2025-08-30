"""
Log formatters for MiniFlow logging system.
"""

import json
import threading
from datetime import datetime
from typing import Any, Dict, Optional
from .context import get_correlation_id


class BaseFormatter:
    """Base formatter - ortak field processing logic"""
    
    def __init__(self, include_timestamp: bool = True, include_thread: bool = True):
        self.include_timestamp = include_timestamp
        self.include_thread = include_thread
    
    def _process_fields(self, log_record: Dict[str, Any]) -> Dict[str, Any]:
        """Ortak field processing logic"""
        formatted_record = {}
        
        # Temel alanları kopyala
        for key, value in log_record.items():
            if value is not None:
                formatted_record[key] = value
        
        # Timestamp'i ISO formatında ekle
        if self.include_timestamp and 'timestamp' in formatted_record:
            if isinstance(formatted_record['timestamp'], datetime):
                formatted_record['timestamp'] = formatted_record['timestamp'].isoformat()
        
        # Thread ID'yi ekle
        if self.include_thread and 'thread_id' in formatted_record:
            formatted_record['thread_id'] = str(formatted_record['thread_id'])
        
        # Correlation ID'yi otomatik ekle (eğer yoksa)
        if 'correlation_id' not in formatted_record:
            correlation_id = get_correlation_id()
            if correlation_id:
                formatted_record['correlation_id'] = correlation_id
        
        return formatted_record


class JSONFormatter(BaseFormatter):
    """JSON formatında log mesajlarını formatlar"""
    def __init__(self, include_timestamp: bool = True, include_thread: bool = True):
        super().__init__(include_timestamp=include_timestamp, include_thread=include_thread)

    def format(self, log_record: Dict[str, Any]) -> str:
        """
        Log record'ı JSON formatına çevirir
        
        Args:
            log_record: Formatlanacak log record
            
        Returns:
            JSON string
        """
        formatted_record = self._process_fields(log_record)
        return json.dumps(formatted_record, ensure_ascii=False, default=str)
    
    def format_exception(self, exc_info: tuple) -> Dict[str, Any]:
        """
        Exception bilgilerini formatlar
        
        Args:
            exc_info: (type, value, traceback) tuple
            
        Returns:
            Exception bilgilerini içeren dict
        """
        if not exc_info or exc_info == (None, None, None):
            return {}
            
        exc_type, exc_value, exc_traceback = exc_info
        
        return {
            'exception_type': exc_type.__name__ if exc_type else None,
            'exception_message': str(exc_value) if exc_value else None,
            'exception_traceback': self._format_traceback(exc_traceback) if exc_traceback else None
        }
    
    def _format_traceback(self, traceback) -> str:
        """Traceback'i string formatına çevirir"""
        import traceback as tb
        return ''.join(tb.format_tb(traceback))


class PlainTextFormatter(BaseFormatter):
    """Düz metin formatında log mesajlarını formatlar"""

    def __init__(self, include_timestamp: bool = True):
        super().__init__(include_timestamp=include_timestamp, include_thread=False)

    def format(self, log_record: Dict[str, Any]) -> str:
        # Base formatter'dan field processing'i kullan
        processed_record = self._process_fields(log_record)
        
        parts = []
        ts = processed_record.get('timestamp')
        if self.include_timestamp and ts is not None:
            if isinstance(ts, datetime):
                parts.append(ts.isoformat())
            else:
                parts.append(str(ts))
        level = processed_record.get('level')
        if level:
            parts.append(str(level))
        logger_name = processed_record.get('logger_name')
        if logger_name:
            parts.append(str(logger_name))
        message = processed_record.get('message', '')
        header = ' '.join(parts)

        # Kalan alanları kompakt olarak ekle (temel anahtarlar hariç)
        extras = {k: v for k, v in processed_record.items() if k not in {
            'timestamp', 'level', 'level_value', 'logger_name', 'message'
        } and v is not None}

        extras_str = ''
        if extras:
            try:
                # Basit anahtar=değer çiftleri
                extras_str = ' ' + ' '.join(f"{k}={v}" for k, v in extras.items())
            except Exception:
                extras_str = ''

        return f"{header} - {message}{extras_str}"
