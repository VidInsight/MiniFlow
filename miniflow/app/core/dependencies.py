import threading
from typing import Optional
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from miniflow.core.logger import get_logger
from miniflow.__main__ import MiniflowCore

# Security scheme
security = HTTPBearer(auto_error=False) # do not create error
logger = get_logger("miniflow_core")


async def get_current_correlation_id(request: Request) -> str:
    """Current correlation ID dependency"""
    return getattr(request.state, 'correlation_id', 'unknown')


async def get_api_logger():
    """API logger dependency"""
    return get_logger("miniflow_api")


def get_miniflow_core():
    """MiniflowCore singleton dependency"""
    return MiniflowCore.get_instance()

def get_database_engine(request: Request):
    """Get database engine from app state (injected by MiniflowCore)"""
    if hasattr(request.app.state, 'database_engine'):
        return request.app.state.database_engine
    
    # Fallback: Create engine if not injected (for standalone usage)
    if not hasattr(get_database_engine, '_fallback_engine'):
        from miniflow.database import get_sqlite_config, create_database_engine
        config = get_sqlite_config("miniflow_team_test")
        get_database_engine._fallback_engine = create_database_engine(config, auto_start=True)
        logger.info("Fallback database engine created for standalone usage")
    
    return get_database_engine._fallback_engine

def get_database_orchestrator(request: Request):
    """Get database orchestrator from app state or MiniflowCore"""
    # Önce app state'den dene (injection varsa)
    if hasattr(request.app.state, 'database_engine'):
        # App state'de engine var, MiniflowCore singleton kullan
        try:
            return MiniflowCore.get_instance().get_database_orchestrator()
        except RuntimeError:
            # MiniflowCore database engine started değil, fallback'e düş
            pass
    
    # Fallback: Standalone için yeni orchestrator
    if not hasattr(get_database_orchestrator, '_fallback_orchestrator'):
        from miniflow.database import get_sqlite_config, create_database_engine
        from miniflow.database.orchestration import DatabaseOrchestrator
        
        config = get_sqlite_config("miniflow_team_test")
        engine = create_database_engine(config, auto_start=True, create_tables=True)
        get_database_orchestrator._fallback_orchestrator = DatabaseOrchestrator(engine)
        logger.info("Fallback database orchestrator created for standalone usage")
    
    return get_database_orchestrator._fallback_orchestrator


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Get current user ID from token"""
    # TODO: Implement proper JWT token validation
    # For now, return a default user ID
    return "default_user"


async def verify_bff_access(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """BFF access verification"""

    # TODO: Frontend için token kontrolü
    # Token validation logic burada
    # JWT decode, database check, etc.
    
    return {"user_id": "frontend_user", "role": "frontend"}


async def verify_bfd_access(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """BFD access verification"""

    # TODO: Developer access için yüksek yetki kontrolü
    # Developer token validation

    return {"user_id": "dev_user", "role": "developer"}


async def verify_bfa_access(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """BFA access verification"""

    # TODO: Admin access için en yüksek yetki kontrolü
    # Admin token validation

    return {"user_id": "admin_user", "role": "admin"}
