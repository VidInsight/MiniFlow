"""
Node BFF Schemas

Pydantic models for Node API requests and responses in the BFF layer.
Includes related entities: Workflow, Script, Edges for frontend consumption.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class NodeCreateRequest(BaseModel):
    """Create new node request"""
    workflow_id: str = Field(..., description="ID of the workflow this node belongs to")
    name: str = Field(..., description="Name of the node")
    description: Optional[str] = Field(None, description="Description of the node")
    script_id: Optional[str] = Field(None, description="ID of the script to execute")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Node parameters")
    max_retries: Optional[int] = Field(3, description="Maximum retry attempts")
    timeout_seconds: Optional[int] = Field(300, description="Timeout in seconds")


class NodeUpdateRequest(BaseModel):
    """Update node request"""
    name: Optional[str] = Field(None, description="Name of the node")
    description: Optional[str] = Field(None, description="Description of the node")
    script_id: Optional[str] = Field(None, description="ID of the script to execute")
    params: Optional[Dict[str, Any]] = Field(None, description="Node parameters")
    max_retries: Optional[int] = Field(None, description="Maximum retry attempts")
    timeout_seconds: Optional[int] = Field(None, description="Timeout in seconds")


class NodeResponse(BaseModel):
    """Node response with all related data for frontend"""
    # Core node data (from Node.to_dict())
    id: str
    workflow_id: str
    script_id: Optional[str]
    name: str
    description: Optional[str]
    params: Dict[str, Any]
    max_retries: int
    timeout_seconds: int
    created_at: str
    updated_at: str
    
    # Related data for frontend
    workflow: Optional[Dict[str, Any]] = Field(None, description="Related workflow data")
    script: Optional[Dict[str, Any]] = Field(None, description="Related script data")
    outgoing_edges: List[Dict[str, Any]] = Field(default_factory=list, description="Outgoing edges")
    incoming_edges: List[Dict[str, Any]] = Field(default_factory=list, description="Incoming edges")


class NodeDeleteResponse(BaseModel):
    """Enhanced node deletion response"""
    success: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Deletion result message")
    node_id: str = Field(..., description="ID of the deleted node")
    deleted_node: Optional[Dict[str, Any]] = Field(None, description="Deleted node data")
    database_deleted: bool = Field(..., description="Whether database deletion was successful")
    related_edges_deleted: int = Field(0, description="Number of related edges deleted")
    warnings: List[str] = Field(default_factory=list, description="Any warnings during deletion")
