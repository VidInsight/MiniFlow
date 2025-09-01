"""
Correlation ID Middleware
FastAPI için Correlation ID middleware
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from miniflow.core.logger.context import (
    set_correlation_id,
    generate_correlation_id
)


class CorrelationMiddleware(BaseHTTPMiddleware):
    """FastAPI için Correlation ID middleware"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Request'ten correlation ID al veya oluştur
        correlation_id = (
            request.headers.get("X-Correlation-ID") or
            request.headers.get("X-Request-ID") or
            generate_correlation_id()
        )
        
        # Context'e set et
        set_correlation_id(correlation_id)
        
        # Request'e ekle (endpoint'lerde kullanım için)
        request.state.correlation_id = correlation_id
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Response header'larına ekle
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


async def get_current_correlation_id(request: Request) -> str:
    """Get current correlation ID from request state"""
    return getattr(request.state, 'correlation_id', generate_correlation_id())