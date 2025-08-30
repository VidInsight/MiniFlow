import traceback
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from miniflow.core.logger import get_logger
from miniflow.core.exceptions import MiniflowException
from miniflow.core.logger.context import get_correlation_id


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        try:
            self.logger = get_logger("api_errors")
        except Exception:
            self.logger = None  # Fallback if logger fails
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as exc:
            # FastAPI HTTP exceptions
            if self.logger:
                self.logger.warning(
                    f"HTTP Exception: {exc.detail}",
                    extra={
                        "status_code": exc.status_code,
                        "url": str(request.url),
                        "method": request.method,
                        "correlation_id": get_correlation_id()
                    }
                )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": True,
                    "message": exc.detail,
                    "correlation_id": get_correlation_id(),
                    "status_code": exc.status_code
                }
            )
            
        except MiniflowException as exc:
            # MiniFlow custom exceptions
            if self.logger:
                self.logger.error(
                    f"MiniFlow Exception: {exc.message}",
                    extra={
                        "error_code": exc.error_code.value,
                        "severity": exc.severity.value,
                        "details": exc.details,
                        "correlation_id": get_correlation_id()
                    }
                )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": True,
                    "message": exc.message,
                    "error_code": exc.error_code.value,
                    "correlation_id": get_correlation_id(),
                    "details": exc.details
                }
            )
            
        except Exception as exc:
            # Unexpected exceptions
            if self.logger:
                self.logger.error(
                    f"Unexpected error: {str(exc)}",
                    extra={
                        "exception_type": type(exc).__name__,
                        "traceback": traceback.format_exc(),
                        "correlation_id": get_correlation_id(),
                        "url": str(request.url),
                        "method": request.method
                    }
                )
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "message": "Internal server error",
                    "correlation_id": get_correlation_id()
                }
            )