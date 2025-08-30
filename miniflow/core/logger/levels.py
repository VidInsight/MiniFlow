"""
Log levels for MiniFlow logging system
"""

from enum import Enum


class LogLevel(Enum):
    """Log seviyeleri"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    
    @classmethod
    def from_string(cls, level_str: str) -> 'LogLevel':
        """String'den LogLevel oluştur"""
        level_map = {
            'debug': cls.DEBUG,
            'info': cls.INFO,
            'warning': cls.WARNING,
            'warn': cls.WARNING,
            'error': cls.ERROR,
            'critical': cls.CRITICAL
        }
        return level_map.get(level_str.lower(), cls.INFO)
