from typing import Optional
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from miniflow.core.logger import get_logger

# Security scheme
security = HTTPBearer(auto_error=False)
logger = get_logger("miniflow_core")


async def get_current_correlation_id(request: Request) -> str:
    """Current correlation ID dependency"""
    return getattr(request.state, 'correlation_id', 'unknown')


async def get_api_logger():
    """API logger dependency"""
    return get_logger("miniflow_api")


async def verify_bff_access(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """BFF access verification"""

    # Frontend için token kontrolü
    # Token validation logic burada
    # JWT decode, database check, etc.
    
    return {"user_id": "frontend_user", "role": "frontend"}


async def verify_bfd_access(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """BFD access verification"""

    # Developer access için yüksek yetki kontrolü
    # Developer token validation

    return {"user_id": "dev_user", "role": "developer"}


async def verify_bfa_access(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """BFA access verification"""

    # Admin access için en yüksek yetki kontrolü
    # Admin token validation

    return {"user_id": "admin_user", "role": "admin"}
