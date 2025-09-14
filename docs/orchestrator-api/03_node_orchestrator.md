# NodeOrchestrator API Documentation

NodeOrchestrator, node yönetimi ve CRUD operasyonlarını yürütür.

## Genel Bilgiler

- **Sınıf:** `NodeOrchestrator`
- **Parent:** `BaseOrchestrator`
- **Modül:** `miniflow.database.orchestration.node_orchestrator`
- **Primary Model:** `Node`
- **Primary CRUD:** `node_crud`

## Node-Specific Metodlar

### create()
```python
@with_session
def create(self, session: Session, workflow_id: str, name: str, **kwargs) -> Dict[str, Any]
```

**Amaç:** Yeni node oluştur

**Parametreler:**
- `workflow_id` (str): Bağlı olduğu workflow ID'si (zorunlu)
- `name` (str): Node adı (zorunlu)
- `**kwargs`: Diğer node alanları
  - `script_id` (str): Bağlı script ID'si
  - `description` (str): Açıklama
  - `params` (dict): Node parametreleri
  - `meta_data` (dict): Metadata
  - `max_retries` (int): Maksimum retry sayısı (default: 3)
  - `timeout_seconds` (int): Timeout süresi (default: 300)

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Oluşturulan node'un dictionary'si
- **Hata:** OrchestrationError

**Örnek Dönüş (Temel):**
```json
{
    "id": "ND-A1B2C3D4E5F6G7H8I",
    "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
    "script_id": "SC-C3D4E5F6G7H8I9J0K",
    "name": "Data Processor",
    "description": "Processes incoming data",
    "params": {"input_path": "/data/input"},
    "meta_data": {"category": "processing"},
    "max_retries": 3,
    "timeout_seconds": 300,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
}
```

**Örnek Dönüş (include_relationships=True):**
```json
{
    "id": "ND-A1B2C3D4E5F6G7H8I",
    "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
    "script_id": "SC-C3D4E5F6G7H8I9J0K",
    "name": "Data Processor",
    "description": "Processes incoming data",
    "params": {"input_path": "/data/input"},
    "meta_data": {"category": "processing"},
    "max_retries": 3,
    "timeout_seconds": 300,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00",
    "workflow": {
        "id": "WF-B2C3D4E5F6G7H8I9J",
        "name": "Data Processing Workflow",
        "status": "ACTIVE",
        "priority": 1
    },
    "script": {
        "id": "SC-C3D4E5F6G7H8I9J0K",
        "name": "csv_processor",
        "category": "data_processing",
        "file_extension": ".py",
        "test_status": "PASSED"
    },
    "outgoing_edges": [
        {
            "id": "ED-D4E5F6G7H8I9J0K1L",
            "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
            "from_node_id": "ND-A1B2C3D4E5F6G7H8I",
            "to_node_id": "ND-E5F6G7H8I9J0K1L2M",
            "condition_type": "SUCCESS"
        }
    ],
    "incoming_edges": [
        {
            "id": "ED-F6G7H8I9J0K1L2M3N",
            "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
            "from_node_id": "ND-G7H8I9J0K1L2M3N4O",
            "to_node_id": "ND-A1B2C3D4E5F6G7H8I",
            "condition_type": "SUCCESS"
        }
    ],
    "execution_inputs": [
        {
            "id": "EI-H8I9J0K1L2M3N4O5P",
            "execution_id": "EX-I9J0K1L2M3N4O5P6Q",
            "node_name": "Data Processor",
            "priority": 2,
            "dependency_count": 1
        }
    ],
    "execution_outputs": [
        {
            "id": "EO-J0K1L2M3N4O5P6Q7R",
            "execution_id": "EX-I9J0K1L2M3N4O5P6Q",
            "status": "SUCCESS",
            "result_data": {"processed_rows": 1500}
        }
    ]
}
```

### update()
```python
@with_session
def update(self, session: Session, record_id: str, **kwargs) -> Dict[str, Any]
```

**Amaç:** Node'u güncelle

**Parametreler:**
- `record_id` (str): Node ID'si
- `**kwargs`: Güncellenecek alanlar

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Güncellenen node'un dictionary'si
- **Bulunamadı:** DatabaseQueryError (Node not found)
- **Hata:** OrchestrationError

### delete()
```python
@with_session
def delete(self, session: Session, record_id: str) -> Dict[str, Any]
```

**Amaç:** Node'u sil

**Silme Etkisi:**
- Node'a bağlı tüm edge'ler otomatik silinir (foreign key cascade)
- Node'a bağlı execution inputs/outputs silinir

**Parametreler:**
- `record_id` (str): Node ID'si

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Silinen node'un dictionary'si
- **Bulunamadı:** DatabaseQueryError
- **Hata:** OrchestrationError

### get_by_name_and_workflow()
```python
@with_session
def get_by_name_and_workflow(
    self, 
    session: Session, 
    name: str, 
    workflow_id: str, 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> Optional[Dict[str, Any]]
```

**Amaç:** Belirli bir workflow içinde node'u adına göre getir

**Parametreler:**
- `name` (str): Node adı
- `workflow_id` (str): Workflow ID'si
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `Optional[Dict[str, Any]]`
- **Başarılı:** Node dictionary'si
- **Bulunamadı:** None
- **Hata:** OrchestrationError

**Örnek Dönüş (Temel):**
```json
{
    "id": "ND-A1B2C3D4E5F6G7H8I",
    "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
    "script_id": "SC-C3D4E5F6G7H8I9J0K",
    "name": "Data Processor",
    "description": "Processes incoming data",
    "params": {"input_path": "/data/input"},
    "meta_data": {"category": "processing"},
    "max_retries": 3,
    "timeout_seconds": 300,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
}
```

**Örnek Dönüş (include_relationships=True):**
```json
{
    "id": "ND-A1B2C3D4E5F6G7H8I",
    "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
    "script_id": "SC-C3D4E5F6G7H8I9J0K",
    "name": "Data Processor",
    "description": "Processes incoming data",
    "params": {"input_path": "/data/input"},
    "meta_data": {"category": "processing"},
    "max_retries": 3,
    "timeout_seconds": 300,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00",
    "workflow": {
        "id": "WF-B2C3D4E5F6G7H8I9J",
        "name": "Data Processing Workflow",
        "status": "ACTIVE",
        "priority": 1
    },
    "script": {
        "id": "SC-C3D4E5F6G7H8I9J0K",
        "name": "csv_processor",
        "category": "data_processing",
        "file_extension": ".py",
        "test_status": "PASSED"
    },
    "outgoing_edges": [
        {
            "id": "ED-D4E5F6G7H8I9J0K1L",
            "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
            "from_node_id": "ND-A1B2C3D4E5F6G7H8I",
            "to_node_id": "ND-E5F6G7H8I9J0K1L2M",
            "condition_type": "SUCCESS"
        }
    ],
    "incoming_edges": [],
    "execution_inputs": [],
    "execution_outputs": []
}
```

### get_by_workflow()
```python
@with_session
def get_by_workflow(
    self, 
    session: Session, 
    workflow_id: str, 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> List[Dict[str, Any]]
```

**Amaç:** Belirli bir workflow'un tüm node'larını getir

**Parametreler:**
- `workflow_id` (str): Workflow ID'si
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** Node dictionary'lerinin listesi
- **Boş Workflow:** []
- **Hata:** OrchestrationError

**Örnek Dönüş (Temel):**
```json
[
    {
        "id": "ND-A1B2C3D4E5F6G7H8I",
        "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
        "script_id": "SC-C3D4E5F6G7H8I9J0K",
        "name": "Data Loader",
        "description": "Loads data from CSV",
        "params": {"input_path": "/data/input.csv"},
        "max_retries": 3,
        "timeout_seconds": 300
    },
    {
        "id": "ND-B2C3D4E5F6G7H8I9J",
        "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
        "script_id": "SC-D4E5F6G7H8I9J0K1L",
        "name": "Data Processor",
        "description": "Processes loaded data",
        "params": {"batch_size": 1000},
        "max_retries": 3,
        "timeout_seconds": 600
    }
]
```

**Örnek Kullanım:**
```python
# Workflow'un tüm node'larını getir
nodes = node_orchestrator.get_by_workflow("WF-A1B2C3D4E5F6G7H8I")

# İlişkilerle birlikte getir
nodes_with_rels = node_orchestrator.get_by_workflow(
    "WF-A1B2C3D4E5F6G7H8I", 
    include_relationships=True
)
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
# Belirli script'e bağlı node'ları getir
nodes = orchestrator.filter({"script_id": "SC-A1B2C3D4E5F6G7H8I"})

# Belirli workflow'daki node'ları getir
workflow_nodes = orchestrator.filter({"workflow_id": "WF-B2C3D4E5F6G7H8I9J"})

# Timeout süresi yüksek node'ları getir
long_timeout_nodes = orchestrator.filter({"timeout_seconds": 600})
```

### count_with_filter()
```python
def count_with_filter(filters: Dict[str, Any]) -> int
```

## Node İlişkileri

Node modeli şu ilişkilere sahiptir:
- `workflow` (Workflow): Bağlı olduğu workflow
- `script` (Script): Bağlı olduğu script (optional)
- `outgoing_edges` (List[Edge]): Bu node'dan çıkan edge'ler
- `incoming_edges` (List[Edge]): Bu node'a gelen edge'ler
- `execution_inputs` (List[ExecutionInput]): Node'un execution input'ları
- `execution_outputs` (List[ExecutionOutput]): Node'un execution output'ları

Bu ilişkiler `include_relationships=True` ile dahil edilebilir.

## Node Parametreleri

### params Alanı
Node'un çalışma parametrelerini içeren JSON alanı:
```json
{
    "input_path": "/data/input",
    "output_path": "/data/output",
    "batch_size": 100,
    "retry_on_failure": true
}
```

### meta_data Alanı
Node hakkında metadata içeren JSON alanı:
```json
{
    "category": "data_processing",
    "tags": ["etl", "batch"],
    "documentation": "https://docs.example.com/node1"
}
```

## Hata Durumları

### Node Oluşturma Hataları
```python
# Workflow bulunamazsa
ValidationError("Workflow not found")

# Aynı isimde node varsa (workflow içinde)
ValidationError("Node name already exists in workflow")

# Geçersiz script ID
ValidationError("Script not found")
```

### Node Silme Hataları
```python
# Node bulunamazsa
DatabaseQueryError("Node 'ND-...' not found")

# Foreign key constraint ihlali
DatabaseQueryError("Cannot delete node - foreign key constraint")
```
