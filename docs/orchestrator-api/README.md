# MiniFlow Orchestrator API Documentation

Bu dokümanlar, MiniFlow orchestrator katmanında bulunan tüm fonksiyonların ne döndürdüğünü ve nasıl kullanıldığını detaylı olarak açıklar.

## Orchestrator Katmanı Genel Bakış

MiniFlow orchestrator katmanı, veritabanı CRUD işlemlerini yöneten ve iş mantığı katmanıdır. Her orchestrator, belirli bir model için CRUD operasyonları ve o modele özgü iş mantığı operasyonları sağlar.

### Temel Serialization Mekanizması

Tüm orchestrator'lar aynı serialization mekanizmasını kullanır:

#### BaseModel.to_dict() Metodu
```python
def to_dict(self, include_relationships=False, exclude_fields=None) -> dict
```

**Parametreler:**
- `include_relationships` (bool): İlişkili objeleri dahil et (varsayılan: False)
- `exclude_fields` (list): Hariç tutulacak alanlar (varsayılan: None)

**Dönen Değer:** Model'in dictionary reprezentasyonu

**🔗 Relationship Handling:**
- `include_relationships=False`: Sadece model'in kendi alanları döner
- `include_relationships=True`: İlişkili modellerin data'sı da dahil edilir
- İlişkili modeller recursive olarak `include_relationships=False` ile serialize edilir (sonsuz loop'u önlemek için)
- Collection relationships (List) olarak, single relationships (Object) olarak döner

**⚠️ Performance Not:** `include_relationships=True` büyük data setleri döndürebilir, dikkatli kullanın.

#### BaseOrchestrator Serialization Metodları

1. **_serialize_single_result()** - Tek sonucu serialize eder
2. **_serialize_multiple_results()** - Çoklu sonuçları serialize eder

## Model Relationships Haritası

| Model | İlişkiler | Açıklama |
|-------|-----------|----------|
| **Workflow** | `nodes`, `edges`, `executions` | Workflow'daki tüm bileşenler |
| **Node** | `workflow`, `script`, `outgoing_edges`, `incoming_edges`, `execution_inputs`, `execution_outputs` | Node'un tüm bağlantıları ve execution geçmişi |
| **Edge** | `workflow`, `from_node`, `to_node` | Edge'in bağladığı workflow ve node'lar |
| **Script** | `nodes` | Script'i kullanan node'lar |
| **Execution** | `workflow`, `execution_inputs`, `execution_outputs` | Execution'ın tüm detayları |
| **ExecutionInput** | `execution`, `workflow`, `node` | Input'un bağlı olduğu objeler |
| **ExecutionOutput** | `execution`, `workflow`, `node` | Output'un bağlı olduğu objeler |
| **EnvironmentVariable** | *relationship yok* | Bağımsız model |
| **FileUpload** | *relationship yok* | Bağımsız model |

## Orchestrator Listesi

| Orchestrator | Açıklama | Relationships | Doküman |
|-------------|----------|---------------|---------|
| BaseOrchestrator | Temel orchestrator sınıfı ve generic CRUD operasyonları | N/A | [BaseOrchestrator](./01_base_orchestrator.md) |
| WorkflowOrchestrator | Workflow yönetimi ve CRUD operasyonları | ✅ Zengin | [WorkflowOrchestrator](./02_workflow_orchestrator.md) |
| NodeOrchestrator | Node yönetimi ve CRUD operasyonları | ✅ Çok Zengin | [NodeOrchestrator](./03_node_orchestrator.md) |
| EdgeOrchestrator | Edge yönetimi ve CRUD operasyonları | ✅ Orta | [EdgeOrchestrator](./04_edge_orchestrator.md) |
| ScriptOrchestrator | Script yönetimi ve CRUD operasyonları | ✅ Basit | [ScriptOrchestrator](./05_script_orchestrator.md) |
| ExecutionOrchestrator | Execution monitoring (READ-ONLY) | ✅ Zengin | [ExecutionOrchestrator](./06_execution_orchestrator.md) |
| ExecutionInputOrchestrator | ExecutionInput monitoring (READ-ONLY) | ✅ Orta | [ExecutionInputOrchestrator](./07_execution_input_orchestrator.md) |
| ExecutionOutputOrchestrator | ExecutionOutput monitoring (READ-ONLY) | ✅ Orta | [ExecutionOutputOrchestrator](./08_execution_output_orchestrator.md) |
| EnvironmentVariableOrchestrator | Environment variable yönetimi | ❌ Yok | [EnvironmentVariableOrchestrator](./09_environment_variable_orchestrator.md) |
| FileUploadOrchestrator | File upload yönetimi | ❌ Yok | [FileUploadOrchestrator](./10_file_upload_orchestrator.md) |

## Genel Return Type Patternleri

### Tek Obje Dönen Metodlar
```python
-> Optional[Dict[str, Any]]  # None veya model dictionary'si
```

### Çoklu Obje Dönen Metodlar
```python
-> List[Dict[str, Any]]      # Model dictionary'lerinin listesi
```

### Sayı Dönen Metodlar
```python
-> int                       # Kayıt sayısı
```

### Delete İşlemleri
```python
-> Dict[str, Any]           # Silinen objenin dictionary'si veya deletion confirmation
```

### Create/Update İşlemleri
```python
-> Dict[str, Any]           # Oluşturulan/güncellenen objenin dictionary'si
```

## Hata Yönetimi

Tüm orchestrator metodları standardize edilmiş hata yönetimi kullanır:
- `OrchestrationError` - Orchestration katmanı hataları
- `ValidationError` - Validasyon hataları  
- `DatabaseQueryError` - Veritabanı sorgu hataları

Her hata, `ErrorContext` ile zenginleştirilmiş detaylı bilgi içerir.

## 📋 Döküman Güncellemeleri

Bu dökümanlar aşağıdaki detayları içerir:

### ✅ Her Orchestrator İçin
- **Temel Return Examples**: `include_relationships=False` (varsayılan)
- **Detaylı Return Examples**: `include_relationships=True` (ilişkilerle)
- **Method Signatures**: Tüm parametreler ve return type'lar
- **Error Handling**: Specific hata tipleri ve durumları
- **Usage Patterns**: Gerçek kullanım örnekleri
- **Performance Considerations**: Önemli notlar

### 🔗 Relationship Detayları
- **Workflow**: 3 relationship (nodes, edges, executions)
- **Node**: 6 relationship (en zengin model)
- **Edge**: 3 relationship (workflow, from_node, to_node)
- **Script**: 1 relationship (nodes)
- **Execution**: 3 relationship (workflow, inputs, outputs)
- **ExecutionInput/Output**: 3 relationship her biri
- **EnvironmentVariable/FileUpload**: Relationship yok

### 🎯 Kullanım Önerileri
- **Performans için**: Basic response'ları kullanın
- **UI için**: Relationship'li response'ları kullanın
- **Analytics için**: Specific filter metodlarını kullanın
- **Monitoring için**: READ-ONLY orchestrator'ları kullanın
