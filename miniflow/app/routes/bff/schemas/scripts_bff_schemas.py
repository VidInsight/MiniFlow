from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ScriptCreateRequest(BaseModel):
    """Script create modeli (Minimal - sadece core fields)"""
    # REQUIRED: Core script fields
    name: str = Field(..., min_length=1, max_length=100, description="Script name (unique)")
    language: str = Field(..., description="Script language (PYTHON, BASH)")
    category: str = Field(..., min_length=1, max_length=50, description="Script category")
    content: str = Field(..., min_length=1, description="Script content")
    
    # OPTIONAL: Basic metadata
    subcategory: Optional[str] = Field(None, max_length=50, description="Script subcategory")
    description: Optional[str] = Field(None, max_length=1000, description="Script description")
    version: Optional[str] = Field("1.0.0", max_length=20, description="Script version")
    
    # OPTIONAL: Advanced metadata
    required_packages: Optional[List[str]] = Field(None, description="Required packages list")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="Input JSON schema")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="Output JSON schema")
    tags: Optional[List[str]] = Field(None, description="Script tags")
    author: Optional[str] = Field(None, max_length=100, description="Script author")
    
    # OPTIONAL: Test fields
    test_input_params: Optional[Dict[str, Any]] = Field(None, description="Test input parameters")
    test_output_params: Optional[Dict[str, Any]] = Field(None, description="Test output parameters")
    
    # OTOMATIK ÇIKARILACAK (Orchestrator tarafından):
    # - file_extension: language'dan otomatik (.py, .sh)
    # - file_path: scripts/{category}/{subcategory}/{name}.{ext}
    # - file_size: len(content.encode('utf-8'))


class ScriptResponse(BaseModel):
    """Script response modeli (Script.to_dict() yapısına tamamen uygun)"""
    # BaseModel alanları (otomatik)
    id: str = Field(description="Script unique identifier (SC-XXXXXXXXXXXXX)")
    created_at: str = Field(description="Creation timestamp (ISO format)")
    updated_at: str = Field(description="Last update timestamp (ISO format)")
    
    # Script model alanları (models.py'den birebir)
    name: str = Field(description="Script name (unique)")
    description: Optional[str] = Field(None, description="Script description")
    version: str = Field(description="Script version")
    language: str = Field(description="Script language enum value")
    
    # Category information
    category: str = Field(description="Script category")
    subcategory: Optional[str] = Field(None, description="Script subcategory")
    
    # File information
    file_extension: Optional[str] = Field(None, description="File extension (.py, .sh, etc.)")
    file_path: Optional[str] = Field(None, description="Physical file path")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    content: Optional[str] = Field(None, description="Script content")
    
    # Environment
    required_packages: List[str] = Field(description="Required packages list")
    
    # Input/Output schemas
    input_schema: Dict[str, Any] = Field(description="Input JSON schema")
    output_schema: Dict[str, Any] = Field(description="Output JSON schema")
    test_input_params: Dict[str, Any] = Field(description="Test input parameters")
    test_output_params: Dict[str, Any] = Field(description="Test output parameters")
    
    # Test and quality
    test_status: str = Field(description="Test status enum value")
    test_coverage: Optional[int] = Field(None, description="Test coverage percentage")
    last_test_run_at: Optional[str] = Field(None, description="Last test run timestamp (ISO format)")
    test_results: Dict[str, Any] = Field(description="Test results data")
    
    # Performance metrics
    avg_execution_time: Optional[float] = Field(None, description="Average execution time")
    min_execution_time: Optional[float] = Field(None, description="Minimum execution time")
    max_execution_time: Optional[float] = Field(None, description="Maximum execution time")
    success_rate: Optional[float] = Field(None, description="Success rate (0.0-1.0)")
    total_executions: int = Field(description="Total execution count")
    
    # Metadata
    tags: List[str] = Field(description="Script tags")
    author: Optional[str] = Field(None, description="Script author")
    documentation_url: Optional[str] = Field(None, description="Documentation URL")


class ScriptDeleteResponse(BaseModel):
    """Script delete response modeli (Actions layer tarafından oluşturulan extended response)"""
    # Silinen record bilgileri (Script.to_dict() formatında)
    deleted_record: ScriptResponse = Field(description="The deleted script record")
    
    # Silme durumu bilgileri
    database_deleted: bool = Field(description="Whether database record was deleted")
    physical_file_deleted: bool = Field(description="Whether physical file was removed from filesystem")
    file_existed: bool = Field(description="Whether physical file existed before deletion attempt")
    
    # Mesajlar
    message: str = Field(description="Overall deletion status message")
    warnings: Optional[List[str]] = Field(None, description="Any warnings during deletion process")