# ExecutionInputOrchestrator API Documentation

ExecutionInputOrchestrator, execution input monitoring ve READ-ONLY operasyonlarını yürütür.

## Genel Bilgiler

- **Sınıf:** `ExecutionInputOrchestrator`
- **Parent:** `BaseOrchestrator`
- **Modül:** `miniflow.database.orchestration.execution_input_orchestrator`
- **Primary Model:** `ExecutionInput`
- **Primary CRUD:** `execution_input_crud`
- **Özellik:** READ-ONLY (sadece okuma operasyonları)

## ExecutionInput-Specific Metodlar

### get_by_priority()
```python
@with_session
def get_by_priority(
    self, 
    session: Session, 
    priority: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[Dict[str, Any]]
```

**Not:** Bu metod `include_relationships` parametresine sahip değildir. Temel serialization kullanır.

**Amaç:** Belirli öncelik değerine sahip execution input'ları getir

**Parametreler:**
- `priority` (int): Öncelik değeri
- `skip` (int): Atlanacak kayıt sayısı (default: 0)
- `limit` (int): Maksimum kayıt sayısı (default: 100)

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** ExecutionInput dictionary'lerinin listesi
- **Boş:** []
- **Hata:** OrchestrationError

**Örnek Dönüş (Temel):**
```json
[
    {
        "id": "EI-A1B2C3D4E5F6G7H8I",
        "execution_id": "EX-B2C3D4E5F6G7H8I9J",
        "workflow_id": "WF-C3D4E5F6G7H8I9J0K",
        "node_id": "ND-D4E5F6G7H8I9J0K1L",
        "priority": 5,
        "dependency_count": 2,
        "wait_factor": 0,
        "node_name": "High Priority Processor",
        "script_path": "/scripts/priority_processor.py",
        "node_params": {
            "batch_size": 1000,
            "urgent": true
        },
        "created_at": "2024-01-01T10:00:00",
        "updated_at": "2024-01-01T10:00:00"
    }
]
```

**Örnek Dönüş (include_relationships=True):**
```json
[
    {
        "id": "EI-A1B2C3D4E5F6G7H8I",
        "execution_id": "EX-B2C3D4E5F6G7H8I9J",
        "workflow_id": "WF-C3D4E5F6G7H8I9J0K",
        "node_id": "ND-D4E5F6G7H8I9J0K1L",
        "priority": 5,
        "dependency_count": 2,
        "wait_factor": 0,
        "node_name": "High Priority Processor",
        "script_path": "/scripts/priority_processor.py",
        "node_params": {
            "batch_size": 1000,
            "urgent": true
        },
        "created_at": "2024-01-01T10:00:00",
        "updated_at": "2024-01-01T10:00:00",
        "execution": {
            "id": "EX-B2C3D4E5F6G7H8I9J",
            "workflow_id": "WF-C3D4E5F6G7H8I9J0K",
            "status": "RUNNING",
            "pending_nodes": 3,
            "executed_nodes": 1,
            "started_at": "2024-01-01T10:00:00"
        },
        "workflow": {
            "id": "WF-C3D4E5F6G7H8I9J0K",
            "name": "Priority Processing Workflow",
            "description": "Handles high priority data processing",
            "status": "ACTIVE",
            "priority": 5
        },
        "node": {
            "id": "ND-D4E5F6G7H8I9J0K1L",
            "workflow_id": "WF-C3D4E5F6G7H8I9J0K",
            "script_id": "SC-E5F6G7H8I9J0K1L2M",
            "name": "High Priority Processor",
            "description": "Processes urgent data requests",
            "params": {"batch_size": 1000, "urgent": true},
            "max_retries": 5,
            "timeout_seconds": 180
        }
    }
]
```

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

**Amaç:** Belirli bir execution'ın input'larını getir

**Parametreler:**
- `execution_id` (str): Execution ID'si
- `skip` (int): Atlanacak kayıt sayısı
- `limit` (int): Maksimum kayıt sayısı

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** ExecutionInput dictionary'lerinin listesi
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

**Amaç:** Belirli bir node'un execution input'larını getir

**Parametreler:**
- `node_id` (str): Node ID'si
- `skip` (int): Atlanacak kayıt sayısı
- `limit` (int): Maksimum kayıt sayısı

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** ExecutionInput dictionary'lerinin listesi
- **Boş:** []
- **Hata:** OrchestrationError

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

**Amaç:** Belirli bir workflow'un execution input'larını getir

**Parametreler:**
- `workflow_id` (str): Workflow ID'si
- `skip` (int): Atlanacak kayıt sayısı
- `limit` (int): Maksimum kayıt sayısı

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** ExecutionInput dictionary'lerinin listesi
- **Boş:** []
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
# Yüksek dependency count'u olan input'lar
high_dependency = orchestrator.filter({"dependency_count": 3})

# Belirli execution ve priority kombinasyonu
priority_inputs = orchestrator.filter({
    "execution_id": "EX-A1B2C3D4E5F6G7H8I",
    "priority": 5
})

# Bekleyen input'lar (wait_factor > 0)
waiting_inputs = orchestrator.filter({"wait_factor": 1})
```

### count_with_filter()
```python
def count_with_filter(filters: Dict[str, Any]) -> int
```

## ExecutionInput Alanları

### Temel Alanlar
- `id`: ExecutionInput ID'si (EI-...)
- `execution_id`: Bağlı execution ID'si
- `workflow_id`: Bağlı workflow ID'si
- `node_id`: Bağlı node ID'si

### Scheduler Optimizasyon Alanları
- `priority`: Öncelik değeri (yüksek değer = yüksek öncelik)
- `dependency_count`: Bu node'un kaç dependency'si var
- `wait_factor`: Bekle faktörü (scheduler tarafından kullanılır)

### Denormalized Performance Alanları
Performans için denormalized edilmiş alanlar:
- `node_name`: Node adı (hızlı erişim için)
- `script_path`: Script dosya yolu
- `node_params`: Node parametreleri (JSON)

### İlişkiler
ExecutionInput modeli şu ilişkilere sahiptir:
- `execution` (Execution): Bağlı execution
- `workflow` (Workflow): Bağlı workflow
- `node` (Node): Bağlı node

## Scheduler Integration

ExecutionInput'lar scheduler tarafından öncelik sırasına göre işlenir:

### Priority-Based Scheduling
```python
# En yüksek öncelikli input'ları getir
high_priority = orchestrator.get_by_priority(5, limit=10)

# Öncelik sırasına göre sırala
all_pending = orchestrator.filter({}, order_by_field="priority DESC")
```

### Dependency Management
```python
# Dependency olmayan input'ları getir (hemen çalıştırılabilir)
ready_to_run = orchestrator.filter({"dependency_count": 0})

# Bekleyen input'ları getir
waiting_for_deps = orchestrator.filter({"dependency_count": 1})  # veya daha fazla
```

### Wait Factor Usage
```python
# Beklemede olan input'ları getir
waiting_inputs = orchestrator.filter({"wait_factor": 1})

# Hemen çalıştırılabilir input'ları getir
immediate_inputs = orchestrator.filter({"wait_factor": 0})
```

## Monitoring ve Analytics

### Execution Input Analytics
```python
# Execution'ın input dağılımını analiz et
execution_inputs = orchestrator.get_by_execution("EX-A1B2C3D4E5F6G7H8I")

priority_distribution = {}
for inp in execution_inputs:
    priority = inp["priority"]
    priority_distribution[priority] = priority_distribution.get(priority, 0) + 1

# Dependency analizi
dependency_analysis = {}
for inp in execution_inputs:
    dep_count = inp["dependency_count"]
    dependency_analysis[dep_count] = dependency_analysis.get(dep_count, 0) + 1
```

### Workflow Input Monitoring
```python
# Workflow'un tüm input'larını izle
workflow_inputs = orchestrator.get_by_workflow("WF-A1B2C3D4E5F6G7H8I")

# Node bazında input sayısı
node_input_counts = {}
for inp in workflow_inputs:
    node_name = inp["node_name"]
    node_input_counts[node_name] = node_input_counts.get(node_name, 0) + 1
```

### Performance Analysis
```python
# Yüksek dependency count'u olan node'ları bul
high_dependency_nodes = orchestrator.filter({"dependency_count": 3})

# Node performance ranking (dependency ve priority bazında)
performance_metrics = {}
for inp in high_dependency_nodes:
    node_name = inp["node_name"]
    if node_name not in performance_metrics:
        performance_metrics[node_name] = {
            "avg_priority": 0,
            "avg_dependency": 0,
            "count": 0
        }
    
    metrics = performance_metrics[node_name]
    metrics["avg_priority"] = (metrics["avg_priority"] * metrics["count"] + inp["priority"]) / (metrics["count"] + 1)
    metrics["avg_dependency"] = (metrics["avg_dependency"] * metrics["count"] + inp["dependency_count"]) / (metrics["count"] + 1)
    metrics["count"] += 1
```

## Önemli Notlar

### READ-ONLY Özellik
ExecutionInputOrchestrator sadece okuma operasyonları sağlar:
- ❌ **create()** - Input'lar engine tarafından oluşturulur
- ❌ **update()** - Input'lar engine tarafından güncellenir
- ❌ **delete()** - Input'lar execution silinirken cascade olarak silinir
- ✅ **get/filter/count** - Tüm okuma operasyonları mevcut

### Denormalization Faydaları
Performans için denormalized alanlar:
- `node_name`: Node tablosuna join yapmadan node adını alabilirsiniz
- `script_path`: Script path'ini hızlıca alabilirsiniz
- `node_params`: Node parametrelerini direkt kullanabilirsiniz

### Scheduler Kullanımı
ExecutionInput'lar execution scheduler tarafından kullanılır:
1. **Priority**: Yüksek öncelikli işler önce çalıştırılır
2. **Dependency Count**: Dependency'si olmayan işler hemen başlatılır
3. **Wait Factor**: Engine tarafından dinamik olarak ayarlanır

### Performance Considerations
- Büyük execution'larda input sayısı çok olabilir, pagination kullanın
- Scheduler sorguları için uygun indexlerin mevcut olduğundan emin olun
- `priority` ve `dependency_count` alanları sık sorgulanır
