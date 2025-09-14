# ExecutionOrchestrator API Documentation

ExecutionOrchestrator, execution monitoring ve READ-ONLY operasyonlarını yürütür.

## Genel Bilgiler

- **Sınıf:** `ExecutionOrchestrator`
- **Parent:** `BaseOrchestrator`
- **Modül:** `miniflow.database.orchestration.execution_orchestrator`
- **Primary Model:** `Execution`
- **Primary CRUD:** `execution_crud`
- **Özellik:** READ-ONLY (sadece okuma operasyonları)

## Execution-Specific Metodlar

### get_by_workflow()
```python
@with_session
def get_by_workflow(
    self, 
    session: Session, 
    workflow_id: str, 
    skip: int = 0, 
    limit: int = 100, 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> List[Dict[str, Any]]
```

**Amaç:** Belirli bir workflow'un execution'larını getir

**Parametreler:**
- `workflow_id` (str): Workflow ID'si
- `skip` (int): Atlanacak kayıt sayısı (default: 0)
- `limit` (int): Maksimum kayıt sayısı (default: 100)
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** Execution dictionary'lerinin listesi (en yeni ilk)
- **Boş:** []
- **Hata:** OrchestrationError

**Örnek Dönüş:**
```json
[
    {
        "id": "EX-A1B2C3D4E5F6G7H8I",
        "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
        "status": "COMPLETED",
        "pending_nodes": 0,
        "executed_nodes": 3,
        "results": {
            "total_processed": 1500,
            "execution_summary": "All nodes completed successfully"
        },
        "started_at": "2024-01-01T10:00:00",
        "ended_at": "2024-01-01T10:05:30",
        "created_at": "2024-01-01T10:00:00",
        "updated_at": "2024-01-01T10:05:30"
    },
    {
        "id": "EX-B2C3D4E5F6G7H8I9J",
        "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
        "status": "FAILED",
        "pending_nodes": 1,
        "executed_nodes": 2,
        "results": {
            "error": "Script execution failed",
            "failed_node": "ND-C3D4E5F6G7H8I9J0K"
        },
        "started_at": "2024-01-01T09:00:00",
        "ended_at": "2024-01-01T09:02:15",
        "created_at": "2024-01-01T09:00:00",
        "updated_at": "2024-01-01T09:02:15"
    }
]
```

### get_by_status()
```python
@with_session
def get_by_status(
    self, 
    session: Session, 
    status: str, 
    skip: int = 0, 
    limit: int = 100, 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> List[Dict[str, Any]]
```

**Amaç:** Belirli statüdeki execution'ları getir

**Parametreler:**
- `status` (str): Execution status'u
- `skip` (int): Atlanacak kayıt sayısı
- `limit` (int): Maksimum kayıt sayısı
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** Filtrelenmiş execution dictionary'lerinin listesi
- **Boş:** []
- **Hata:** OrchestrationError

**Örnek Kullanım:**
```python
# Çalışan execution'ları getir
running_executions = orchestrator.get_by_status("RUNNING")

# Bekleyen execution'ları getir
pending_executions = orchestrator.get_by_status("PENDING", limit=50)

# Başarısız execution'ları getir
failed_executions = orchestrator.get_by_status("FAILED")
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

**Örnek Kullanım:**
```python
# Execution detaylarını getir
execution = orchestrator.get_by_id("EX-A1B2C3D4E5F6G7H8I")

# İlişkilerle birlikte getir (workflow, inputs, outputs)
execution_with_rels = orchestrator.get_by_id(
    "EX-A1B2C3D4E5F6G7H8I", 
    include_relationships=True
)
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

**Kullanım:** Toplam execution sayısını getir

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
# Son 24 saatteki execution'ları getir
from datetime import datetime, timedelta
yesterday = datetime.now() - timedelta(days=1)
recent_executions = orchestrator.filter({
    "started_at": f">={yesterday.isoformat()}"
})

# Belirli workflow ve status kombinasyonu
workflow_failed = orchestrator.filter({
    "workflow_id": "WF-A1B2C3D4E5F6G7H8I",
    "status": "FAILED"
})

# Uzun süren execution'lar (5 dakikadan fazla)
# Bu durum için özel CRUD metodu gerekebilir
```

### count_with_filter()
```python
def count_with_filter(filters: Dict[str, Any]) -> int
```

## Execution Status Değerleri

```python
class ExecutionStatus(str, enum.Enum):
    PENDING = "PENDING"       # Bekliyor
    RUNNING = "RUNNING"       # Çalışıyor
    COMPLETED = "COMPLETED"   # Tamamlandı
    FAILED = "FAILED"         # Başarısız
    CANCELLED = "CANCELLED"   # İptal edildi
```

## Execution İlişkileri

Execution modeli şu ilişkilere sahiptir:
- `workflow` (Workflow): Bağlı olduğu workflow
- `execution_inputs` (List[ExecutionInput]): Execution input'ları
- `execution_outputs` (List[ExecutionOutput]): Execution output'ları

**İlişkilerle Örnek Dönüş (include_relationships=True):**
```json
{
    "id": "EX-A1B2C3D4E5F6G7H8I",
    "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
    "status": "COMPLETED",
    "pending_nodes": 0,
    "executed_nodes": 3,
    "results": {"total_processed": 1500, "execution_time": 330.5},
    "started_at": "2024-01-01T10:00:00",
    "ended_at": "2024-01-01T10:05:30",
    "created_at": "2024-01-01T10:00:00",
    "updated_at": "2024-01-01T10:05:30",
    "workflow": {
        "id": "WF-B2C3D4E5F6G7H8I9J",
        "name": "Data Processing Workflow",
        "description": "Processes daily data files",
        "status": "ACTIVE",
        "priority": 1
    },
    "execution_inputs": [
        {
            "id": "EI-C3D4E5F6G7H8I9J0K",
            "execution_id": "EX-A1B2C3D4E5F6G7H8I",
            "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
            "node_id": "ND-D4E5F6G7H8I9J0K1L",
            "node_name": "Data Loader",
            "script_path": "/scripts/data_loader.py",
            "priority": 1,
            "dependency_count": 0,
            "wait_factor": 0,
            "node_params": {"input_path": "/data/input.csv"}
        },
        {
            "id": "EI-F6G7H8I9J0K1L2M3N",
            "execution_id": "EX-A1B2C3D4E5F6G7H8I",
            "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
            "node_id": "ND-G7H8I9J0K1L2M3N4O",
            "node_name": "Data Processor",
            "script_path": "/scripts/data_processor.py",
            "priority": 2,
            "dependency_count": 1,
            "wait_factor": 0,
            "node_params": {"batch_size": 1000}
        }
    ],
    "execution_outputs": [
        {
            "id": "EO-E5F6G7H8I9J0K1L2M",
            "execution_id": "EX-A1B2C3D4E5F6G7H8I",
            "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
            "node_id": "ND-D4E5F6G7H8I9J0K1L",
            "status": "SUCCESS",
            "result_data": {
                "rows_processed": 1500,
                "execution_time": 120.5,
                "output_file": "/data/output/processed_data.csv"
            },
            "started_at": "2024-01-01T10:00:00",
            "ended_at": "2024-01-01T10:02:00"
        },
        {
            "id": "EO-H8I9J0K1L2M3N4O5P",
            "execution_id": "EX-A1B2C3D4E5F6G7H8I",
            "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
            "node_id": "ND-G7H8I9J0K1L2M3N4O",
            "status": "SUCCESS",
            "result_data": {
                "processed_batches": 15,
                "execution_time": 210.0,
                "memory_usage": "512MB"
            },
            "started_at": "2024-01-01T10:02:00",
            "ended_at": "2024-01-01T10:05:30"
        }
    ]
}
```

## Execution Results Alanı

`results` alanı execution'ın genel sonuçlarını JSON formatında tutar:

### Başarılı Execution
```json
{
    "results": {
        "total_processed": 1500,
        "execution_time": 330.5,
        "nodes_executed": 3,
        "execution_summary": "All nodes completed successfully",
        "performance_metrics": {
            "avg_node_time": 110.17,
            "total_data_processed": "1.5GB"
        }
    }
}
```

### Başarısız Execution
```json
{
    "results": {
        "error": "Script execution failed",
        "error_code": "SCRIPT_ERROR",
        "failed_node": "ND-C3D4E5F6G7H8I9J0K",
        "failed_at": "2024-01-01T09:02:15",
        "executed_nodes": 2,
        "pending_nodes": 1,
        "error_details": {
            "exception": "FileNotFoundError",
            "message": "Input file not found: /data/input.csv"
        }
    }
}
```

## Monitoring ve Analytics

### Execution Durumu İzleme
```python
# Aktif execution'ları izle
active_executions = []
active_executions.extend(orchestrator.get_by_status("RUNNING"))
active_executions.extend(orchestrator.get_by_status("PENDING"))

# Başarısız execution'ları analiz et
failed_executions = orchestrator.get_by_status("FAILED", limit=100)
failure_reasons = {}
for execution in failed_executions:
    error = execution.get("results", {}).get("error", "Unknown")
    failure_reasons[error] = failure_reasons.get(error, 0) + 1
```

### Workflow Performance Analizi
```python
# Belirli workflow'un performansını analiz et
workflow_executions = orchestrator.get_by_workflow("WF-A1B2C3D4E5F6G7H8I")

success_count = len([e for e in workflow_executions if e["status"] == "COMPLETED"])
total_count = len(workflow_executions)
success_rate = success_count / total_count if total_count > 0 else 0

# Ortalama execution süresi
completed_executions = [e for e in workflow_executions if e["status"] == "COMPLETED"]
avg_duration = 0
if completed_executions:
    durations = []
    for execution in completed_executions:
        if execution["started_at"] and execution["ended_at"]:
            start = datetime.fromisoformat(execution["started_at"])
            end = datetime.fromisoformat(execution["ended_at"])
            durations.append((end - start).total_seconds())
    avg_duration = sum(durations) / len(durations) if durations else 0
```

## Önemli Notlar

### READ-ONLY Özellik
ExecutionOrchestrator sadece okuma operasyonları sağlar:
- ❌ **create()** - Execution'lar engine tarafından oluşturulur
- ❌ **update()** - Execution'lar engine tarafından güncellenir  
- ❌ **delete()** - Execution'lar workflow silinirken cascade olarak silinir
- ✅ **get/filter/count** - Tüm okuma operasyonları mevcut

### Execution Lifecycle
1. **PENDING**: Execution oluşturuldu, başlatılmayı bekliyor
2. **RUNNING**: Execution aktif olarak çalışıyor
3. **COMPLETED**: Tüm node'lar başarıyla tamamlandı
4. **FAILED**: En az bir node başarısız oldu
5. **CANCELLED**: Execution kullanıcı tarafından iptal edildi

### Performance Considerations
- Büyük execution listelerinde pagination kullanın
- `include_relationships=True` kullanırken dikkatli olun (büyük data)
- Sık sorgulanan filtreler için index'lerin mevcut olduğundan emin olun
