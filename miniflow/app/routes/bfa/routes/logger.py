from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request

from miniflow.app.core.response import APIResponse
from miniflow.app.core.dependencies import verify_bfa_access, get_current_correlation_id
from miniflow.app.routes.bfa.actions import LoggerActions
from miniflow.app.routes.bfa.schemas.logger import (
    LoggerConfigUpdate,
    LogFileInfo
)
from miniflow.core.exceptions import MiniflowException

router = APIRouter()
logger_ops = LoggerActions()


@router.get("/", response_model=APIResponse[List[Dict[str, Any]]])
async def list_loggers(request: Request, auth_data: dict = Depends(verify_bfa_access)):
    """Sistemdeki tüm logger'ları listele"""
    try:
        loggers = logger_ops.get_available_loggers()

        correlation_id = await get_current_correlation_id(request)
        return APIResponse(
            data=loggers,
            message=f"Found {len(loggers)} loggers",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{logger_name}/config")
async def get_logger_config(logger_name: str, request: Request, auth_data: dict = Depends(verify_bfa_access)):
    """Logger konfigürasyonunu getir"""
    try:
        config = logger_ops.get_logger_config(logger_name)
        correlation_id = await get_current_correlation_id(request)

        return APIResponse(
            data=config,
            message=f"Logger config for {logger_name}",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/{logger_name}/config")
async def update_logger_config(logger_name: str, config_update: LoggerConfigUpdate, correlation_id: str = Depends(get_current_correlation_id), auth_data: dict = Depends(verify_bfa_access)):
    """Logger konfigürasyonunu güncelle"""
    try:
        # Sadece None olmayan değerleri güncelle
        updates = {k: v for k, v in config_update.dict().items() if v is not None}

        updated_config = logger_ops.update_logger_config(logger_name, updates)

        return APIResponse(
            data=updated_config,
            message=f"Logger {logger_name} config updated",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{logger_name}", response_model=APIResponse[LogFileInfo])
async def get_log_file_info(logger_name: str, correlation_id: str = Depends(get_current_correlation_id), auth_data: dict = Depends(verify_bfa_access)):
    """Log dosyası bilgilerini getir"""
    try:
        file_info = logger_ops.get_log_file_info(logger_name)

        return APIResponse(
            data=file_info,
            message=f"Log file info for {logger_name}",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ❌ STREAM ENDPOINT REMOVED
# Sebep: Production ortamında risk oluşturuyor
# - Memory leak potansiyeli
# - Connection timeout sorunları  
# - File rotation ile bozulma
# Alternatif: Manual log dosyası indirme veya SSH ile tail -f


@router.delete("/{logger_name}/file")
async def clear_log_file(logger_name: str, correlation_id: str = Depends(get_current_correlation_id), auth_data: dict = Depends(verify_bfa_access)):
    """Log dosyasını temizle"""
    try:
        result = logger_ops.clear_log_file(logger_name)

        return APIResponse(
            data=result,
            message=f"Log file cleared for {logger_name}",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


