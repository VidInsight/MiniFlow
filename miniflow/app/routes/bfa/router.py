"""
BFA Router
Back for Admin - Admin paneli için API router
"""

from fastapi import APIRouter, Depends

from miniflow.app.core.dependencies import verify_bfa_access
from miniflow.app.routes.bfa.routes import logger, monitoring

# BFA Ana router - Admin yetkilendirmesi ile
bfa_router = APIRouter(dependencies=[Depends(verify_bfa_access)])

# Logger management endpoint'lerini dahil et
bfa_router.include_router(
    logger.router,
    prefix="/logger", 
    tags=["BFA - Logger Management"]
)

# Monitoring management endpoint'lerini dahil et
bfa_router.include_router(
    monitoring.router,
    prefix="/monitoring",
    tags=["BFA - Monitoring Management"]
)
