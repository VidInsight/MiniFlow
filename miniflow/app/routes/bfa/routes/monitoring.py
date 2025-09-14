"""
BFA Monitoring Routes
Admin monitoring yönetimi endpoint'leri
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from miniflow.app.core.response import APIResponse
from miniflow.app.core.dependencies import verify_bfa_access, get_current_correlation_id
from miniflow.app.routes.bfa.actions import MonitoringActions
from miniflow.app.routes.bfa.schemas.monitoring import (
    SystemMetricsResponse,
    AlertResponse,
    AlertSummary,
    ComponentMetricsResponse,
    MonitoringConfigUpdate,
    MonitoringConfigResponse,
    MonitoringStatusResponse,
    ClearAlertsResponse
)
from miniflow.core.exceptions import MiniflowException
from miniflow.app.utils.decorators import with_api_error_handling

router = APIRouter()
monitoring_ops = MonitoringActions()


# ==================== SYSTEM METRICS ENDPOINTS ====================

@router.get("/metrics/system", response_model=APIResponse[SystemMetricsResponse])
@with_api_error_handling(operation="get_system_metrics")
async def get_system_metrics(
    correlation_id: str = Depends(get_current_correlation_id), 
    auth_data: dict = Depends(verify_bfa_access)
):
    """Anlık sistem metriklerini getir"""
    metrics = monitoring_ops.get_system_metrics()
    return APIResponse(
        data=metrics,
        message="System metrics retrieved",
        correlation_id=correlation_id
    )


@router.get("/metrics/components", response_model=APIResponse[Dict[str, ComponentMetricsResponse]])
@with_api_error_handling(operation="get_all_components_metrics")
async def get_all_components_metrics(
    correlation_id: str = Depends(get_current_correlation_id), 
    auth_data: dict = Depends(verify_bfa_access)
):
    """Tüm component metriklerini getir"""
    components_metrics = monitoring_ops.get_all_components_metrics()
    
    return APIResponse(
        data=components_metrics,
        message=f"Retrieved metrics for {len(components_metrics)} components",
        correlation_id=correlation_id
    )


@router.get("/metrics/component/{component_name}", response_model=APIResponse[ComponentMetricsResponse])
async def get_component_metrics(component_name: str, correlation_id: str = Depends(get_current_correlation_id), auth_data: dict = Depends(verify_bfa_access)):
    """Belirli bir component'in metriklerini getir"""
    try:
        metrics = monitoring_ops.get_component_metrics(component_name)
        
        return APIResponse(
            data=metrics,
            message=f"Component metrics for {component_name}",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/status", response_model=APIResponse[MonitoringStatusResponse])
async def get_monitoring_status(correlation_id: str = Depends(get_current_correlation_id), auth_data: dict = Depends(verify_bfa_access)):
    """Monitoring sistem durumunu getir"""
    try:
        status = monitoring_ops.get_monitoring_status()
        
        return APIResponse(
            data=status,
            message="Monitoring status retrieved",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ==================== ALERT MANAGEMENT ENDPOINTS ====================

@router.get("/alerts", response_model=APIResponse[List[AlertResponse]])
async def get_alerts(
    limit: Optional[int] = Query(None, description="Limit number of alerts", ge=1, le=1000),
    level: Optional[str] = Query(None, description="Filter by alert level (INFO, WARNING, CRITICAL)"),
    component: Optional[str] = Query(None, description="Filter by component name"),
    correlation_id: str = Depends(get_current_correlation_id),
    auth_data: dict = Depends(verify_bfa_access)
):
    """
    Uyarıları getir - filtreleme seçenekleri ile
    
    Query parameters:
    - limit: Maksimum alert sayısı (1-1000)
    - level: Alert seviyesi (INFO, WARNING, CRITICAL)
    - component: Component adı
    """
    try:
        if level:
            alerts = monitoring_ops.get_alerts_by_level(level)
        elif component:
            alerts = monitoring_ops.get_alerts_by_component(component)
        else:
            alerts = monitoring_ops.get_all_alerts(limit)
        
        # Apply limit if specified and not already filtered
        if limit and not level and not component:
            alerts = alerts[-limit:]  # Get most recent
        
        return APIResponse(
            data=alerts,
            message=f"Retrieved {len(alerts)} alerts",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/alerts/recent", response_model=APIResponse[List[AlertResponse]])
async def get_recent_alerts(count: int = Query(default=10, description="Number of recent alerts", ge=1, le=100), correlation_id: str = Depends(get_current_correlation_id),  auth_data: dict = Depends(verify_bfa_access)):
    """Son N uyarıyı getir"""
    try:
        alerts = monitoring_ops.get_recent_alerts(count)
        
        return APIResponse(
            data=alerts,
            message=f"Retrieved {len(alerts)} recent alerts",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/alerts/summary", response_model=APIResponse[AlertSummary])
async def get_alert_summary(correlation_id: str = Depends(get_current_correlation_id), auth_data: dict = Depends(verify_bfa_access)):
    """Uyarı özetini getir"""
    try:
        summary = monitoring_ops.get_alert_summary()
        
        return APIResponse(
            data=summary,
            message="Alert summary retrieved",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete("/alerts", response_model=APIResponse[ClearAlertsResponse])
async def clear_all_alerts(correlation_id: str = Depends(get_current_correlation_id), auth_data: dict = Depends(verify_bfa_access)):
    """Tüm uyarıları temizle"""
    try:
        result = monitoring_ops.clear_all_alerts()
        
        return APIResponse(
            data=result,
            message="Alerts cleared successfully",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ==================== CONFIGURATION MANAGEMENT ENDPOINTS ====================

@router.get("/config", response_model=APIResponse[MonitoringConfigResponse])
async def get_monitoring_config(correlation_id: str = Depends(get_current_correlation_id), auth_data: dict = Depends(verify_bfa_access)):
    """Monitoring konfigürasyonunu getir"""
    try:
        config = monitoring_ops.get_monitoring_config()
        
        return APIResponse(
            data=config,
            message="Monitoring configuration retrieved",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/config", response_model=APIResponse[MonitoringConfigResponse])
async def update_monitoring_config(config_update: MonitoringConfigUpdate, correlation_id: str = Depends(get_current_correlation_id), auth_data: dict = Depends(verify_bfa_access)):
    """Monitoring konfigürasyonunu güncelle"""
    try:
        # Sadece None olmayan değerleri güncelle
        updates = {k: v for k, v in config_update.dict().items() if v is not None}
        
        if not updates:
            raise HTTPException(status_code=400, detail="No valid updates provided")
        
        updated_config = monitoring_ops.update_monitoring_config(updates)
        
        return APIResponse(
            data=updated_config,
            message="Monitoring configuration updated",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ==================== COMPONENT MANAGEMENT ENDPOINTS ====================

@router.get("/components", response_model=APIResponse[List[str]])
async def get_registered_components(correlation_id: str = Depends(get_current_correlation_id), auth_data: dict = Depends(verify_bfa_access)):
    """Kayıtlı component'leri listele"""
    try:
        components = monitoring_ops.get_registered_components()
        
        return APIResponse(
            data=components,
            message=f"Found {len(components)} registered components",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ==================== HEALTH CHECK ENDPOINTS ====================

@router.get("/health", response_model=APIResponse[Dict[str, Any]])
async def get_system_health(request: Request, auth_data: dict = Depends(verify_bfa_access)):
    """Genel sistem sağlığını getir"""
    try:
        health = monitoring_ops.get_system_health()
        correlation_id = await get_current_correlation_id(request)
        
        return APIResponse(
            data=health,
            message="System health retrieved",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
