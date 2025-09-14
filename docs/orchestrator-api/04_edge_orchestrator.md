# EdgeOrchestrator API Documentation

EdgeOrchestrator, edge (bağlantı) yönetimi ve CRUD operasyonlarını yürütür.

## Genel Bilgiler

- **Sınıf:** `EdgeOrchestrator`
- **Parent:** `BaseOrchestrator`
- **Modül:** `miniflow.database.orchestration.edge_orchestrator`
- **Primary Model:** `Edge`
- **Primary CRUD:** `edge_crud`

## Edge-Specific Metodlar

### create()
```python
@with_session
def create(
    self, 
    session: Session, 
    workflow_id: str, 
    from_node_id: str, 
    to_node_id: str, 
    **kwargs
) -> Dict[str, Any]
```

**Amaç:** Yeni edge oluştur

**Özel Özellik:** Aynı node'lar arasında edge varsa, yeni oluşturmak yerine mevcut olanı döndürür.

**Parametreler:**
- `workflow_id` (str): Bağlı olduğu workflow ID'si (zorunlu)
- `from_node_id` (str): Kaynak node ID'si (zorunlu)
- `to_node_id` (str): Hedef node ID'si (zorunlu)
- `**kwargs`: Diğer edge alanları
  - `condition_type` (ConditionType): Koşul tipi (default: SUCCESS)

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Oluşturulan/mevcut edge'in dictionary'si
- **Hata:** OrchestrationError

**Örnek Dönüş (Temel):**
```json
{
    "id": "ED-A1B2C3D4E5F6G7H8I",
    "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
    "from_node_id": "ND-C3D4E5F6G7H8I9J0K",
    "to_node_id": "ND-D4E5F6G7H8I9J0K1L",
    "condition_type": "SUCCESS",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
}
```

**Örnek Dönüş (include_relationships=True):**
```json
{
    "id": "ED-A1B2C3D4E5F6G7H8I",
    "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
    "from_node_id": "ND-C3D4E5F6G7H8I9J0K",
    "to_node_id": "ND-D4E5F6G7H8I9J0K1L",
    "condition_type": "SUCCESS",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00",
    "workflow": {
        "id": "WF-B2C3D4E5F6G7H8I9J",
        "name": "Data Processing Workflow",
        "status": "ACTIVE",
        "priority": 1,
        "description": "Processes daily data"
    },
    "from_node": {
        "id": "ND-C3D4E5F6G7H8I9J0K",
        "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
        "script_id": "SC-E5F6G7H8I9J0K1L2M",
        "name": "Data Loader",
        "description": "Loads data from CSV",
        "params": {"input_path": "/data/input.csv"},
        "max_retries": 3,
        "timeout_seconds": 300
    },
    "to_node": {
        "id": "ND-D4E5F6G7H8I9J0K1L",
        "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
        "script_id": "SC-F6G7H8I9J0K1L2M3N",
        "name": "Data Processor",
        "description": "Processes loaded data",
        "params": {"batch_size": 1000},
        "max_retries": 3,
        "timeout_seconds": 600
    }
}
```

### update()
```python
@with_session
def update(self, session: Session, record_id: str, **kwargs) -> Dict[str, Any]
```

**Amaç:** Edge'i güncelle

**Parametreler:**
- `record_id` (str): Edge ID'si
- `**kwargs`: Güncellenecek alanlar

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Güncellenen edge'in dictionary'si
- **Bulunamadı:** DatabaseQueryError (Edge not found)
- **Hata:** OrchestrationError

### delete()
```python
@with_session
def delete(self, session: Session, record_id: str) -> Dict[str, Any]
```

**Amaç:** Edge'i sil

**Parametreler:**
- `record_id` (str): Edge ID'si

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Silinen edge'in dictionary'si
- **Bulunamadı:** DatabaseQueryError
- **Hata:** OrchestrationError

### get_edges_by_workflow()
```python
@with_session
def get_edges_by_workflow(
    self, 
    session: Session, 
    workflow_id: str, 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> List[Dict[str, Any]]
```

**Amaç:** Belirli bir workflow'un tüm edge'lerini getir

**Parametreler:**
- `workflow_id` (str): Workflow ID'si
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** Edge dictionary'lerinin listesi
- **Boş Workflow:** []
- **Hata:** OrchestrationError

**Örnek Dönüş (Temel):**
```json
[
    {
        "id": "ED-A1B2C3D4E5F6G7H8I",
        "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
        "from_node_id": "ND-C3D4E5F6G7H8I9J0K",
        "to_node_id": "ND-D4E5F6G7H8I9J0K1L",
        "condition_type": "SUCCESS",
        "created_at": "2024-01-01T12:00:00",
        "updated_at": "2024-01-01T12:00:00"
    },
    {
        "id": "ED-B2C3D4E5F6G7H8I9J",
        "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
        "from_node_id": "ND-D4E5F6G7H8I9J0K1L",
        "to_node_id": "ND-E5F6G7H8I9J0K1L2M",
        "condition_type": "SUCCESS",
        "created_at": "2024-01-01T12:00:00",
        "updated_at": "2024-01-01T12:00:00"
    }
]
```

### get_edges_by_node()
```python
@with_session
def get_edges_by_node(
    self, 
    session: Session, 
    node_id: str, 
    direction: str = 'both', 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> List[Dict[str, Any]]
```

**Amaç:** Belirli bir node'a bağlı edge'leri getir

**Parametreler:**
- `node_id` (str): Node ID'si
- `direction` (str): Edge yönü
  - `"outgoing"`: Sadece çıkan edge'ler
  - `"incoming"`: Sadece gelen edge'ler
  - `"both"`: Hem gelen hem çıkan (default)
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** Edge dictionary'lerinin listesi
- **Edge Yok:** []
- **Hata:** OrchestrationError

**Örnek Kullanım:**
```python
# Node'un tüm edge'lerini getir
all_edges = edge_orchestrator.get_edges_by_node("ND-A1B2C3D4E5F6G7H8I")

# Sadece çıkan edge'leri getir
outgoing = edge_orchestrator.get_edges_by_node(
    "ND-A1B2C3D4E5F6G7H8I", 
    direction="outgoing"
)

# Sadece gelen edge'leri getir
incoming = edge_orchestrator.get_edges_by_node(
    "ND-A1B2C3D4E5F6G7H8I", 
    direction="incoming"
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
# Belirli workflow'daki edge'leri getir
workflow_edges = orchestrator.filter({"workflow_id": "WF-A1B2C3D4E5F6G7H8I"})

# Belirli kaynak node'dan çıkan edge'leri getir
from_node_edges = orchestrator.filter({"from_node_id": "ND-B2C3D4E5F6G7H8I9J"})

# Belirli hedef node'a gelen edge'leri getir
to_node_edges = orchestrator.filter({"to_node_id": "ND-C3D4E5F6G7H8I9J0K"})

# SUCCESS koşullu edge'leri getir
success_edges = orchestrator.filter({"condition_type": "SUCCESS"})
```

### count_with_filter()
```python
def count_with_filter(filters: Dict[str, Any]) -> int
```

## Condition Types

Edge'lerin koşul tipleri:

```python
class ConditionType(str, enum.Enum):
    SUCCESS = "SUCCESS"        # Başarılı tamamlanma
    FAILURE = "FAILURE"        # Hata durumu
    ALWAYS = "ALWAYS"          # Her zaman çalış
    CONDITIONAL = "CONDITIONAL" # Koşullu çalışma
```

## Edge İlişkileri

Edge modeli şu ilişkilere sahiptir:
- `workflow` (Workflow): Bağlı olduğu workflow
- `from_node` (Node): Kaynak node
- `to_node` (Node): Hedef node

Bu ilişkiler `include_relationships=True` ile dahil edilebilir.

**İlişkilerle Örnek Dönüş:**
```json
{
    "id": "ED-A1B2C3D4E5F6G7H8I",
    "workflow_id": "WF-B2C3D4E5F6G7H8I9J",
    "from_node_id": "ND-C3D4E5F6G7H8I9J0K",
    "to_node_id": "ND-D4E5F6G7H8I9J0K1L",
    "condition_type": "SUCCESS",
    "workflow": {
        "id": "WF-B2C3D4E5F6G7H8I9J",
        "name": "Sample Workflow"
    },
    "from_node": {
        "id": "ND-C3D4E5F6G7H8I9J0K",
        "name": "Source Node"
    },
    "to_node": {
        "id": "ND-D4E5F6G7H8I9J0K1L",
        "name": "Target Node"
    }
}
```

## Hata Durumları

### Edge Oluşturma Hataları
```python
# Workflow bulunamazsa
ValidationError("Workflow not found")

# Kaynak node bulunamazsa
ValidationError("From node not found")

# Hedef node bulunamazsa
ValidationError("To node not found")

# Self-loop (node kendine bağlanamaz)
ValidationError("Self-loops are not allowed")
```

### Edge Silme Hataları
```python
# Edge bulunamazsa
DatabaseQueryError("Edge 'ED-...' not found")
```

## Workflow Graph Analizi

Edge'ler workflow'un graph yapısını oluşturur. Bu metodlarla graph analizi yapılabilir:

```python
# Workflow'un tüm edge'lerini getir
edges = edge_orchestrator.get_edges_by_workflow("WF-A1B2C3D4E5F6G7H8I")

# Root node'ları bul (gelen edge'i olmayan)
all_nodes = node_orchestrator.get_by_workflow("WF-A1B2C3D4E5F6G7H8I")
root_nodes = []
for node in all_nodes:
    incoming = edge_orchestrator.get_edges_by_node(node["id"], direction="incoming")
    if not incoming:
        root_nodes.append(node)

# Leaf node'ları bul (çıkan edge'i olmayan)
leaf_nodes = []
for node in all_nodes:
    outgoing = edge_orchestrator.get_edges_by_node(node["id"], direction="outgoing")
    if not outgoing:
        leaf_nodes.append(node)
```
