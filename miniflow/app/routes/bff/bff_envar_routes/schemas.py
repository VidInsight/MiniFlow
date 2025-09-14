"""
Environment Variable Schemas
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from miniflow.database.models import VariableType, VariableScope


# Request - CREATE
class EnvironmentVariableCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Variable name (required)", pattern="^[A-Za-z][A-Za-z0-9_]*$")
    value: str = Field(..., description="Variable value")
    description: Optional[str] = Field(None, max_length=500, description="Variable description")
    variable_type: Optional[VariableType] = Field(VariableType.STRING, description="Variable type: STRING, INTEGER, FLOAT, BOOLEAN, JSON, SECRET, CREDENTIAL, FILE_PATH, URL")
    scope: Optional[VariableScope] = Field(VariableScope.USER, description="Variable scope: GLOBAL, WORKFLOW, TRIGGER, USER, NODE")

    def to_dict(self):
        return {
            'name': self.name,  
            'value': self.value,
            'description': self.description,
            'variable_type': self.variable_type,
            'scope': self.scope
        }
            
# Request - UPDATE
class EnvironmentVariableUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Variable name (required)", pattern="^[A-Za-z][A-Za-z0-9_]*$")
    value: Optional[str] = Field(None, description="Variable value")
    description: Optional[str] = Field(None, max_length=500, description="Variable description")
    variable_type: Optional[VariableType] = Field(None, description="Variable type: STRING, INTEGER, FLOAT, BOOLEAN, JSON, SECRET, CREDENTIAL, FILE_PATH, URL")
    scope: Optional[VariableScope] = Field(None, description="Variable scope: GLOBAL, WORKFLOW, TRIGGER, USER, NODE")

    def to_dict(self):
        return {
            'name': self.name,  
            'value': self.value,
            'description': self.description,
            'variable_type': self.variable_type,
            'scope': self.scope
        }

# Request - FILTER
class EnvironmentVariableFilterRequest(BaseModel):
    """Environment variable filtreleme modeli"""
    filters: Dict[str, Any] = Field(..., description="Filter criteria")
    skip: int = Field(0, ge=0, description="Number of records to skip for pagination")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")
    order_by_field: Optional[str] = Field(None, description="Field to order by")
    include_relationships: bool = Field(False, description="Include related objects (always False for EnvironmentVariable)")
    exclude_fields: Optional[List[str]] = Field(None, description="Fields to exclude from response")

    def to_dict(self):
        return {
            'filters': self.filters,  
            'skip': self.skip,
            'limit': self.limit,
            'order_by_field': self.order_by_field,
            'include_relationships': self.include_relationships,
            'exclude_fields': self.exclude_fields
        }

# Response - Environment Variable
class EnvironmentVariableResponse(BaseModel):
    # BaseModel alanları
    id: str = Field(description="Variable unique identifier (EV-XXXXXXXXXXXXX)")
    created_at: str = Field(description="Creation timestamp (ISO format)")
    updated_at: str = Field(description="Last update timestamp (ISO format)")

    # EnvironmentVariable model alanları
    name: str = Field(description="Variable name")
    value: Optional[str] = Field(None, description="Variable value")
    description: Optional[str] = Field(None, description="Variable description")
    variable_type: VariableType = Field(description="Variable type: STRING, INTEGER, FLOAT, BOOLEAN, JSON, SECRET, CREDENTIAL, FILE_PATH, URL")
    scope: VariableScope = Field(description="Variable scope: GLOBAL, WORKFLOW, TRIGGER, USER, NODE")
    last_accessed_at: Optional[str] = Field(None, description="Last access timestamp (ISO format)")
    access_count: int = Field(default=0, description="Access count")
    last_modified_by: Optional[str] = Field(None, description="Last modified by user")

# Response - Environment Variable List
class EnvironmentVariableListResponse(BaseModel):
    items: List[EnvironmentVariableResponse] = Field(description="List of environment variables")
    total: int = Field(description="Total number of environment variables")
    skip: int = Field(description="Number of records skipped")
    limit: int = Field(description="Maximum number of records requested")

# Response - Delete Response
class EnvironmentVariableOperationResponse(BaseModel):
    action_status: bool = Field(description="Whether deletion was successful")
    record_id: str = Field(description="ID of deleted variable")
    message: str = Field(description="Success message")

# Response - Count Response
class CountResponse(BaseModel):
    count: int = Field(description="Total count")
