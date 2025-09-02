"""
ExecutionInput BFF Schemas

Pydantic models for ExecutionInput API requests and responses in the BFF layer.
READ-ONLY operations for scheduler monitoring and execution planning.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ExecutionInputResponse(BaseModel):
    """ExecutionInput response with all related data for frontend"""
    # Core execution input data (from ExecutionInput.to_dict())
    id: str
    execution_id: str
    workflow_id: str
    node_id: str
    priority: int
    dependency_count: int
    wait_factor: int
    node_name: str
    script_path: Optional[str]
    node_params: Dict[str, Any]
    created_at: str
    updated_at: str
    
    # Related data for frontend
    execution: Optional[Dict[str, Any]] = Field(None, description="Related execution data")
    workflow: Optional[Dict[str, Any]] = Field(None, description="Related workflow data")
    node: Optional[Dict[str, Any]] = Field(None, description="Related node data")


class ExecutionInputListResponse(BaseModel):
    """List response for execution inputs with pagination info"""
    execution_inputs: List[ExecutionInputResponse]
    total_count: int = Field(..., description="Total number of execution inputs")
    page_info: Dict[str, Any] = Field(default_factory=dict, description="Pagination information")
