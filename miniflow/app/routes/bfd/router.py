"""
BFD Router
Back for Development - Developer araçları için API router
"""

from fastapi import APIRouter, Depends

from miniflow.app.core.dependencies import verify_bfd_access

# BFD Ana router - Developer yetkilendirmesi ile
bfd_router = APIRouter(dependencies=[Depends(verify_bfd_access)])

# TODO: Developer endpoint'lerini buraya ekle
# Örnek: metrics, debug, system info, logs, etc.
