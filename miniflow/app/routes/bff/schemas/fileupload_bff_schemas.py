from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FileUploadCreateRequest(BaseModel):
    """File upload oluşturma modeli (API upload'tan sonra otomatik metadata çıkarma)"""
    # OPTIONAL: Sadece override etmek için
    is_temporary: Optional[bool] = Field(True, description="Whether file is temporary (default: True)")
    
    # OTOMATIK ÇIKARILACAK (API Upload sırasında):
    # - filename: request.file.filename (from multipart/form-data)
    # - file_path: ./temp/{unique_filename} or uploaded path
    # - name: filename
    # - filename_base: os.path.splitext(filename)[0] 
    # - file_extension: os.path.splitext(filename)[1]
    # - file_size: len(file_content) or file.size
    # - mime_type: request.file.content_type or mimetypes.guess_type()
    # - checksum: hashlib calculation from file content
    
    # NOT NEEDED: filename -> API upload'tan otomatik geliyor!


class FileUploadResponse(BaseModel):
    """File upload response modeli (FileUpload.to_dict() yapısına tamamen uygun)"""
    # BaseModel alanları (otomatik)
    id: str = Field(description="File upload unique identifier (FU-XXXXXXXXXXXXX)")
    created_at: str = Field(description="Creation timestamp (ISO format)")
    updated_at: str = Field(description="Last update timestamp (ISO format)")
    
    # FileUpload model alanları (models.py'den birebir)
    name: str = Field(description="Full file name with extension (file_name.file_extension format)")
    filename: str = Field(description="Base filename without extension")
    file_extension: Optional[str] = Field(None, description="File extension (.pdf, .txt, etc.)")
    file_path: str = Field(description="Absolute path to file")
    file_size: int = Field(description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    checksum: Optional[str] = Field(None, description="File checksum")
    is_temporary: bool = Field(description="Whether file is temporary (default: True)")


class FileUploadDeleteResponse(BaseModel):
    """File upload silme response modeli (Actions layer tarafından oluşturulan extended response)"""
    # Silinen record bilgileri (FileUpload.to_dict() formatında)
    deleted_record: FileUploadResponse = Field(description="The deleted file upload record")
    
    # Silme durumu bilgileri
    database_deleted: bool = Field(description="Whether database record was deleted")
    physical_file_deleted: bool = Field(description="Whether physical file was removed from filesystem")
    file_existed: bool = Field(description="Whether physical file existed before deletion attempt")
    
    # Mesajlar
    message: str = Field(description="Overall deletion status message")
    warnings: Optional[List[str]] = Field(None, description="Any warnings during deletion process")
