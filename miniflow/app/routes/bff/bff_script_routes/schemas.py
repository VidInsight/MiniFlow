from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ScriptCreateRequest(BaseModel):
    """Script create request"""
    name: str = Field(..., min_length=1, max_length=100, description="Script name (unique)")
    category: str = Field(..., min_length=1, max_length=50, description="Script category")
    content: str = Field(..., min_length=1, description="Script content")
    subcategory: Optional[str] = Field(None, max_length=50, description="Script subcategory")
    description: Optional[str] = Field(None, max_length=1000, description="Script description")
    version: Optional[str] = Field("1.0.0", max_length=20, description="Script version")
    author: Optional[str] = Field(None, max_length=100, description="Script author")
    file_extension: Optional[str] = Field(".py", max_length=10, description="File extension (.py, .js, .sh, etc.)")

    # Input/Output schema definitions
    input_schema: Optional[Dict[str, Any]] = Field(default_factory=dict, description="JSON schema for input validation")
    output_schema: Optional[Dict[str, Any]] = Field(default_factory=dict, description="JSON schema for output validation")
    test_input_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Test input parameters")
    test_output_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Test output parameters")

    def to_dict(self):
        return {
            'name': self.name,
            'category': self.category,
            'content': self.content,
            'subcategory': self.subcategory,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'file_extension': self.file_extension,
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'test_input_params': self.test_input_params,
            'test_output_params': self.test_output_params
        }


class ScriptUpdateRequest(BaseModel):
    """Script update request"""
    content: Optional[str] = Field(None, min_length=1, description="Script content")
    description: Optional[str] = Field(None, max_length=1000, description="Script description")
    version: Optional[str] = Field(None, max_length=20, description="Script version")
    author: Optional[str] = Field(None, max_length=100, description="Script author")

    # Input/Output schema definitions
    input_schema: Optional[Dict[str, Any]] = Field(None, description="JSON schema for input validation")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="JSON schema for output validation")
    test_input_params: Optional[Dict[str, Any]] = Field(None, description="Test input parameters")
    test_output_params: Optional[Dict[str, Any]] = Field(None, description="Test output parameters")

    def to_dict(self):
        result = {}
        if self.content is not None:
            result['content'] = self.content
        if self.description is not None:
            result['description'] = self.description
        if self.version is not None:
            result['version'] = self.version
        if self.author is not None:
            result['author'] = self.author
        if self.input_schema is not None:
            result['input_schema'] = self.input_schema
        if self.output_schema is not None:
            result['output_schema'] = self.output_schema
        if self.test_input_params is not None:
            result['test_input_params'] = self.test_input_params
        if self.test_output_params is not None:
            result['test_output_params'] = self.test_output_params
        return result


class ScriptFilterRequest(BaseModel):
    """Script filter request"""
    filters: Dict[str, Any] = Field(..., description="Filter criteria")
    skip: int = Field(0, ge=0, description="Number of records to skip for pagination")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")
    order_by_field: Optional[str] = Field(None, description="Field to order by")
    include_relationships: bool = Field(False, description="Include related objects")
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


class ScriptResponse(BaseModel):
    """Script response data"""
    id: str = Field(description="Script unique identifier")
    name: str = Field(description="Script name")
    description: Optional[str] = Field(description="Script description")
    version: str = Field(description="Script version")
    category: str = Field(description="Script category")
    subcategory: Optional[str] = Field(description="Script subcategory")
    file_extension: Optional[str] = Field(description="File extension")
    content: Optional[str] = Field(description="Script content")
    author: Optional[str] = Field(description="Script author")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Last update timestamp")
    
    # Input/Output schema definitions
    input_schema: Optional[Dict[str, Any]] = Field(default_factory=dict, description="JSON schema for input validation")
    output_schema: Optional[Dict[str, Any]] = Field(default_factory=dict, description="JSON schema for output validation")
    test_input_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Test input parameters")
    test_output_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Test output parameters")


class ScriptListResponse(BaseModel):
    """Script list response"""
    items: List[ScriptResponse] = Field(description="List of scripts")
    total: int = Field(description="Total number of scripts")
    skip: int = Field(description="Number of records skipped")
    limit: int = Field(description="Maximum number of records requested")


class ScriptOperationResponse(BaseModel):
    """Script action response"""
    action_status: bool = Field(description="Whether action was successful")
    record_id: str = Field(description="ID of script")
    message: str = Field(description="Action result message")
    file_operations: Dict[str, Any] = Field(description="File operation details", default_factory=dict)


class CountResponse(BaseModel):
    """Count response"""
    count: int = Field(description="Total count")


class ScriptTestStatsResponse(BaseModel):
    test_status: str = Field(description="Test status")
    test_coverage: float = Field(description="Test coverage")
    last_test_run_at: str = Field(description="Last test run at")
    test_results: dict = Field(description="Test results")

class ScriptPerformanceResultResponse(BaseModel):
    avg_execution_time: float = Field(description="Average execution time")
    min_execution_time: float = Field(description="Minimum execution time")
    max_execution_time: float = Field(description="Maximum execution time")
    success_rate: float = Field(description="Success rate")
    total_executions:  int = Field(description="Total executions")