# BaseOrchestrator API Documentation

BaseOrchestrator, tüm orchestrator'ların türediği temel sınıftır ve generic CRUD operasyonları sağlar.

## Genel Bilgiler

- **Sınıf:** `BaseOrchestrator`
- **Modül:** `miniflow.database.orchestration.base_orchestrator`
- **Amaç:** Generic CRUD operasyonları ve session yönetimi

## Session Yönetimi

### @with_session Decorator
Tüm orchestrator metodları `@with_session` decorator'ı kullanır:
- Otomatik session oluşturma ve cleanup
- Auto-commit (auto_commit=True)
- Exception durumunda auto-rollback

## Serialization Metodları

### _serialize_single_result()
```python
def _serialize_single_result(
    self, 
    result, 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> Optional[Dict[str, Any]]
```

**Parametreler:**
- `result`: Serialize edilecek model instance
- `include_relationships`: İlişkili objeleri dahil et
- `exclude_fields`: Hariç tutulacak alanlar

**Dönen Değer:** `Optional[Dict[str, Any]]` - Model dictionary'si veya None

### _serialize_multiple_results()
```python
def _serialize_multiple_results(
    self, 
    results, 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> List[Dict[str, Any]]
```

**Parametreler:**
- `results`: Serialize edilecek model instance'ları listesi
- `include_relationships`: İlişkili objeleri dahil et
- `exclude_fields`: Hariç tutulacak alanlar

**Dönen Değer:** `List[Dict[str, Any]]` - Model dictionary'lerinin listesi

## Generic CRUD Operasyonları

### get_by_id()
```python
@with_session
def get_by_id(
    self, 
    session, 
    record_id: str, 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> Optional[Dict[str, Any]]
```

**Amaç:** ID'ye göre tek kayıt getir

**Parametreler:**
- `record_id` (str): Kayıt ID'si
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `Optional[Dict[str, Any]]`
- **Başarılı:** Model dictionary'si
- **Bulunamadı:** None
- **Hata:** OrchestrationError

**Örnek Dönüş:**
```json
{
    "id": "WF-A1B2C3D4E5F6G7H8I",
    "name": "Sample Workflow",
    "description": "A sample workflow",
    "priority": 0,
    "status": "DRAFT",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
}
```

### get_all()
```python
@with_session
def get_all(
    self, 
    session, 
    skip: int = 0, 
    limit: int = 100, 
    order_by: str = None, 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> List[Dict[str, Any]]
```

**Amaç:** Tüm kayıtları getir (pagination ile)

**Parametreler:**
- `skip` (int): Atlanacak kayıt sayısı (default: 0)
- `limit` (int): Maksimum kayıt sayısı (default: 100)
- `order_by` (str): Sıralama alanı (default: None)
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** Model dictionary'lerinin listesi
- **Boş:** []
- **Hata:** OrchestrationError

### count()
```python
@with_session
def count(self, session) -> int
```

**Amaç:** Toplam kayıt sayısını getir

**Dönen Değer:** `int`
- **Başarılı:** Kayıt sayısı
- **Hata:** OrchestrationError

### filter()
```python
@with_session
def filter(
    self, 
    session, 
    filters: Dict[str, Any], 
    skip: int = 0, 
    limit: int = 100, 
    order_by_field: str = None, 
    include_relationships: bool = False, 
    exclude_fields: List[str] = None
) -> List[Dict[str, Any]]
```

**Amaç:** Filtreleme ile kayıtları getir

**Parametreler:**
- `filters` (Dict[str, Any]): Filtre kriterleri
- `skip` (int): Atlanacak kayıt sayısı
- `limit` (int): Maksimum kayıt sayısı
- `order_by_field` (str): Sıralama alanı
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `List[Dict[str, Any]]`
- **Başarılı:** Filtrelenmiş model dictionary'lerinin listesi
- **Boş:** []
- **Hata:** OrchestrationError

**Örnek Filtre:**
```python
filters = {
    "status": "ACTIVE",
    "priority": 1
}
```

### count_with_filter()
```python
@with_session
def count_with_filter(self, session, filters: Dict[str, Any]) -> int
```

**Amaç:** Filtreleme ile kayıt sayısını getir

**Parametreler:**
- `filters` (Dict[str, Any]): Filtre kriterleri

**Dönen Değer:** `int`
- **Başarılı:** Filtrelenmiş kayıt sayısı
- **Hata:** OrchestrationError

## Hata Yönetimi

### _create_error_context()
```python
def _create_error_context(self, operation: str, **kwargs) -> ErrorContext
```

**Amaç:** Hata tracking için error context oluştur

### _handle_not_found()
```python
def _handle_not_found(self, resource_name: str, identifier: str, operation: str)
```

**Amaç:** Standardize edilmiş "bulunamadı" hatası fırlat
- **Fırlatılan Hata:** DatabaseQueryError
- **Severity:** HIGH

## CRUD Instances

BaseOrchestrator tüm CRUD instance'ları tutar:
- `self.envar_crud` - EnvironmentVariableCRUD
- `self.fileupload_crud` - FileUploadCRUD  
- `self.script_crud` - ScriptCRUD
- `self.workflow_crud` - WorkflowCRUD
- `self.node_crud` - NodeCRUD
- `self.edge_crud` - EdgeCRUD
- `self.execution_crud` - ExecutionCRUD
- `self.execution_input_crud` - ExecutionInputCRUD
- `self.execution_output_crud` - ExecutionOutputCRUD

## Kalıtım Gereksinimleri

Child orchestrator'lar şu metodu implement etmeli:

### _get_primary_crud()
```python
def _get_primary_crud(self):
    """Get the primary CRUD instance for this orchestrator."""
    raise NotImplementedError("Child orchestrators must implement _get_primary_crud method")
```

**Amaç:** Bu orchestrator'ın primary CRUD instance'ını döndür
