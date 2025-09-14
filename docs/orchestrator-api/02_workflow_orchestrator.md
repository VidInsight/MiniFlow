# WorkflowOrchestrator API Documentation

WorkflowOrchestrator, workflow yönetimi ve CRUD operasyonlarını yürütür.

## Genel Bilgiler

- **Sınıf:** `WorkflowOrchestrator`
- **Parent:** `BaseOrchestrator`
- **Modül:** `miniflow.database.orchestration.workflow_orchestrator`
- **Primary Model:** `Workflow`
- **Primary CRUD:** `workflow_crud`

## Workflow-Specific Metodlar

### create()
```python
@with_session
def create(self, session: Session, name: str, **kwargs) -> Dict[str, Any]
```

**Amaç:** Yeni workflow oluştur

**Parametreler:**
- `name` (str): Workflow adı (zorunlu)
- `**kwargs`: Diğer workflow alanları
  - `description` (str): Açıklama
  - `priority` (int): Öncelik (default: 0)
  - `status` (WorkflowStatus): Durum (default: DRAFT)

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Oluşturulan workflow'un dictionary'si
- **Hata:** OrchestrationError

**Örnek Dönüş (Temel):**
```json
{
    "id": "WF-A1B2C3D4E5F6G7H8I",
    "name": "Data Processing Workflow",
    "description": "Processes daily data",
    "priority": 1,
    "status": "DRAFT",
    "status_message": null,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
}
```

**Not:** Bu metod `include_relationships` parametresine sahip değildir. Temel serialization kullanır.

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

**Amaç:** Workflow'u adına göre getir

**Parametreler:**
- `name` (str): Workflow adı
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `Optional[Dict[str, Any]]`
- **Başarılı:** Workflow dictionary'si
- **Bulunamadı:** None
- **Hata:** OrchestrationError

**Örnek Dönüş (Temel):**
```json
{
    "id": "WF-A1B2C3D4E5F6G7H8I",
    "name": "Data Processing Workflow",
    "description": "Processes daily data",
    "priority": 1,
    "status": "ACTIVE",
    "status_message": null,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
}
```

**Örnek Dönüş (include_relationships=True):**
```json
{
    "id": "WF-A1B2C3D4E5F6G7H8I",
    "name": "Data Processing Workflow",
    "description": "Processes daily data",
    "priority": 1,
    "status": "ACTIVE",
    "status_message": null,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00",
    "nodes": [
        {
            "id": "ND-B2C3D4E5F6G7H8I9J",
            "workflow_id": "WF-A1B2C3D4E5F6G7H8I",
            "script_id": "SC-C3D4E5F6G7H8I9J0K",
            "name": "Data Loader",
            "description": "Loads data from CSV",
            "params": {"input_path": "/data/input.csv"},
            "max_retries": 3,
            "timeout_seconds": 300
        },
        {
            "id": "ND-C3D4E5F6G7H8I9J0K",
            "workflow_id": "WF-A1B2C3D4E5F6G7H8I",
            "script_id": "SC-D4E5F6G7H8I9J0K1L",
            "name": "Data Processor",
            "description": "Processes loaded data",
            "params": {"batch_size": 1000},
            "max_retries": 3,
            "timeout_seconds": 600
        }
    ],
    "edges": [
        {
            "id": "ED-D4E5F6G7H8I9J0K1L",
            "workflow_id": "WF-A1B2C3D4E5F6G7H8I",
            "from_node_id": "ND-B2C3D4E5F6G7H8I9J",
            "to_node_id": "ND-C3D4E5F6G7H8I9J0K",
            "condition_type": "SUCCESS"
        }
    ],
    "executions": [
        {
            "id": "EX-E5F6G7H8I9J0K1L2M",
            "workflow_id": "WF-A1B2C3D4E5F6G7H8I",
            "status": "COMPLETED",
            "pending_nodes": 0,
            "executed_nodes": 2,
            "results": {"total_processed": 1500},
            "started_at": "2024-01-01T10:00:00",
            "ended_at": "2024-01-01T10:05:30"
        }
    ]
}
```

### update()
```python
@with_session
def update(self, session: Session, workflow_id: str, **kwargs) -> Dict[str, Any]
```

**Amaç:** Workflow'u güncelle

**Parametreler:**
- `workflow_id` (str): Workflow ID'si
- `**kwargs`: Güncellenecek alanlar

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Güncellenen workflow'un dictionary'si
- **Bulunamadı:** DatabaseQueryError (Workflow not found)
- **Hata:** OrchestrationError

**Örnek Dönüş:**
```json
{
    "id": "WF-A1B2C3D4E5F6G7H8I",
    "name": "Updated Data Processing Workflow",
    "description": "Updated description for daily data processing",
    "priority": 2,
    "status": "ACTIVE",
    "status_message": "Updated successfully",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T14:30:00"
}
```

**Not:** Bu metod `include_relationships` parametresine sahip değildir. Temel serialization kullanır.

### delete()
```python
@with_session
def delete(self, session: Session, workflow_id: str) -> Dict[str, Any]
```

**Amaç:** Workflow'u cascade olarak sil

**Silme Sırası:**
1. Aktif execution kontrolü (RUNNING/PENDING)
2. Tüm execution'lar silinir (inputs/outputs dahil)
3. Tüm node'lar silinir (edge'ler otomatik silinir)
4. Workflow silinir

**Parametreler:**
- `workflow_id` (str): Workflow ID'si

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** `{"deleted": True, "workflow_id": "WF-..."}`
- **Bulunamadı:** DatabaseQueryError
- **Aktif Execution Var:** OrchestrationError
- **Hata:** OrchestrationError

**Örnek Başarılı Dönüş:**
```json
{
    "deleted": true,
    "workflow_id": "WF-A1B2C3D4E5F6G7H8I"
}
```

## Kalıtım Edilen Generic CRUD Metodları

WorkflowOrchestrator, BaseOrchestrator'dan aşağıdaki metodları kalıtım alır:

### get_by_id()
```python
def get_by_id(
    record_id: str, 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> Optional[Dict[str, Any]]
```

**Amaç:** ID'ye göre workflow getir

**Parametreler:**
- `record_id` (str): Workflow ID'si
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `Optional[Dict[str, Any]]`
- **Başarılı:** Workflow dictionary'si (yukarıdaki örneklerdeki gibi)
- **Bulunamadı:** None
- **Hata:** OrchestrationError

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

**Amaç:** Tüm workflow'ları getir (pagination ile)

**Parametreler:**
- `skip` (int): Atlanacak kayıt sayısı (default: 0)
- `limit` (int): Maksimum kayıt sayısı (default: 100)
- `order_by` (str): Sıralama alanı (default: None)
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** Workflow dictionary'lerinin listesi
- **Boş:** []
- **Hata:** OrchestrationError

### count()
```python
def count() -> int
```

**Amaç:** Toplam workflow sayısını getir

**Dönen Değer:** `int`
- **Başarılı:** Workflow sayısı
- **Hata:** OrchestrationError

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

**Amaç:** Filtreleme ile workflow'ları getir

**Parametreler:**
- `filters` (Dict[str, Any]): Filtre kriterleri
- `skip` (int): Atlanacak kayıt sayısı
- `limit` (int): Maksimum kayıt sayısı
- `order_by_field` (str): Sıralama alanı
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** Filtrelenmiş workflow dictionary'lerinin listesi
- **Boş:** []
- **Hata:** OrchestrationError

**Örnek Filtre Kullanımı:**
```python
# Aktif workflow'ları getir
workflows = orchestrator.filter({"status": "ACTIVE"})

# Yüksek öncelikli workflow'ları getir
high_priority = orchestrator.filter({"priority": 5}, limit=10)

# İsme göre arama
search_results = orchestrator.filter({"name": "Processing"})
```

### count_with_filter()
```python
def count_with_filter(filters: Dict[str, Any]) -> int
```

**Amaç:** Filtreleme ile workflow sayısını getir

**Parametreler:**
- `filters` (Dict[str, Any]): Filtre kriterleri

**Dönen Değer:** `int`
- **Başarılı:** Filtrelenmiş workflow sayısı
- **Hata:** OrchestrationError

## Workflow Status Değerleri

```python
class WorkflowStatus(str, enum.Enum):
    DRAFT = "DRAFT"           # Taslak
    ACTIVE = "ACTIVE"         # Aktif
    DEACTIVATED = "DEACTIVATED"  # Deaktif
```

## İlişkili Modeller

Workflow modeli şu ilişkilere sahiptir:
- `nodes` (List[Node]): Workflow'daki node'lar
- `edges` (List[Edge]): Workflow'daki edge'ler  
- `executions` (List[Execution]): Workflow execution'ları

Bu ilişkiler `include_relationships=True` ile dahil edilebilir.

## Hata Durumları

### Workflow Silme Hataları
```python
# Aktif execution varsa
OrchestrationError("Cannot delete workflow 'WF-...' - it has active executions")

# Workflow bulunamazsa
DatabaseQueryError("Workflow 'WF-...' not found")
```

### Validation Hataları
```python
# İsim boşsa veya geçersizse
ValidationError("Invalid workflow name")

# Duplicate name
ValidationError("Workflow name already exists")
```
