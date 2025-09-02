"""
Edge BFF Schemas

Pydantic models for Edge API requests and responses in the BFF layer.
Includes related entities: Workflow, FromNode, ToNode for frontend consumption.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ConditionType(str, Enum):
    """Edge condition types"""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ALWAYS = "ALWAYS"
    CONDITIONAL = "CONDITIONAL"


class EdgeCreateRequest(BaseModel):
    """Create new edge request"""
    workflow_id: str = Field(..., description="ID of the workflow this edge belongs to")
    from_node_id: str = Field(..., description="ID of the source node")
    to_node_id: str = Field(..., description="ID of the target node")
    condition_type: Optional[ConditionType] = Field(ConditionType.SUCCESS, description="Edge condition type")


class EdgeUpdateRequest(BaseModel):
    """Update edge request"""
    condition_type: Optional[ConditionType] = Field(None, description="Edge condition type")


class EdgeResponse(BaseModel):
    """Edge response with all related data for frontend"""
    # Core edge data (from Edge.to_dict())
    id: str
    workflow_id: str
    from_node_id: str
    to_node_id: str
    condition_type: str
    created_at: str
    updated_at: str
    
    # Related data for frontend
    workflow: Optional[Dict[str, Any]] = Field(None, description="Related workflow data")
    from_node: Optional[Dict[str, Any]] = Field(None, description="Source node data")
    to_node: Optional[Dict[str, Any]] = Field(None, description="Target node data")


class EdgeDeleteResponse(BaseModel):
    """Enhanced edge deletion response"""
    success: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Deletion result message")
    edge_id: str = Field(..., description="ID of the deleted edge")
    deleted_edge: Optional[Dict[str, Any]] = Field(None, description="Deleted edge data")
    database_deleted: bool = Field(..., description="Whether database deletion was successful")
    warnings: List[str] = Field(default_factory=list, description="Any warnings during deletion")
