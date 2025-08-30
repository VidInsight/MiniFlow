"""
BFF Router
Back for Frontend - Frontend için API router
"""

from fastapi import APIRouter, Depends

from miniflow.app.core.dependencies import verify_bff_access

# BFF Ana router - Frontend yetkilendirmesi ile
bff_router = APIRouter(dependencies=[Depends(verify_bff_access)])

# TODO: Frontend endpoint'lerini buraya ekle
# Örnek: user data, dashboard, notifications, etc.
