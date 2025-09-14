# Edge Endpoints Dokümantasyonu

Workflow edge/bağlantı yönetimi için tüm CRUD işlemleri.

## Endpoint Listesi

### 1. Edge Sayısını Getir
**GET** `/api/bff/edges/count`

#### Amaç
Sistemdeki toplam edge sayısını getirir.

#### Girdi
- Query parametresi yok
- Request body yok

#### Çıktı
```json
{
  "data": {
    "count": 189
  },
  "message": "Edges count retrieved",
  "correlation_id": "uuid",
  "timestamp": "2025-01-01T00:00:00.000Z"
}
```

---

### 2. Edge Filtrele
**POST** `/api/bff/edges/filter`

#### Amaç
Belirli kriterlere göre edge'leri filtreler ve sayfalama ile getirir.

#### Girdi
```json
{
  "filters": {
    "workflow_id": "WF-XXXXXXXXXXXXX",
    "source_node_id": "ND-XXXXXXXXXXXXX",
    "target_node_id": "ND-YYYYYYYYYYYYY",
    "edge_type": "SUCCESS",
    "status": "ACTIVE"
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
        "id": "ED-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "workflow_id": "WF-XXXXXXXXXXXXX",
        "source_node_id": "ND-XXXXXXXXXXXXX",
        "target_node_id": "ND-YYYYYYYYYYYYY",
        "edge_type": "SUCCESS",
        "status": "ACTIVE",
        "label": "Success Path",
        "condition": null,
        "weight": 1
      }
    ],
    "total": 15,
    "skip": 0,
    "limit": 50
  },
  "message": "Edges filtered",
  "correlation_id": "uuid"
}
```

---

### 3. Edge Oluştur
**POST** `/api/bff/edges/`

#### Amaç
İki node arasında yeni bir bağlantı oluşturur.

#### Girdi
```json
{
  "workflow_id": "WF-XXXXXXXXXXXXX",
  "source_node_id": "ND-XXXXXXXXXXXXX",
  "target_node_id": "ND-YYYYYYYYYYYYY",
  "edge_type": "SUCCESS",
  "label": "İşlem Başarılı",
  "condition": {
    "field": "status",
    "operator": "equals",
    "value": "completed"
  },
  "weight": 1,
  "metadata": {
    "description": "Normal akış bağlantısı",
    "color": "#4CAF50"
  }
}
```

**Zorunlu Alanlar:**
- `workflow_id`: string (Mevcut workflow ID'si)
- `source_node_id`: string (Kaynak node ID'si)
- `target_node_id`: string (Hedef node ID'si)
- `edge_type`: enum (SUCCESS, ERROR, CONDITION, DEFAULT)

**Opsiyonel Alanlar:**
- `label`: string (Edge etiketi)
- `condition`: object (Koşullu edge'ler için)
- `weight`: integer (Edge ağırlığı, default: 1)
- `metadata`: object (Ek bilgiler)

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "ED-XXXXXXXXXXXXX",
    "message": "Edge creation successful"
  },
  "message": "Edge created",
  "correlation_id": "uuid"
}
```

---

### 4. Edge'leri Listele
**GET** `/api/bff/edges/`

#### Amaç
Sistemdeki tüm edge'leri sayfalama ile listeler.

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
        "id": "ED-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "workflow_id": "WF-XXXXXXXXXXXXX",
        "source_node_id": "ND-STARTXXXXXXXX",
        "target_node_id": "ND-PROCESSXXXXXX",
        "edge_type": "DEFAULT",
        "status": "ACTIVE",
        "label": "Başlangıç",
        "condition": null,
        "weight": 1,
        "metadata": {
          "color": "#2196F3"
        }
      }
    ],
    "total": 189,
    "skip": 0,
    "limit": 100
  },
  "message": "Edges retrieved",
  "correlation_id": "uuid"
}
```

---

### 5. Edge Detay Getir
**GET** `/api/bff/edges/{edge_id}`

#### Amaç
Belirli bir edge'in detay bilgilerini getirir.

#### Girdi
- **Path Parameter:** `edge_id` (string) - Edge ID'si
- **Query Parameters:**
  - `include_relationships` (boolean, optional) - İlişkili verileri dahil et (default: false)
  - `exclude_fields` (string, optional) - Hariç tutulacak alanlar (virgülle ayrılmış)

#### Çıktı
```json
{
  "data": {
    "id": "ED-XXXXXXXXXXXXX",
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:00:00.000Z",
    "workflow_id": "WF-XXXXXXXXXXXXX",
    "source_node_id": "ND-PROCESSXXXXXX",
    "target_node_id": "ND-DECISIONXXXXX",
    "edge_type": "CONDITION",
    "status": "ACTIVE",
    "label": "Veri Kontrolü",
    "condition": {
      "field": "data_quality",
      "operator": "greater_than",
      "value": 0.8,
      "description": "Veri kalitesi %80'den yüksek olmalı"
    },
    "weight": 2,
    "metadata": {
      "description": "Veri kalite kontrolü için koşullu geçiş",
      "color": "#FF9800",
      "line_style": "dashed",
      "arrow_type": "arrow"
    }
  },
  "message": "Edge retrieved",
  "correlation_id": "uuid"
}
```

---

### 6. Edge Güncelle
**PUT** `/api/bff/edges/{edge_id}`

#### Amaç
Mevcut bir edge'i günceller.

#### Girdi
- **Path Parameter:** `edge_id` (string) - Edge ID'si
- **Request Body:**
```json
{
  "edge_type": "SUCCESS",
  "label": "Güncellenmiş Başarı Yolu",
  "condition": {
    "field": "result_status",
    "operator": "equals",
    "value": "success",
    "description": "İşlem başarıyla tamamlandı"
  },
  "weight": 3,
  "metadata": {
    "description": "Güncellenmiş bağlantı",
    "color": "#4CAF50",
    "line_style": "solid",
    "arrow_type": "arrow",
    "animation": "flow"
  }
}
```

**Tüm Alanlar Opsiyonel:**
- `edge_type`: enum
- `label`: string
- `condition`: object
- `weight`: integer
- `metadata`: object

**Not:** `source_node_id`, `target_node_id` ve `workflow_id` güncellenemez.

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "ED-XXXXXXXXXXXXX",
    "message": "Edge update successful"
  },
  "message": "Edge updated",
  "correlation_id": "uuid"
}
```

---

### 7. Edge Sil
**DELETE** `/api/bff/edges/{edge_id}`

#### Amaç
Bir edge'i siler.

#### Girdi
- **Path Parameter:** `edge_id` (string) - Edge ID'si

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "ED-XXXXXXXXXXXXX",
    "message": "Edge deletion successful"
  },
  "message": "Edge deleted",
  "correlation_id": "uuid"
}
```

**Önemli Notlar:**
- Edge silindiğinde workflow'un akışı etkilenir
- Execution'ı devam eden edge'ler silinemez

## Edge Tipleri

### Desteklenen Edge Tipleri
- **DEFAULT**: Varsayılan akış
- **SUCCESS**: Başarılı sonuç akışı
- **ERROR**: Hata durumu akışı
- **CONDITION**: Koşullu akış
- **TIMEOUT**: Zaman aşımı akışı
- **RETRY**: Tekrar deneme akışı

### Edge Durumları
- **ACTIVE**: Aktif bağlantı
- **INACTIVE**: Pasif bağlantı
- **DISABLED**: Devre dışı bağlantı

## Koşul Yapısı

### Desteklenen Operatörler
- `equals`: Eşittir
- `not_equals`: Eşit değildir
- `greater_than`: Büyüktür
- `less_than`: Küçüktür
- `greater_than_or_equal`: Büyük eşittir
- `less_than_or_equal`: Küçük eşittir
- `contains`: İçerir
- `not_contains`: İçermez
- `starts_with`: İle başlar
- `ends_with`: İle biter
- `regex`: Regex pattern

### Örnek Koşullar
```json
{
  "field": "status_code",
  "operator": "equals",
  "value": 200
}
```

```json
{
  "field": "error_message",
  "operator": "contains",
  "value": "timeout"
}
```

```json
{
  "field": "process_time",
  "operator": "less_than",
  "value": 30
}
```

## Hata Durumları

### 404 Not Found
```json
{
  "error": {
    "code": "EDGE_NOT_FOUND",
    "message": "Edge not found",
    "details": {"edge_id": "ED-XXXXXXXXXXXXX"}
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
    "details": {"field": "source_node_id", "error": "Source node not found"}
  },
  "correlation_id": "uuid"
}
```

### 409 Conflict
```json
{
  "error": {
    "code": "CIRCULAR_DEPENDENCY",
    "message": "Edge would create circular dependency",
    "details": {
      "source_node_id": "ND-XXXXXXXXXXXXX",
      "target_node_id": "ND-YYYYYYYYYYYYY"
    }
  },
  "correlation_id": "uuid"
}
```
