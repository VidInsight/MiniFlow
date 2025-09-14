# ExecutionOutputOrchestrator API Documentation

ExecutionOutputOrchestrator, execution output monitoring ve READ-ONLY operasyonlarını yürütür.

## Genel Bilgiler

- **Sınıf:** `ExecutionOutputOrchestrator`
- **Parent:** `BaseOrchestrator`
- **Modül:** `miniflow.database.orchestration.execution_output_orchestrator`
- **Primary Model:** `ExecutionOutput`
- **Primary CRUD:** `execution_output_crud`
- **Özellik:** READ-ONLY (sadece okuma operasyonları)

## ExecutionOutput-Specific Metodlar

### get_by_execution()
```python
@with_session
def get_by_execution(
    self, 
    session: Session, 
    execution_id: str, 
    skip: int = 0, 
    limit: int = 100
) -> List[Dict[str, Any]]
```

**Not:** Bu metod `include_relationships` parametresine sahip değildir. Temel serialization kullanır.

**Amaç:** Belirli bir execution'ın output'larını getir

**Parametreler:**
- `execution_id` (str): Execution ID'si
- `skip` (int): Atlanacak kayıt sayısı (default: 0)
- `limit` (int): Maksimum kayıt sayısı (default: 100)

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** ExecutionOutput dictionary'lerinin listesi
- **Boş:** []
- **Hata:** OrchestrationError

**Örnek Dönüş (Temel):**
```json
[
    {
        "id": "EO-A1B2C3D4E5F6G7H8I",
        "execution_id": "EX-B2C3D4E5F6G7H8I9J",
        "workflow_id": "WF-C3D4E5F6G7H8I9J0K",
        "node_id": "ND-D4E5F6G7H8I9J0K1L",
        "status": "SUCCESS",
        "result_data": {
            "processed_rows": 1500,
            "output_file": "/data/output/processed_data.csv",
            "execution_time": 45.2,
            "memory_usage": "512MB"
        },
        "started_at": "2024-01-01T10:00:00",
        "ended_at": "2024-01-01T10:00:45",
        "created_at": "2024-01-01T10:00:00",
        "updated_at": "2024-01-01T10:00:45"
    },
    {
        "id": "EO-B2C3D4E5F6G7H8I9J",
        "execution_id": "EX-B2C3D4E5F6G7H8I9J",
        "workflow_id": "WF-C3D4E5F6G7H8I9J0K",
        "node_id": "ND-E5F6G7H8I9J0K1L2M",
        "status": "FAILED",
        "result_data": {
            "error": "File not found",
            "error_code": "FILE_NOT_FOUND",
            "stack_trace": "FileNotFoundError: /data/input/missing.csv",
            "execution_time": 2.1
        },
        "started_at": "2024-01-01T10:01:00",
        "ended_at": "2024-01-01T10:01:02",
        "created_at": "2024-01-01T10:01:00",
        "updated_at": "2024-01-01T10:01:02"
    }
]
```

**Örnek Dönüş (include_relationships=True):**
```json
[
    {
        "id": "EO-A1B2C3D4E5F6G7H8I",
        "execution_id": "EX-B2C3D4E5F6G7H8I9J",
        "workflow_id": "WF-C3D4E5F6G7H8I9J0K",
        "node_id": "ND-D4E5F6G7H8I9J0K1L",
        "status": "SUCCESS",
        "result_data": {
            "processed_rows": 1500,
            "output_file": "/data/output/processed_data.csv",
            "execution_time": 45.2,
            "memory_usage": "512MB",
            "performance_metrics": {
                "rows_per_second": 33.3,
                "throughput": "2.1MB/s"
            }
        },
        "started_at": "2024-01-01T10:00:00",
        "ended_at": "2024-01-01T10:00:45",
        "created_at": "2024-01-01T10:00:00",
        "updated_at": "2024-01-01T10:00:45",
        "execution": {
            "id": "EX-B2C3D4E5F6G7H8I9J",
            "workflow_id": "WF-C3D4E5F6G7H8I9J0K",
            "status": "COMPLETED",
            "pending_nodes": 0,
            "executed_nodes": 2,
            "results": {"total_processed": 1500},
            "started_at": "2024-01-01T10:00:00",
            "ended_at": "2024-01-01T10:00:45"
        },
        "workflow": {
            "id": "WF-C3D4E5F6G7H8I9J0K",
            "name": "Data Processing Workflow",
            "description": "Processes daily data files",
            "status": "ACTIVE",
            "priority": 1
        },
        "node": {
            "id": "ND-D4E5F6G7H8I9J0K1L",
            "workflow_id": "WF-C3D4E5F6G7H8I9J0K",
            "script_id": "SC-F6G7H8I9J0K1L2M3N",
            "name": "Data Processor",
            "description": "Processes CSV data files",
            "params": {"input_path": "/data/input.csv", "batch_size": 1000},
            "max_retries": 3,
            "timeout_seconds": 300
        }
    },
    {
        "id": "EO-B2C3D4E5F6G7H8I9J",
        "execution_id": "EX-B2C3D4E5F6G7H8I9J",
        "workflow_id": "WF-C3D4E5F6G7H8I9J0K",
        "node_id": "ND-E5F6G7H8I9J0K1L2M",
        "status": "FAILED",
        "result_data": {
            "error": "File not found",
            "error_code": "FILE_NOT_FOUND",
            "error_type": "FileNotFoundError",
            "stack_trace": "FileNotFoundError: /data/input/missing.csv",
            "execution_time": 2.1,
            "failed_at_step": "file_validation"
        },
        "started_at": "2024-01-01T10:01:00",
        "ended_at": "2024-01-01T10:01:02",
        "created_at": "2024-01-01T10:01:00",
        "updated_at": "2024-01-01T10:01:02",
        "execution": {
            "id": "EX-B2C3D4E5F6G7H8I9J",
            "workflow_id": "WF-C3D4E5F6G7H8I9J0K",
            "status": "FAILED",
            "pending_nodes": 1,
            "executed_nodes": 1,
            "results": {"error": "Node execution failed", "failed_node": "ND-E5F6G7H8I9J0K1L2M"},
            "started_at": "2024-01-01T10:01:00",
            "ended_at": "2024-01-01T10:01:02"
        },
        "workflow": {
            "id": "WF-C3D4E5F6G7H8I9J0K",
            "name": "Data Processing Workflow",
            "description": "Processes daily data files",
            "status": "ACTIVE",
            "priority": 1
        },
        "node": {
            "id": "ND-E5F6G7H8I9J0K1L2M",
            "workflow_id": "WF-C3D4E5F6G7H8I9J0K",
            "script_id": "SC-G7H8I9J0K1L2M3N4O",
            "name": "File Validator",
            "description": "Validates input files exist",
            "params": {"input_file": "/data/input/missing.csv"},
            "max_retries": 3,
            "timeout_seconds": 60
        }
    }
]
```

### get_by_workflow()
```python
@with_session
def get_by_workflow(
    self, 
    session: Session, 
    workflow_id: str, 
    skip: int = 0, 
    limit: int = 100
) -> List[Dict[str, Any]]
```

**Not:** Bu metod `include_relationships` parametresine sahip değildir. Temel serialization kullanır.

**Amaç:** Belirli bir workflow'un execution output'larını getir

**Parametreler:**
- `workflow_id` (str): Workflow ID'si
- `skip` (int): Atlanacak kayıt sayısı
- `limit` (int): Maksimum kayıt sayısı

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** ExecutionOutput dictionary'lerinin listesi
- **Boş:** []
- **Hata:** OrchestrationError

### get_by_node()
```python
@with_session
def get_by_node(
    self, 
    session: Session, 
    node_id: str, 
    skip: int = 0, 
    limit: int = 100
) -> List[Dict[str, Any]]
```

**Not:** Bu metod `include_relationships` parametresine sahip değildir. Temel serialization kullanır.

**Amaç:** Belirli bir node'un execution output'larını getir

**Parametreler:**
- `node_id` (str): Node ID'si
- `skip` (int): Atlanacak kayıt sayısı
- `limit` (int): Maksimum kayıt sayısı

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** ExecutionOutput dictionary'lerinin listesi
- **Boş:** []
- **Hata:** OrchestrationError

### get_by_status()
```python
@with_session
def get_by_status(
    self, 
    session: Session, 
    status: str, 
    skip: int = 0, 
    limit: int = 100
) -> List[Dict[str, Any]]
```

**Not:** Bu metod `include_relationships` parametresine sahip değildir. Temel serialization kullanır.

**Amaç:** Belirli statüdeki execution output'ları getir

**Parametreler:**
- `status` (str): ExecutionOutput status'u
- `skip` (int): Atlanacak kayıt sayısı
- `limit` (int): Maksimum kayıt sayısı

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** Filtrelenmiş ExecutionOutput dictionary'lerinin listesi
- **Boş:** []
- **Hata:** OrchestrationError

**Örnek Kullanım:**
```python
# Başarılı output'ları getir
successful_outputs = orchestrator.get_by_status("SUCCESS")

# Başarısız output'ları getir
failed_outputs = orchestrator.get_by_status("FAILED", limit=50)

# Timeout olan output'ları getir
timeout_outputs = orchestrator.get_by_status("TIMEOUT")

# İptal edilen output'ları getir
cancelled_outputs = orchestrator.get_by_status("CANCELLED")
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
# Belirli execution ve status kombinasyonu
failed_in_execution = orchestrator.filter({
    "execution_id": "EX-A1B2C3D4E5F6G7H8I",
    "status": "FAILED"
})

# Belirli tarih aralığındaki output'lar
from datetime import datetime
today = datetime.now().date()
today_outputs = orchestrator.filter({
    "started_at": f">={today.isoformat()}"
})

# Uzun süren execution'ları bul (result_data'da execution_time > 60)
# Bu durumda özel CRUD metodu veya complex query gerekebilir
```

### count_with_filter()
```python
def count_with_filter(filters: Dict[str, Any]) -> int
```

## ExecutionOutput Status Değerleri

```python
class ExecutionOutputStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"       # Başarılı
    FAILED = "FAILED"         # Başarısız
    TIMEOUT = "TIMEOUT"       # Zaman aşımı
    CANCELLED = "CANCELLED"   # İptal edildi
```

## ExecutionOutput Alanları

### Temel Alanlar
- `id`: ExecutionOutput ID'si (EO-...)
- `execution_id`: Bağlı execution ID'si
- `workflow_id`: Bağlı workflow ID'si
- `node_id`: Bağlı node ID'si
- `status`: Output status'u

### Timing Alanları
- `started_at`: Node başlangıç zamanı
- `ended_at`: Node bitiş zamanı
- `created_at`: Kayıt oluşturulma zamanı
- `updated_at`: Kayıt güncellenme zamanı

### Result Data Alanı
`result_data` alanı node'un çalışma sonuçlarını JSON formatında tutar.

## Result Data Formatları

### Başarılı Execution Result
```json
{
    "result_data": {
        "processed_rows": 1500,
        "output_file": "/data/output/processed_data.csv",
        "execution_time": 45.2,
        "memory_usage": "512MB",
        "cpu_usage": "25%",
        "performance_metrics": {
            "rows_per_second": 33.2,
            "throughput": "2.1MB/s"
        },
        "output_summary": {
            "total_records": 1500,
            "valid_records": 1487,
            "invalid_records": 13,
            "skipped_records": 0
        }
    }
}
```

### Başarısız Execution Result
```json
{
    "result_data": {
        "error": "File not found",
        "error_code": "FILE_NOT_FOUND",
        "error_type": "FileNotFoundError",
        "error_message": "Input file '/data/input/missing.csv' does not exist",
        "stack_trace": "Traceback (most recent call last):\n  File...",
        "execution_time": 2.1,
        "failed_at_step": "file_validation",
        "recovery_suggestions": [
            "Check if input file exists",
            "Verify file permissions",
            "Check network connectivity"
        ]
    }
}
```

### Timeout Execution Result
```json
{
    "result_data": {
        "error": "Execution timeout",
        "error_code": "TIMEOUT",
        "timeout_seconds": 300,
        "execution_time": 300.0,
        "partial_results": {
            "processed_rows": 750,
            "completion_percentage": 50.0
        },
        "last_operation": "data_transformation",
        "memory_usage_at_timeout": "1.2GB"
    }
}
```

### Cancelled Execution Result
```json
{
    "result_data": {
        "cancellation_reason": "User requested cancellation",
        "cancelled_at": "2024-01-01T10:02:30",
        "execution_time": 150.0,
        "partial_results": {
            "processed_rows": 600,
            "completion_percentage": 40.0
        },
        "cleanup_status": "completed",
        "resources_released": true
    }
}
```

## İlişkiler

ExecutionOutput modeli şu ilişkilere sahiptir:
- `execution` (Execution): Bağlı execution
- `workflow` (Workflow): Bağlı workflow
- `node` (Node): Bağlı node

**İlişkilerle Örnek Dönüş:**
```json
{
    "id": "EO-A1B2C3D4E5F6G7H8I",
    "execution_id": "EX-B2C3D4E5F6G7H8I9J",
    "workflow_id": "WF-C3D4E5F6G7H8I9J0K",
    "node_id": "ND-D4E5F6G7H8I9J0K1L",
    "status": "SUCCESS",
    "result_data": {"processed_rows": 1500},
    "execution": {
        "id": "EX-B2C3D4E5F6G7H8I9J",
        "status": "COMPLETED"
    },
    "workflow": {
        "id": "WF-C3D4E5F6G7H8I9J0K",
        "name": "Data Processing Workflow"
    },
    "node": {
        "id": "ND-D4E5F6G7H8I9J0K1L",
        "name": "Data Processor",
        "script_id": "SC-E5F6G7H8I9J0K1L2M"
    }
}
```

## Monitoring ve Analytics

### Success Rate Analysis
```python
# Node'un başarı oranını hesapla
node_outputs = orchestrator.get_by_node("ND-A1B2C3D4E5F6G7H8I")

success_count = len([o for o in node_outputs if o["status"] == "SUCCESS"])
total_count = len(node_outputs)
success_rate = success_count / total_count if total_count > 0 else 0

print(f"Node success rate: {success_rate:.2%}")
```

### Performance Analysis
```python
# Execution sürelerini analiz et
successful_outputs = orchestrator.get_by_status("SUCCESS")

execution_times = []
for output in successful_outputs:
    result_data = output.get("result_data", {})
    exec_time = result_data.get("execution_time")
    if exec_time:
        execution_times.append(exec_time)

if execution_times:
    avg_time = sum(execution_times) / len(execution_times)
    min_time = min(execution_times)
    max_time = max(execution_times)
    
    print(f"Average execution time: {avg_time:.2f}s")
    print(f"Min execution time: {min_time:.2f}s")
    print(f"Max execution time: {max_time:.2f}s")
```

### Error Analysis
```python
# Hata tiplerini analiz et
failed_outputs = orchestrator.get_by_status("FAILED")

error_types = {}
for output in failed_outputs:
    result_data = output.get("result_data", {})
    error_code = result_data.get("error_code", "UNKNOWN")
    error_types[error_code] = error_types.get(error_code, 0) + 1

print("Error distribution:")
for error_code, count in error_types.items():
    print(f"  {error_code}: {count}")
```

### Resource Usage Analysis
```python
# Memory ve CPU kullanımını analiz et
successful_outputs = orchestrator.get_by_status("SUCCESS")

memory_usage = []
cpu_usage = []

for output in successful_outputs:
    result_data = output.get("result_data", {})
    
    # Memory usage parsing (örnek: "512MB" -> 512)
    mem_str = result_data.get("memory_usage", "")
    if mem_str.endswith("MB"):
        memory_usage.append(float(mem_str[:-2]))
    
    # CPU usage parsing (örnek: "25%" -> 25)
    cpu_str = result_data.get("cpu_usage", "")
    if cpu_str.endswith("%"):
        cpu_usage.append(float(cpu_str[:-1]))

if memory_usage:
    avg_memory = sum(memory_usage) / len(memory_usage)
    print(f"Average memory usage: {avg_memory:.1f}MB")

if cpu_usage:
    avg_cpu = sum(cpu_usage) / len(cpu_usage)
    print(f"Average CPU usage: {avg_cpu:.1f}%")
```

## Önemli Notlar

### READ-ONLY Özellik
ExecutionOutputOrchestrator sadece okuma operasyonları sağlar:
- ❌ **create()** - Output'lar engine tarafından oluşturulur
- ❌ **update()** - Output'lar engine tarafından güncellenir
- ❌ **delete()** - Output'lar execution silinirken cascade olarak silinir
- ✅ **get/filter/count** - Tüm okuma operasyonları mevcut

### Result Data Usage
- JSON formatında esnek veri depolama
- Her node kendi result formatını belirleyebilir
- Standart alanlar: execution_time, memory_usage, error_code
- Performance metrikleri için zengin veri

### Performance Considerations
- Büyük result_data'lar performansı etkileyebilir
- Sık sorgularda `exclude_fields=["result_data"]` kullanabilirsiniz
- Pagination büyük veri setleri için önemli
- Index'ler status ve timestamp alanlarında mevcut olmalı

### Monitoring Best Practices
- Düzenli olarak başarısız execution'ları analiz edin
- Performance trendlerini takip edin
- Resource usage'ı monitör edin
- Error pattern'larını belirleyin ve önleyici aksiyonlar alın
