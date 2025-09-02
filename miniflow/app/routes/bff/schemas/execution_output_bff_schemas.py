"""
ExecutionOutput BFF Schemas

Pydantic models for ExecutionOutput API requests and responses in the BFF layer.
READ-ONLY operations for execution results monitoring and analysis.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ExecutionOutputStatus(str, Enum):
    """Execution output status types"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"


class ExecutionOutputResponse(BaseModel):
    """ExecutionOutput response with all related data for frontend"""
    # Core execution output data (from ExecutionOutput.to_dict())
    id: str
    execution_id: str
    workflow_id: str
    node_id: str
    status: str
    result_data: Optional[Dict[str, Any]]
    started_at: Optional[str]
    ended_at: Optional[str]
    created_at: str
    updated_at: str
    
    # Related data for frontend
    execution: Optional[Dict[str, Any]] = Field(None, description="Related execution data")
    workflow: Optional[Dict[str, Any]] = Field(None, description="Related workflow data")
    node: Optional[Dict[str, Any]] = Field(None, description="Related node data")
    
    # Computed fields for frontend
    duration_seconds: Optional[float] = Field(None, description="Execution duration in seconds")
    success: bool = Field(False, description="Whether execution was successful")


class ExecutionOutputListResponse(BaseModel):
    """List response for execution outputs with pagination info"""
    execution_outputs: List[ExecutionOutputResponse]
    total_count: int = Field(..., description="Total number of execution outputs")
    page_info: Dict[str, Any] = Field(default_factory=dict, description="Pagination information")
