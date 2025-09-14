# ScriptOrchestrator API Documentation

ScriptOrchestrator, script yönetimi ve CRUD operasyonlarını yürütür.

## Genel Bilgiler

- **Sınıf:** `ScriptOrchestrator`
- **Parent:** `BaseOrchestrator`
- **Modül:** `miniflow.database.orchestration.script_orchestrator`
- **Primary Model:** `Script`
- **Primary CRUD:** `script_crud`

## Script-Specific Metodlar

### create()
```python
@with_session
def create(self, session: Session, name: str, content: str, **kwargs) -> Dict[str, Any]
```

**Amaç:** Yeni script oluştur

**Parametreler:**
- `name` (str): Script adı (zorunlu, unique)
- `content` (str): Script içeriği (zorunlu)
- `**kwargs`: Diğer script alanları
  - `description` (str): Açıklama
  - `version` (str): Versiyon (default: "1.0.0")
  - `category` (str): Kategori (zorunlu)
  - `subcategory` (str): Alt kategori
  - `file_extension` (str): Dosya uzantısı (.py, .sh, .js, vb.)
  - `required_packages` (list): Gerekli paketler
  - `input_schema` (dict): Input JSON schema
  - `output_schema` (dict): Output JSON schema
  - `tags` (list): Etiketler
  - `author` (str): Yazar

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Oluşturulan script'in dictionary'si
- **Hata:** OrchestrationError

**Örnek Dönüş (Temel):**
```json
{
    "id": "SC-A1B2C3D4E5F6G7H8I",
    "name": "data_processor",
    "description": "Processes CSV data files",
    "version": "1.0.0",
    "category": "data_processing",
    "subcategory": "etl",
    "file_extension": ".py",
    "content": "import pandas as pd\ndef process_data():\n    pass",
    "required_packages": ["pandas==1.5.0"],
    "input_schema": {"type": "object", "properties": {"file_path": {"type": "string"}}},
    "output_schema": {"type": "object", "properties": {"processed_rows": {"type": "integer"}}},
    "test_status": "UNTESTED",
    "test_coverage": null,
    "avg_execution_time": null,
    "success_rate": null,
    "total_executions": 0,
    "tags": ["etl", "csv", "pandas"],
    "author": "Data Team",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
}
```

**Örnek Dönüş (include_relationships=True):**
```json
{
    "id": "SC-A1B2C3D4E5F6G7H8I",
    "name": "data_processor",
    "description": "Processes CSV data files",
    "version": "1.0.0",
    "category": "data_processing",
    "subcategory": "etl",
    "file_extension": ".py",
    "content": "import pandas as pd\ndef process_data():\n    pass",
    "required_packages": ["pandas==1.5.0"],
    "input_schema": {"type": "object", "properties": {"file_path": {"type": "string"}}},
    "output_schema": {"type": "object", "properties": {"processed_rows": {"type": "integer"}}},
    "test_status": "PASSED",
    "test_coverage": 85.5,
    "avg_execution_time": 45.2,
    "success_rate": 0.95,
    "total_executions": 150,
    "tags": ["etl", "csv", "pandas"],
    "author": "Data Team",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00",
    "nodes": [
        {
            "id": "ND-B2C3D4E5F6G7H8I9J",
            "workflow_id": "WF-C3D4E5F6G7H8I9J0K",
            "script_id": "SC-A1B2C3D4E5F6G7H8I",
            "name": "CSV Processor Node",
            "description": "Processes CSV files in workflow",
            "params": {"input_path": "/data/input.csv", "batch_size": 1000},
            "max_retries": 3,
            "timeout_seconds": 300
        },
        {
            "id": "ND-D4E5F6G7H8I9J0K1L",
            "workflow_id": "WF-E5F6G7H8I9J0K1L2M",
            "script_id": "SC-A1B2C3D4E5F6G7H8I",
            "name": "Data Validator",
            "description": "Validates processed data",
            "params": {"validation_rules": ["not_null", "unique_id"]},
            "max_retries": 2,
            "timeout_seconds": 180
        }
    ]
}
```

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

**Amaç:** Script'i adına göre getir

**Parametreler:**
- `name` (str): Script adı
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `Optional[Dict[str, Any]]`
- **Başarılı:** Script dictionary'si
- **Bulunamadı:** None
- **Hata:** OrchestrationError

**Örnek Dönüş (Temel):**
```json
{
    "id": "SC-A1B2C3D4E5F6G7H8I",
    "name": "data_processor",
    "description": "Processes CSV data files",
    "version": "1.0.0",
    "category": "data_processing",
    "subcategory": "etl",
    "file_extension": ".py",
    "test_status": "PASSED",
    "test_coverage": 85.5,
    "avg_execution_time": 45.2,
    "success_rate": 0.95,
    "total_executions": 150,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
}
```

**Örnek Dönüş (include_relationships=True):**
```json
{
    "id": "SC-A1B2C3D4E5F6G7H8I",
    "name": "data_processor",
    "description": "Processes CSV data files",
    "version": "1.0.0",
    "category": "data_processing",
    "subcategory": "etl",
    "file_extension": ".py",
    "test_status": "PASSED",
    "test_coverage": 85.5,
    "avg_execution_time": 45.2,
    "success_rate": 0.95,
    "total_executions": 150,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00",
    "nodes": [
        {
            "id": "ND-B2C3D4E5F6G7H8I9J",
            "workflow_id": "WF-C3D4E5F6G7H8I9J0K",
            "script_id": "SC-A1B2C3D4E5F6G7H8I",
            "name": "CSV Processor Node",
            "description": "Processes CSV files in workflow",
            "params": {"input_path": "/data/input.csv", "batch_size": 1000},
            "max_retries": 3,
            "timeout_seconds": 300
        }
    ]
}
```

### delete()
```python
@with_session
def delete(self, session: Session, record_id: str) -> Dict[str, Any]
```

**Amaç:** Script'i sil

**Silme Etkisi:**
- Script'e bağlı node'lar script_id=null olur (SET NULL)

**Parametreler:**
- `record_id` (str): Script ID'si

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Silinen script'in dictionary'si
- **Bulunamadı:** DatabaseQueryError
- **Hata:** OrchestrationError

### update()
```python
@with_session
def update(self, session: Session, record_id: str, **kwargs) -> Dict[str, Any]
```

**Amaç:** Script'i güvenli şekilde güncelle

**GÜVENLİK KISITLAMALARI:**
- **Değiştirilemez alanlar:** name, category, subcategory, file_path, file_size
- **Bu alanlar file_path'i etkiler ve BFF katmanında yönetilir**

**Parametreler:**
- `record_id` (str): Script ID'si (zorunlu)
- `**kwargs`: Güncellenecek alanlar

**İzin Verilen Alanlar:**
- `content` (str): Script kodu
- `description` (str): Açıklama
- `version` (str): Versiyon
- `file_extension` (str): Dosya uzantısı
- `required_packages` (list): Bağımlılıklar
- `input_schema` (dict): Giriş şeması
- `output_schema` (dict): Çıkış şeması
- `test_input_params` (dict): Test girişleri
- `test_output_params` (dict): Test çıkışları
- `tags` (list): Etiketler
- `author` (str): Yazar
- `documentation_url` (str): Dokümantasyon URL

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Güncellenmiş script'in dictionary'si
- **Bulunamadı:** DatabaseQueryError
- **Geçersiz Alan:** ValidationError
- **Hata:** OrchestrationError

**Örnek Kullanım:**
```python
# Schema ve content güncelleme
updated_script = orchestrator.update(
    record_id="SC-123456789",
    content="import pandas as pd\ndef process():\n    return 'updated'",
    version="2.0.0",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string"},
            "encoding": {"type": "string", "default": "utf-8"}
        }
    },
    output_schema={
        "type": "object",
        "properties": {
            "result": {"type": "string"},
            "rows_processed": {"type": "integer"}
        }
    },
    test_input_params={
        "file_path": "/test/sample.csv",
        "encoding": "utf-8"
    },
    test_output_params={
        "result": "success",
        "rows_processed": 1000
    }
)
```

**Güvenlik Uyarıları:**
```python
# ❌ Bu alanlar göz ardı edilir ve uyarı loglanır
orchestrator.update(
    record_id="SC-123456789",
    name="new_name",          # IGNORED - file_path'i etkiler
    category="new_category",  # IGNORED - file_path'i etkiler
    file_path="/malicious"    # IGNORED - BFF tarafından yönetilir
)
```

### get_content()
```python
@with_session
def get_content(self, session: Session, record_id: str) -> Dict[str, Any]
```

**Amaç:** Script'in sadece content alanını getir

**Parametreler:**
- `record_id` (str): Script ID'si

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** `{"content": "script_content"}`
- **Bulunamadı:** None
- **Hata:** OrchestrationError

**Örnek Dönüş:**
```json
{
    "content": "import pandas as pd\n\ndef process_data(input_file):\n    df = pd.read_csv(input_file)\n    return df.shape[0]"
}
```

### set_content()
```python
@with_session
def set_content(self, session: Session, record_id: str, content: str) -> Dict[str, Any]
```

**Amaç:** Script'in content alanını güncelle

**Parametreler:**
- `record_id` (str): Script ID'si
- `content` (str): Yeni script içeriği

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Güncellenen script'in dictionary'si
- **Hata:** OrchestrationError

### get_test_stats()
```python
@with_session
def get_test_stats(self, session: Session, record_id: str) -> Dict[str, Any]
```

**Amaç:** Script'in test istatistiklerini getir

**Parametreler:**
- `record_id` (str): Script ID'si

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Test istatistikleri
- **Hata:** OrchestrationError

**Örnek Dönüş:**
```json
{
    "test_status": "PASSED",
    "test_coverage": 85.5,
    "last_test_run_at": "2024-01-01T10:00:00",
    "test_results": {
        "total_tests": 15,
        "passed": 14,
        "failed": 1,
        "errors": []
    }
}
```

### get_performance_stats()
```python
@with_session
def get_performance_stats(self, session: Session, record_id: str) -> Dict[str, Any]
```

**Amaç:** Script'in performans istatistiklerini getir

**Parametreler:**
- `record_id` (str): Script ID'si

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Performans istatistikleri
- **Hata:** OrchestrationError

**Örnek Dönüş:**
```json
{
    "avg_execution_time": 2.5,
    "min_execution_time": 1.2,
    "max_execution_time": 5.8,
    "success_rate": 0.95,
    "total_executions": 1250
}
```

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
# Belirli kategorideki script'leri getir
data_scripts = orchestrator.filter({"category": "data_processing"})

# Python script'lerini getir
python_scripts = orchestrator.filter({"file_extension": ".py"})

# Test edilmiş script'leri getir
tested_scripts = orchestrator.filter({"test_status": "PASSED"})

# Yüksek başarı oranına sahip script'leri getir
reliable_scripts = orchestrator.filter({"success_rate": 0.9})

# Belirli tag'e sahip script'leri getir (JSON query gerekebilir)
# Bu durumda özel CRUD metodu kullanılmalı
```

### count_with_filter()
```python
def count_with_filter(filters: Dict[str, Any]) -> int
```

## Script Test Status

```python
class ScriptTestStatus(str, enum.Enum):
    UNTESTED = "UNTESTED"   # Test edilmemiş
    PASSED = "PASSED"       # Test başarılı
    FAILED = "FAILED"       # Test başarısız
```

## Script Kategorileri

Script'ler kategori bazında organize edilir:
- `category`: Ana kategori (data_processing, notification, file_management, vb.)
- `subcategory`: Alt kategori (etl, validation, cleanup, vb.)

## Script İlişkileri

Script modeli şu ilişkilere sahiptir:
- `nodes` (List[Node]): Bu script'i kullanan node'lar

Bu ilişki `include_relationships=True` ile dahil edilebilir.

## Schema Tanımları

### input_schema
Script'in beklediği input parametrelerinin JSON Schema tanımı:
```json
{
    "type": "object",
    "properties": {
        "input_file": {
            "type": "string",
            "description": "Path to input CSV file"
        },
        "output_dir": {
            "type": "string", 
            "description": "Output directory path"
        },
        "batch_size": {
            "type": "integer",
            "minimum": 1,
            "default": 1000
        }
    },
    "required": ["input_file", "output_dir"]
}
```

### output_schema
Script'in döndürdüğü output'un JSON Schema tanımı:
```json
{
    "type": "object",
    "properties": {
        "processed_rows": {
            "type": "integer",
            "description": "Number of processed rows"
        },
        "output_file": {
            "type": "string",
            "description": "Path to output file"
        },
        "execution_time": {
            "type": "number",
            "description": "Execution time in seconds"
        }
    }
}
```

## Performans Metrikleri

Script'ler otomatik olarak performans metriklerini takip eder:
- `avg_execution_time`: Ortalama çalışma süresi (saniye)
- `min_execution_time`: Minimum çalışma süresi
- `max_execution_time`: Maksimum çalışma süresi
- `success_rate`: Başarı oranı (0.0 - 1.0)
- `total_executions`: Toplam çalıştırılma sayısı

## Hata Durumları

### Script Oluşturma Hataları
```python
# İsim boşsa
ValidationError("Script name is required")

# Aynı isimde script varsa
ValidationError("Script name already exists")

# Content boşsa
ValidationError("Script content is required")

# Kategori boşsa
ValidationError("Script category is required")
```

### Script Silme Hataları
```python
# Script bulunamazsa
DatabaseQueryError("Script 'SC-...' not found")

# Aktif node'larda kullanılıyorsa (uyarı, ama silme devam eder)
# Node'lar script_id=null olur
```

## En İyi Uygulamalar

### Content Yönetimi
```python
# Büyük script'ler için sadece content'i getir
content = script_orchestrator.get_content("SC-A1B2C3D4E5F6G7H8I")

# Content güncelleme
updated_script = script_orchestrator.set_content(
    "SC-A1B2C3D4E5F6G7H8I",
    new_content
)
```

### Schema Kullanımı
Input/output schema'ları script validation ve documentation için kullanılır:
```python
script_data = {
    "name": "csv_processor",
    "content": "...",
    "category": "data_processing",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string"}
        },
        "required": ["file_path"]
    },
    "output_schema": {
        "type": "object", 
        "properties": {
            "row_count": {"type": "integer"}
        }
    }
}
```
