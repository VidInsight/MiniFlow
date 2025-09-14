# FileUploadOrchestrator API Documentation

FileUploadOrchestrator, file upload yönetimi ve CRUD operasyonlarını yürütür.

## Genel Bilgiler

- **Sınıf:** `FileUploadOrchestrator`
- **Parent:** `BaseOrchestrator`
- **Modül:** `miniflow.database.orchestration.fileupload_orchestrator`
- **Primary Model:** `FileUpload`
- **Primary CRUD:** `fileupload_crud`

## FileUpload-Specific Metodlar

### create()
```python
@with_session
def create(
    self, 
    session: Session, 
    name: str, 
    file_path: str, 
    file_size: int, 
    **kwargs
) -> Dict[str, Any]
```

**Amaç:** Yeni file upload kaydı oluştur

**Parametreler:**
- `name` (str): Dosya adı (file_name.extension formatında, unique)
- `file_path` (str): Dosya path'i (absolute path, unique)
- `file_size` (int): Dosya boyutu (bytes)
- `**kwargs`: Diğer file upload alanları
  - `filename` (str): Base filename (extension olmadan)
  - `file_extension` (str): Dosya uzantısı (.pdf, .txt, vb.)
  - `mime_type` (str): MIME type
  - `checksum` (str): Dosya checksum'ı (MD5/SHA256)
  - `is_temporary` (bool): Geçici dosya mı (default: True)

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Oluşturulan file upload'un dictionary'si
- **Hata:** OrchestrationError

**Örnek Dönüş:**
```json
{
    "id": "FU-A1B2C3D4E5F6G7H8I",
    "name": "data_report.pdf",
    "filename": "data_report",
    "file_extension": ".pdf",
    "file_path": "/uploads/2024/01/01/data_report.pdf",
    "file_size": 2048576,
    "mime_type": "application/pdf",
    "checksum": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "is_temporary": false,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
}
```

**Not:** FileUpload modeli relationship'e sahip olmadığı için `include_relationships=True` kullanılsa bile aynı sonuç döner.

### get_by_name()
```python
@with_session
def get_by_name(
    self, 
    session: Session, 
    name: str, 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> Optional[Dict[str, Any]]
```

**Amaç:** File upload'u adına göre getir

**Parametreler:**
- `name` (str): Dosya adı (file_name.extension)
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `Optional[Dict[str, Any]]`
- **Başarılı:** File upload dictionary'si
- **Bulunamadı:** None
- **Hata:** OrchestrationError

**Örnek Dönüş:**
```json
{
    "id": "FU-A1B2C3D4E5F6G7H8I",
    "name": "data_report.pdf",
    "filename": "data_report",
    "file_extension": ".pdf",
    "file_path": "/uploads/2024/01/01/data_report.pdf",
    "file_size": 2048576,
    "mime_type": "application/pdf",
    "checksum": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "is_temporary": false,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
}
```

**Örnek Kullanım:**
```python
# Dosyayı adına göre getir
file_info = orchestrator.get_by_name("data_report.pdf")

# Büyük dosyalar için sadece metadata getir
file_metadata = orchestrator.get_by_name(
    "large_dataset.csv",
    exclude_fields=["file_path"]  # Path bilgisini hariç tut
)
```

### get_by_path()
```python
@with_session
def get_by_path(
    self, 
    session: Session, 
    file_path: str, 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> Optional[Dict[str, Any]]
```

**Amaç:** File upload'u dosya path'ine göre getir

**Parametreler:**
- `file_path` (str): Dosya path'i (absolute path)
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `Optional[Dict[str, Any]]`
- **Başarılı:** File upload dictionary'si
- **Bulunamadı:** None
- **Hata:** OrchestrationError

**Örnek Dönüş:**
```json
{
    "id": "FU-B2C3D4E5F6G7H8I9J",
    "name": "data_report.pdf",
    "filename": "data_report",
    "file_extension": ".pdf",
    "file_path": "/uploads/2024/01/01/data_report.pdf",
    "file_size": 2048576,
    "mime_type": "application/pdf",
    "checksum": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "is_temporary": false,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
}
```

**Örnek Kullanım:**
```python
# Path'e göre dosya bilgisi getir
file_info = orchestrator.get_by_path("/uploads/2024/01/01/data_report.pdf")

# Dosya varlığını kontrol et
if file_info:
    print(f"File exists: {file_info['name']} ({file_info['file_size']} bytes)")
else:
    print("File not found in database")
```

### delete()
```python
@with_session
def delete(self, session: Session, record_id: str) -> Dict[str, Any]
```

**Amaç:** File upload kaydını sil

**Önemli:** Bu metod sadece veritabanı kaydını siler, fiziksel dosyayı silmez.

**Parametreler:**
- `record_id` (str): File upload ID'si

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Silinen file upload'un dictionary'si
- **Bulunamadı:** DatabaseQueryError
- **Hata:** OrchestrationError

## Kalıtım Edilen Generic CRUD Metodları

### get_by_id()
```python
def get_by_id(
    record_id: str, 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> Optional[Dict[str, Any]]
```

### get_all()
```python
def get_all(
    skip: int = 0, 
    limit: int = 100, 
    order_by: str = None, 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> List[Dict[str, Any]]
```

### count()
```python
def count() -> int
```

### filter()
```python
def filter(
    filters: Dict[str, Any], 
    skip: int = 0, 
    limit: int = 100, 
    order_by_field: str = None, 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> List[Dict[str, Any]]
```

**Örnek Filtre Kullanımı:**
```python
# PDF dosyalarını getir
pdf_files = orchestrator.filter({"file_extension": ".pdf"})

# Geçici dosyaları getir
temp_files = orchestrator.filter({"is_temporary": True})

# Büyük dosyaları getir (1MB'dan büyük)
# Bu durumda özel CRUD metodu gerekebilir (file_size > 1048576)

# MIME type'a göre filtreleme
image_files = orchestrator.filter({"mime_type": "image/jpeg"})

# Belirli tarihten sonra upload edilen dosyalar
from datetime import datetime, timedelta
yesterday = datetime.now() - timedelta(days=1)
recent_files = orchestrator.filter({
    "created_at": f">={yesterday.isoformat()}"
})
```

### count_with_filter()
```python
def count_with_filter(filters: Dict[str, Any]) -> int
```

## FileUpload Alanları

### Temel Dosya Bilgileri
- `id`: File upload ID'si (FU-...)
- `name`: Tam dosya adı (filename.extension)
- `filename`: Base filename (extension olmadan)
- `file_extension`: Dosya uzantısı
- `file_path`: Absolute dosya path'i
- `file_size`: Dosya boyutu (bytes)

### Metadata
- `mime_type`: MIME type (application/pdf, image/jpeg, vb.)
- `checksum`: Dosya integrity kontrolü için checksum
- `is_temporary`: Geçici dosya flag'i

### Timestamps
- `created_at`: Upload zamanı
- `updated_at`: Son güncellenme zamanı

## File Management Patterns

### Upload Workflow
```python
# 1. Dosya upload edildi ve disk'e kaydedildi
file_path = "/uploads/2024/01/01/document.pdf"
file_size = os.path.getsize(file_path)

# 2. Checksum hesapla
import hashlib
with open(file_path, 'rb') as f:
    checksum = hashlib.md5(f.read()).hexdigest()

# 3. Database'e kaydet
file_record = orchestrator.create(
    name="document.pdf",
    file_path=file_path,
    file_size=file_size,
    filename="document",
    file_extension=".pdf",
    mime_type="application/pdf",
    checksum=checksum,
    is_temporary=False
)
```

### File Validation
```python
def validate_file_integrity(file_id):
    """Dosya integrity'sini kontrol et"""
    file_record = orchestrator.get_by_id(file_id)
    if not file_record:
        return False, "File record not found"
    
    file_path = file_record["file_path"]
    stored_checksum = file_record["checksum"]
    
    # Dosya var mı kontrol et
    if not os.path.exists(file_path):
        return False, "Physical file not found"
    
    # Boyut kontrolü
    actual_size = os.path.getsize(file_path)
    if actual_size != file_record["file_size"]:
        return False, f"Size mismatch: expected {file_record['file_size']}, got {actual_size}"
    
    # Checksum kontrolü
    if stored_checksum:
        import hashlib
        with open(file_path, 'rb') as f:
            actual_checksum = hashlib.md5(f.read()).hexdigest()
        if actual_checksum != stored_checksum:
            return False, "Checksum mismatch - file corrupted"
    
    return True, "File is valid"
```

### Temporary File Cleanup
```python
def cleanup_temporary_files(older_than_hours=24):
    """Eski geçici dosyaları temizle"""
    from datetime import datetime, timedelta
    
    cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
    
    # Eski geçici dosyaları getir
    temp_files = orchestrator.filter({
        "is_temporary": True,
        "created_at": f"<{cutoff_time.isoformat()}"
    })
    
    cleaned_count = 0
    for file_record in temp_files:
        try:
            # Fiziksel dosyayı sil
            if os.path.exists(file_record["file_path"]):
                os.remove(file_record["file_path"])
            
            # Database kaydını sil
            orchestrator.delete(file_record["id"])
            cleaned_count += 1
        except Exception as e:
            print(f"Error cleaning file {file_record['name']}: {e}")
    
    return cleaned_count
```

## File Type Analysis

### MIME Type Distribution
```python
def analyze_file_types():
    """Upload edilen dosya tiplerini analiz et"""
    all_files = orchestrator.get_all()
    
    # MIME type dağılımı
    mime_distribution = {}
    extension_distribution = {}
    
    for file_record in all_files:
        # MIME type analizi
        mime_type = file_record.get("mime_type", "unknown")
        mime_distribution[mime_type] = mime_distribution.get(mime_type, 0) + 1
        
        # Extension analizi
        extension = file_record.get("file_extension", "unknown")
        extension_distribution[extension] = extension_distribution.get(extension, 0) + 1
    
    return {
        "mime_types": mime_distribution,
        "extensions": extension_distribution
    }
```

### Size Analysis
```python
def analyze_file_sizes():
    """Dosya boyutlarını analiz et"""
    all_files = orchestrator.get_all()
    
    sizes = [f["file_size"] for f in all_files]
    
    if not sizes:
        return {}
    
    return {
        "total_files": len(sizes),
        "total_size_bytes": sum(sizes),
        "average_size_bytes": sum(sizes) / len(sizes),
        "min_size_bytes": min(sizes),
        "max_size_bytes": max(sizes),
        "total_size_mb": sum(sizes) / (1024 * 1024)
    }
```

## Storage Management

### Disk Usage Monitoring
```python
def get_storage_usage():
    """Disk kullanımını hesapla"""
    all_files = orchestrator.get_all()
    
    total_size = sum(f["file_size"] for f in all_files)
    temp_size = sum(f["file_size"] for f in all_files if f["is_temporary"])
    permanent_size = total_size - temp_size
    
    return {
        "total_files": len(all_files),
        "total_size_bytes": total_size,
        "total_size_mb": total_size / (1024 * 1024),
        "temporary_size_mb": temp_size / (1024 * 1024),
        "permanent_size_mb": permanent_size / (1024 * 1024)
    }
```

### Duplicate Detection
```python
def find_duplicate_files():
    """Aynı checksum'a sahip dosyaları bul"""
    all_files = orchestrator.get_all()
    
    checksum_map = {}
    duplicates = {}
    
    for file_record in all_files:
        checksum = file_record.get("checksum")
        if checksum:
            if checksum in checksum_map:
                if checksum not in duplicates:
                    duplicates[checksum] = [checksum_map[checksum]]
                duplicates[checksum].append(file_record)
            else:
                checksum_map[checksum] = file_record
    
    return duplicates
```

## Security Considerations

### File Access Control
```python
def check_file_access_permission(file_id, user_id):
    """Dosya erişim iznini kontrol et"""
    file_record = orchestrator.get_by_id(file_id)
    if not file_record:
        return False, "File not found"
    
    # Geçici dosyalara sadece upload eden erişebilir
    if file_record["is_temporary"]:
        # uploaded_by alanı varsa kontrol et
        # Şu anda models.py'de bu alan yok, gelecekte eklenebilir
        pass
    
    return True, "Access granted"
```

### File Path Validation
```python
def validate_file_path(file_path):
    """Dosya path'inin güvenli olduğunu kontrol et"""
    import os.path
    
    # Path traversal saldırılarını önle
    if ".." in file_path:
        return False, "Path traversal not allowed"
    
    # Absolute path olmalı
    if not os.path.isabs(file_path):
        return False, "Path must be absolute"
    
    # İzin verilen dizinlerde olmalı
    allowed_dirs = ["/uploads", "/data", "/temp"]
    if not any(file_path.startswith(allowed) for allowed in allowed_dirs):
        return False, "Path not in allowed directories"
    
    return True, "Path is valid"
```

## Best Practices

### File Naming
```python
# Önerilen dosya adlandırma pattern'ları
def generate_safe_filename(original_name):
    """Güvenli dosya adı oluştur"""
    import re
    from datetime import datetime
    
    # Özel karakterleri temizle
    safe_name = re.sub(r'[^\w\-_.]', '_', original_name)
    
    # Timestamp ekle (uniqueness için)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(safe_name)
    
    return f"{name}_{timestamp}{ext}"
```

### Upload Size Limits
```python
def check_upload_limits(file_size, file_extension):
    """Upload limitlerini kontrol et"""
    # Dosya boyutu limitleri (bytes)
    size_limits = {
        ".pdf": 10 * 1024 * 1024,    # 10MB
        ".jpg": 5 * 1024 * 1024,     # 5MB
        ".png": 5 * 1024 * 1024,     # 5MB
        ".csv": 50 * 1024 * 1024,    # 50MB
        ".txt": 1 * 1024 * 1024,     # 1MB
    }
    
    # İzin verilen uzantılar
    allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".csv", ".txt", ".json"}
    
    if file_extension not in allowed_extensions:
        return False, f"File type {file_extension} not allowed"
    
    max_size = size_limits.get(file_extension, 1024 * 1024)  # Default 1MB
    if file_size > max_size:
        return False, f"File too large: {file_size} bytes (max: {max_size})"
    
    return True, "Upload limits OK"
```

## Hata Durumları

### File Upload Hataları
```python
# Dosya adı boşsa
ValidationError("File name is required")

# Aynı isimde dosya varsa
ValidationError("File name already exists")

# Aynı path'de dosya varsa
ValidationError("File path already exists")

# Geçersiz dosya boyutu
ValidationError("Invalid file size")

# Path validation başarısızsa
ValidationError("Invalid file path")
```

### File Access Hataları
```python
# Dosya bulunamazsa
DatabaseQueryError("File upload 'FU-...' not found")

# Fiziksel dosya bulunamazsa (validation'da)
FileNotFoundError("Physical file not found at path")

# Permission hatası
PermissionError("Access denied to file")
```
