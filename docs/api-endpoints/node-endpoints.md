# Node Endpoints Dokümantasyonu

Workflow node yönetimi için tüm CRUD işlemleri.

## Endpoint Listesi

### 1. Node Sayısını Getir
**GET** `/api/bff/nodes/count`

#### Amaç
Sistemdeki toplam node sayısını getirir.

#### Girdi
- Query parametresi yok
- Request body yok

#### Çıktı
```json
{
  "data": {
    "count": 256
  },
  "message": "Nodes count retrieved",
  "correlation_id": "uuid",
  "timestamp": "2025-01-01T00:00:00.000Z"
}
```

---

### 2. Node Filtrele
**POST** `/api/bff/nodes/filter`

#### Amaç
Belirli kriterlere göre node'ları filtreler ve sayfalama ile getirir.

#### Girdi
```json
{
  "filters": {
    "workflow_id": "WF-XXXXXXXXXXXXX",
    "node_type": "SCRIPT",
    "status": "ACTIVE",
    "name": "processor"
  },
  "skip": 0,
  "limit": 50,
  "order_by_field": "created_at",
  "include_relationships": true,
  "exclude_fields": ["metadata"]
}
```

#### Çıktı
```json
{
  "data": {
    "items": [
      {
        "id": "ND-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "workflow_id": "WF-XXXXXXXXXXXXX",
        "name": "Data Processor",
        "node_type": "SCRIPT",
        "position_x": 150,
        "position_y": 200,
        "status": "ACTIVE",
        "script_id": "SC-XXXXXXXXXXXXX",
        "input_schema": {},
        "output_schema": {}
      }
    ],
    "total": 25,
    "skip": 0,
    "limit": 50
  },
  "message": "Nodes filtered",
  "correlation_id": "uuid"
}
```

---

### 3. Node Oluştur
**POST** `/api/bff/nodes/`

#### Amaç
Workflow için yeni bir node oluşturur.

#### Girdi
```json
{
  "workflow_id": "WF-XXXXXXXXXXXXX",
  "name": "Yeni Node",
  "node_type": "SCRIPT",
  "position_x": 100,
  "position_y": 150,
  "script_id": "SC-XXXXXXXXXXXXX",
  "description": "Node açıklaması",
  "input_schema": {
    "type": "object",
    "properties": {
      "input_data": {"type": "string"}
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "result": {"type": "object"}
    }
  },
  "metadata": {
    "timeout": 300,
    "retry_count": 3
  }
}
```

**Zorunlu Alanlar:**
- `workflow_id`: string (Mevcut workflow ID'si)
- `name`: string (Node adı)
- `node_type`: enum (SCRIPT, START, END, DECISION, etc.)
- `position_x`: integer (Canvas üzerindeki X koordinatı)
- `position_y`: integer (Canvas üzerindeki Y koordinatı)

**Opsiyonel Alanlar:**
- `script_id`: string (SCRIPT type için gerekli)
- `description`: string
- `input_schema`: object
- `output_schema`: object
- `metadata`: object

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "ND-XXXXXXXXXXXXX",
    "message": "Node creation successful"
  },
  "message": "Node created",
  "correlation_id": "uuid"
}
```

---

### 4. Node'ları Listele
**GET** `/api/bff/nodes/`

#### Amaç
Sistemdeki tüm node'ları sayfalama ile listeler.

#### Girdi (Query Parametreleri)
- `skip`: integer (default: 0)
- `limit`: integer (default: 100, max: 1000)
- `order_by`: string (opsiyonel)
- `include_relationships`: boolean (default: false)
- `exclude_fields`: string (opsiyonel)

#### Çıktı
```json
{
  "data": {
    "items": [
      {
        "id": "ND-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "workflow_id": "WF-XXXXXXXXXXXXX",
        "name": "Start Node",
        "node_type": "START",
        "position_x": 50,
        "position_y": 100,
        "status": "ACTIVE",
        "script_id": null,
        "description": "Workflow başlangıç node'u",
        "input_schema": {},
        "output_schema": {},
        "metadata": {}
      }
    ],
    "total": 256,
    "skip": 0,
    "limit": 100
  },
  "message": "Nodes retrieved",
  "correlation_id": "uuid"
}
```

---

### 5. Node Detay Getir
**GET** `/api/bff/nodes/{node_id}`

#### Amaç
Belirli bir node'un detay bilgilerini getirir.

#### Girdi
- **Path Parameter:** `node_id` (string) - Node ID'si
- **Query Parameters:**
  - `include_relationships` (boolean, optional) - İlişkili verileri dahil et (default: false)
  - `exclude_fields` (string, optional) - Hariç tutulacak alanlar (virgülle ayrılmış)

#### Çıktı
```json
{
  "data": {
    "id": "ND-XXXXXXXXXXXXX",
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:00:00.000Z",
    "workflow_id": "WF-XXXXXXXXXXXXX",
    "name": "Data Processor",
    "node_type": "SCRIPT",
    "position_x": 150,
    "position_y": 200,
    "status": "ACTIVE",
    "script_id": "SC-XXXXXXXXXXXXX",
    "description": "CSV veri işleme node'u",
    "input_schema": {
      "type": "object",
      "properties": {
        "file_path": {"type": "string"},
        "delimiter": {"type": "string", "default": ","}
      }
    },
    "output_schema": {
      "type": "object",
      "properties": {
        "processed_data": {"type": "array"},
        "row_count": {"type": "integer"}
      }
    },
    "metadata": {
      "timeout": 600,
      "retry_count": 3,
      "memory_limit": "512MB"
    }
  },
  "message": "Node retrieved",
  "correlation_id": "uuid"
}
```

---

### 6. Node Güncelle
**PUT** `/api/bff/nodes/{node_id}`

#### Amaç
Mevcut bir node'u günceller.

#### Girdi
- **Path Parameter:** `node_id` (string) - Node ID'si
- **Request Body:**
```json
{
  "name": "Güncellenmiş Processor",
  "position_x": 200,
  "position_y": 250,
  "description": "Güncellenmiş açıklama",
  "input_schema": {
    "type": "object",
    "properties": {
      "file_path": {"type": "string"},
      "delimiter": {"type": "string", "default": ";"},
      "encoding": {"type": "string", "default": "utf-8"}
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "processed_data": {"type": "array"},
      "row_count": {"type": "integer"},
      "processing_time": {"type": "number"}
    }
  },
  "metadata": {
    "timeout": 900,
    "retry_count": 5,
    "memory_limit": "1GB"
  }
}
```

**Tüm Alanlar Opsiyonel:**
- `name`: string
- `position_x`: integer
- `position_y`: integer
- `description`: string
- `script_id`: string
- `input_schema`: object
- `output_schema`: object
- `metadata`: object

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "ND-XXXXXXXXXXXXX",
    "message": "Node update successful"
  },
  "message": "Node updated",
  "correlation_id": "uuid"
}
```

---

### 7. Node Sil
**DELETE** `/api/bff/nodes/{node_id}`

#### Amaç
Bir node'u ve ilişkili edge'leri siler.

#### Girdi
- **Path Parameter:** `node_id` (string) - Node ID'si

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "ND-XXXXXXXXXXXXX",
    "message": "Node deletion successful"
  },
  "message": "Node deleted",
  "correlation_id": "uuid"
}
```

**Önemli Notlar:**
- Node silindiğinde, bu node'a bağlı tüm edge'ler de otomatik silinir
- Execution'ı devam eden node'lar silinemez

## Node Tipleri

### Desteklenen Node Tipleri
- **START**: Workflow başlangıç node'u
- **END**: Workflow bitiş node'u
- **SCRIPT**: Script çalıştırma node'u
- **DECISION**: Karar verme node'u
- **PARALLEL**: Paralel işlem node'u
- **JOIN**: Birleştirme node'u
- **WAIT**: Bekleme node'u

### Node Durumları
- **ACTIVE**: Aktif node
- **INACTIVE**: Pasif node
- **ERROR**: Hatalı node
- **PROCESSING**: İşlem halinde

## Hata Durumları

### 404 Not Found
```json
{
  "error": {
    "code": "NODE_NOT_FOUND",
    "message": "Node not found",
    "details": {"node_id": "ND-XXXXXXXXXXXXX"}
  },
  "correlation_id": "uuid"
}
```

### 400 Bad Request
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {"field": "workflow_id", "error": "Invalid workflow ID"}
  },
  "correlation_id": "uuid"
}
```

### 409 Conflict
```json
{
  "error": {
    "code": "NODE_IN_USE",
    "message": "Cannot delete node with active connections",
    "details": {"node_id": "ND-XXXXXXXXXXXXX", "edge_count": 3}
  },
  "correlation_id": "uuid"
}
```
