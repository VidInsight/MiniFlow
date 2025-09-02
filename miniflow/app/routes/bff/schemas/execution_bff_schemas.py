"""
Execution BFF Schemas

Pydantic models for Execution API requests and responses in the BFF layer.
READ-ONLY operations for execution monitoring and analysis.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ExecutionStatus(str, Enum):
    """Execution status types"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ExecutionResponse(BaseModel):
    """Execution response with all related data for frontend"""
    # Core execution data (from Execution.to_dict())
    id: str
    workflow_id: str
    status: str
    pending_nodes: int
    executed_nodes: int
    results: Dict[str, Any]
    started_at: str
    ended_at: Optional[str]
    created_at: str
    updated_at: str
    
    # Related data for frontend
    workflow: Optional[Dict[str, Any]] = Field(None, description="Related workflow data")
    
    # Computed fields for frontend
    duration_seconds: Optional[float] = Field(None, description="Execution duration in seconds")
    progress_percentage: Optional[float] = Field(None, description="Execution progress percentage")
    total_nodes: Optional[int] = Field(None, description="Total number of nodes in workflow")
    is_active: bool = Field(False, description="Whether execution is currently active")


class ExecutionListResponse(BaseModel):
    """List response for executions with pagination info"""
    executions: List[ExecutionResponse]
    total_count: int = Field(..., description="Total number of executions")
    page_info: Dict[str, Any] = Field(default_factory=dict, description="Pagination information")
