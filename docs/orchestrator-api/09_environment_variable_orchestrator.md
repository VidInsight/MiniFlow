# EnvironmentVariableOrchestrator API Documentation

EnvironmentVariableOrchestrator, environment variable yönetimi ve CRUD operasyonlarını yürütür.

## Genel Bilgiler

- **Sınıf:** `EnvironmentVariableOrchestrator`
- **Parent:** `BaseOrchestrator`
- **Modül:** `miniflow.database.orchestration.envar_orchestrator`
- **Primary Model:** `EnvironmentVariable`
- **Primary CRUD:** `envar_crud`

## EnvironmentVariable-Specific Metodlar

### create()
```python
@with_session
def create(self, session: Session, name: str, value: str, **kwargs) -> Dict[str, Any]
```

**Amaç:** Yeni environment variable oluştur

**Parametreler:**
- `name` (str): Variable adı (zorunlu)
- `value` (str): Variable değeri (zorunlu)
- `**kwargs`: Diğer environment variable alanları
  - `description` (str): Açıklama
  - `variable_type` (VariableType): Değişken tipi (default: STRING)
  - `scope` (VariableScope): Kapsam (default: GLOBAL)
  - `last_modified_by` (str): Son değiştiren kişi

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Oluşturulan environment variable'ın dictionary'si
- **Hata:** OrchestrationError

**Örnek Dönüş:**
```json
{
    "id": "EV-A1B2C3D4E5F6G7H8I",
    "name": "DATABASE_URL",
    "value": "postgresql://localhost:5432/miniflow",
    "description": "Main database connection string",
    "variable_type": "STRING",
    "scope": "GLOBAL",
    "last_accessed_at": null,
    "access_count": 0,
    "last_modified_by": "admin",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
}
```

**Not:** EnvironmentVariable modeli relationship'e sahip olmadığı için `include_relationships=True` kullanılsa bile aynı sonuç döner.

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

**Amaç:** Environment variable'ı adına göre getir

**Parametreler:**
- `name` (str): Variable adı
- `include_relationships` (bool): İlişkili objeleri dahil et
- `exclude_fields` (List[str]): Hariç tutulacak alanlar

**Dönen Değer:** `Optional[Dict[str, Any]]`
- **Başarılı:** Environment variable dictionary'si
- **Bulunamadı:** None
- **Hata:** OrchestrationError

**Örnek Dönüş:**
```json
{
    "id": "EV-A1B2C3D4E5F6G7H8I",
    "name": "DATABASE_URL",
    "value": "postgresql://localhost:5432/miniflow",
    "description": "Main database connection string",
    "variable_type": "STRING",
    "scope": "GLOBAL",
    "last_accessed_at": "2024-01-01T11:00:00",
    "access_count": 25,
    "last_modified_by": "admin",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
}
```

**Örnek Kullanım:**
```python
# Variable'ı adına göre getir
db_url = orchestrator.get_by_name("DATABASE_URL")

# Güvenlik için value alanını hariç tut
config_var = orchestrator.get_by_name(
    "API_SECRET", 
    exclude_fields=["value"]
)
```

### delete()
```python
@with_session
def delete(self, session: Session, record_id: str) -> Dict[str, Any]
```

**Amaç:** Environment variable'ı sil

**Parametreler:**
- `record_id` (str): Environment variable ID'si

**Dönen Değer:** `Dict[str, Any]`
- **Başarılı:** Silinen environment variable'ın dictionary'si
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

**Güvenlik Notu:** Sensitive value'lar için `exclude_fields=["value"]` kullanın.

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
# Global scope'daki variable'ları getir
global_vars = orchestrator.filter({"scope": "GLOBAL"})

# SECRET tipindeki variable'ları getir (value olmadan)
secrets = orchestrator.filter(
    {"variable_type": "SECRET"}, 
    exclude_fields=["value"]
)

# Belirli kullanıcının oluşturduğu variable'ları getir
user_vars = orchestrator.filter({"last_modified_by": "john_doe"})

# Sık kullanılan variable'ları getir (access_count > 10)
popular_vars = orchestrator.filter({"access_count": 10})  # Bu durumda > operatörü için özel CRUD metodu gerekebilir
```

### count_with_filter()
```python
def count_with_filter(filters: Dict[str, Any]) -> int
```

## Variable Types

```python
class VariableType(str, enum.Enum):
    STRING = "STRING"           # Metin değeri
    INTEGER = "INTEGER"         # Tam sayı
    FLOAT = "FLOAT"             # Ondalık sayı
    BOOLEAN = "BOOLEAN"         # True/False
    JSON = "JSON"               # JSON objesi
    SECRET = "SECRET"           # Gizli değer
    CREDENTIAL = "CREDENTIAL"   # Kimlik bilgisi
    FILE_PATH = "FILE_PATH"     # Dosya yolu
    URL = "URL"                 # Web adresi
```

## Variable Scopes

```python
class VariableScope(str, enum.Enum):
    GLOBAL = "GLOBAL"       # Tüm sistem
    WORKFLOW = "WORKFLOW"   # Belirli workflow
    TRIGGER = "TRIGGER"     # Trigger seviyesi
    USER = "USER"          # Kullanıcı seviyesi
    NODE = "NODE"          # Node seviyesi
```

## Environment Variable Alanları

### Temel Alanlar
- `id`: Environment variable ID'si (EV-...)
- `name`: Variable adı (unique)
- `value`: Variable değeri
- `description`: Açıklama

### Type ve Scope
- `variable_type`: Değişken tipi
- `scope`: Kapsam seviyesi

### Tracking Alanları
- `last_accessed_at`: Son erişim zamanı
- `access_count`: Erişim sayısı
- `last_modified_by`: Son değiştiren kişi

### Timestamps
- `created_at`: Oluşturulma zamanı
- `updated_at`: Güncellenme zamanı

## Güvenlik Considerations

### Sensitive Data Handling
```python
# SECRET ve CREDENTIAL tipindeki variable'lar için güvenlik
secrets = orchestrator.filter(
    {"variable_type": "SECRET"}, 
    exclude_fields=["value"]  # Value'yu dahil etme
)

# Log'larda value görünmemesi için
credential_info = orchestrator.get_by_name(
    "API_KEY", 
    exclude_fields=["value"]
)
```

### Access Tracking
```python
# Sık erişilen variable'ları monitör et
high_access_vars = orchestrator.filter({})  # Tüm variable'ları getir
for var in high_access_vars:
    if var["access_count"] > 1000:
        print(f"High access variable: {var['name']} - {var['access_count']} times")
```

## Usage Patterns

### Configuration Management
```python
# Sistem konfigürasyon variable'ları
config_vars = orchestrator.filter({"scope": "GLOBAL"})

database_configs = [v for v in config_vars if "DATABASE" in v["name"]]
api_configs = [v for v in config_vars if "API" in v["name"]]
```

### Type-based Filtering
```python
# Farklı tiplerdeki variable'ları getir
string_vars = orchestrator.filter({"variable_type": "STRING"})
json_configs = orchestrator.filter({"variable_type": "JSON"})
file_paths = orchestrator.filter({"variable_type": "FILE_PATH"})
```

### Scope-based Management
```python
# Workflow-specific variable'ları getir
workflow_vars = orchestrator.filter({"scope": "WORKFLOW"})

# User-specific variable'ları getir
user_vars = orchestrator.filter({"scope": "USER"})
```

## Value Parsing ve Validation

### Type-based Value Processing
```python
def parse_variable_value(var_dict):
    """Variable type'ına göre value'yu parse et"""
    var_type = var_dict["variable_type"]
    value = var_dict["value"]
    
    if var_type == "INTEGER":
        return int(value)
    elif var_type == "FLOAT":
        return float(value)
    elif var_type == "BOOLEAN":
        return value.lower() in ("true", "1", "yes", "on")
    elif var_type == "JSON":
        import json
        return json.loads(value)
    else:
        return value

# Kullanım
db_port_var = orchestrator.get_by_name("DATABASE_PORT")
if db_port_var:
    db_port = parse_variable_value(db_port_var)  # int değeri alır
```

## Monitoring ve Analytics

### Access Pattern Analysis
```python
# En çok kullanılan variable'ları bul
all_vars = orchestrator.get_all()
sorted_by_access = sorted(all_vars, key=lambda x: x["access_count"], reverse=True)

print("Most accessed variables:")
for var in sorted_by_access[:10]:
    print(f"  {var['name']}: {var['access_count']} accesses")
```

### Type Distribution Analysis
```python
# Variable tiplerinin dağılımını analiz et
all_vars = orchestrator.get_all()
type_distribution = {}

for var in all_vars:
    var_type = var["variable_type"]
    type_distribution[var_type] = type_distribution.get(var_type, 0) + 1

print("Variable type distribution:")
for var_type, count in type_distribution.items():
    print(f"  {var_type}: {count}")
```

### Scope Analysis
```python
# Scope dağılımını analiz et
all_vars = orchestrator.get_all()
scope_distribution = {}

for var in all_vars:
    scope = var["scope"]
    scope_distribution[scope] = scope_distribution.get(scope, 0) + 1

print("Variable scope distribution:")
for scope, count in scope_distribution.items():
    print(f"  {scope}: {count}")
```

## Best Practices

### Naming Conventions
```python
# Önerilen naming pattern'ları
naming_patterns = {
    "DATABASE": "DATABASE_*",      # DATABASE_URL, DATABASE_PORT
    "API": "API_*",               # API_KEY, API_URL
    "FEATURE": "FEATURE_*_ENABLED", # FEATURE_NOTIFICATIONS_ENABLED
    "TIMEOUT": "*_TIMEOUT_SECONDS", # SCRIPT_TIMEOUT_SECONDS
}
```

### Security Best Practices
```python
# Sensitive variable'ları her zaman güvenli şekilde handle et
def get_sensitive_variable(name):
    """Sensitive variable'ı güvenli şekilde getir"""
    var = orchestrator.get_by_name(name)
    if var and var["variable_type"] in ["SECRET", "CREDENTIAL"]:
        # Log'lama veya debug için value'yu maskele
        var_copy = var.copy()
        var_copy["value"] = "***HIDDEN***"
        return var_copy
    return var
```

### Environment-specific Management
```python
# Environment'a göre variable'ları organize et
def get_environment_config():
    """Environment-specific konfigürasyonu getir"""
    config = {}
    
    # Global variable'ları al
    global_vars = orchestrator.filter({"scope": "GLOBAL"})
    for var in global_vars:
        config[var["name"]] = parse_variable_value(var)
    
    return config
```

## Hata Durumları

### Variable Oluşturma Hataları
```python
# İsim boşsa
ValidationError("Variable name is required")

# Aynı isimde variable varsa
ValidationError("Variable name already exists")

# Geçersiz variable type
ValidationError("Invalid variable type")

# Geçersiz scope
ValidationError("Invalid variable scope")
```

### Variable Silme Hataları
```python
# Variable bulunamazsa
DatabaseQueryError("Environment variable 'EV-...' not found")

# Sistem kritik variable'ı silme koruması (CRUD seviyesinde)
ValidationError("Cannot delete system critical variable")
```

### Value Validation Hataları
```python
# INTEGER tipinde non-numeric value
ValidationError("Invalid integer value")

# JSON tipinde malformed JSON
ValidationError("Invalid JSON format")

# URL tipinde geçersiz URL
ValidationError("Invalid URL format")
```
