from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class WorkflowCreateRequest(BaseModel):
    """Schema for creating a new workflow (minimal)"""
    # REQUIRED: Core fields
    name: str = Field(..., min_length=1, max_length=100, description="Workflow name (unique)")
    
    # OPTIONAL: Basic metadata
    description: Optional[str] = Field(None, max_length=1000, description="Workflow description")
    priority: Optional[int] = Field(0, ge=0, le=100, description="Workflow priority (0-100)")
    
    # OPTIONAL: Status (defaults to DRAFT in orchestrator)
    # status will be set automatically to DRAFT by orchestrator


class WorkflowUpdateRequest(BaseModel):
    """Schema for updating an existing workflow"""
    # All fields optional for updates
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Workflow name")
    description: Optional[str] = Field(None, max_length=1000, description="Workflow description")
    priority: Optional[int] = Field(None, ge=0, le=100, description="Workflow priority (0-100)")
    status: Optional[str] = Field(None, description="Workflow status (DRAFT, ACTIVE, DEACTIVATED)")
    status_message: Optional[str] = Field(None, max_length=500, description="Status message")


class WorkflowResponse(BaseModel):
    """Workflow response model (Workflow.to_dict() yapısına tamamen uygun)"""
    # BaseModel alanları (otomatik)
    id: str = Field(description="Workflow unique identifier (WF-XXXXXXXXXXXXX)")
    created_at: str = Field(description="Creation timestamp (ISO format)")
    updated_at: str = Field(description="Last update timestamp (ISO format)")
    
    # Workflow model alanları (models.py'den birebir)
    name: str = Field(description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    priority: int = Field(description="Workflow priority")
    status: str = Field(description="Workflow status (DRAFT, ACTIVE, DEACTIVATED)")
    status_message: Optional[str] = Field(None, description="Workflow status message")


class WorkflowDeleteResponse(BaseModel):
    """Workflow deletion response model (Actions layer tarafından oluşturulan extended response)"""
    # Silinen record bilgileri (Workflow.to_dict() formatında)
    deleted_record: WorkflowResponse = Field(description="The deleted workflow record")
    
    # Silme durumu bilgileri
    database_deleted: bool = Field(description="Whether database record was deleted")
    
    # Mesajlar
    message: str = Field(description="Overall deletion status message")
    warnings: Optional[List[str]] = Field(None, description="Any warnings during deletion process")
