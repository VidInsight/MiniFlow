import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from miniflow.core.logger import get_logger
from miniflow.core.logger.context import get_correlation_id


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/Response logging middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("miniflow_api")
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Request logging
        if self.logger:
            self.logger.info(
                "API Request",
                extra={
                    "request_method": request.method,
                    "request_url": str(request.url),
                    "request_headers": dict(request.headers),
                    "correlation_id": get_correlation_id(),
                    "client_ip": request.client.host if request.client else None
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Response logging
        if self.logger:
            self.logger.info(
                "API Response",
                extra={
                    "response_status": response.status_code,
                    "process_time": round(process_time, 4),
                    "correlation_id": get_correlation_id()
                }
            )
        
        return response