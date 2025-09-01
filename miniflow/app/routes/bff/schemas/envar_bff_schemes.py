from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class EnvironmentVariableCreateRequest(BaseModel):
    """Environment variable oluşturma modeli (Frontend için)"""
    name: str = Field(..., min_length=1, max_length=100, description="Variable name (required)", pattern="^[A-Za-z][A-Za-z0-9_]*$")
    value: str = Field(..., description="Variable value")
    description: Optional[str] = Field(None, max_length=500,description="Variable description")
    variable_type: Optional[str] = Field("string",description="Variable type (string, integer, float, boolean, json, url, file_path)")

class EnvironmentVariableUpdateRequest(BaseModel):
    """Environment variable güncelleme modeli (Frontend için)"""
    value: Optional[str] = Field(None,description="New variable value")
    description: Optional[str] = Field( None, max_length=500, description="New variable description")

class EnvironmentVariableResponse(BaseModel):
    """Environment variable response modeli (EnvironmentVariable.to_dict() yapısına uygun)"""
    # BaseModel alanları
    id: str = Field(description="Variable unique identifier")
    created_at: str = Field(description="Creation timestamp (ISO format)")
    updated_at: str = Field(description="Last update timestamp (ISO format)")
    
    # EnvironmentVariable model alanları
    name: str = Field(description="Variable name")
    value: Optional[str] = Field(None, description="Variable value")
    description: Optional[str] = Field(None, description="Variable description")
    variable_type: str = Field(description="Variable type enum value")
    scope: str = Field(description="Variable scope enum value")
    last_accessed_at: Optional[str] = Field(None, description="Last access timestamp (ISO format)")
    access_count: int = Field(default=0, description="Access count")
    last_modified_by: Optional[str] = Field(None, description="Last modified by user")

# List response - actions sadece List[Dict] döndürüyor, extra metadata yok
# Bu yüzden EnvironmentVariablesListResponse yerine List[EnvironmentVariableResponse] kullanılacak

class EnvironmentVariableDeleteResponse(BaseModel):
    """Environment variable silme response modeli"""
    deleted: bool = Field(description="Whether deletion was successful")
    name: str = Field(description="Deleted variable name")
    message: str = Field(description="Success message")