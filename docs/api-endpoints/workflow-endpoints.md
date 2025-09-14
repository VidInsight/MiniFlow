# Workflow Endpoints Dokümantasyonu

Workflow yönetimi için tüm CRUD işlemleri ve istatistik endpoint'leri.

## Endpoint Listesi

### 1. Workflow Sayısını Getir
**GET** `/api/bff/workflows/count`

#### Amaç
Sistemdeki toplam workflow sayısını getirir.

#### Girdi
- Query parametresi yok
- Request body yok

#### Çıktı
```json
{
  "data": {
    "count": 42
  },
  "message": "Workflows count retrieved",
  "correlation_id": "uuid",
  "timestamp": "2025-01-01T00:00:00.000Z"
}
```

---

### 2. Workflow Filtrele
**POST** `/api/bff/workflows/filter`

#### Amaç
Belirli kriterlere göre workflow'ları filtreler ve sayfalama ile getirir.

#### Girdi
```json
{
  "filters": {
    "status": "ACTIVE",
    "name": "test",
    "priority": 5
  },
  "skip": 0,
  "limit": 50,
  "order_by_field": "created_at",
  "include_relationships": false,
  "exclude_fields": ["description"]
}
```

#### Çıktı
```json
{
  "data": {
    "items": [
      {
        "id": "WF-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "name": "Test Workflow",
        "priority": 5,
        "status": "ACTIVE",
        "status_message": null
      }
    ],
    "total": 15,
    "skip": 0,
    "limit": 50
  },
  "message": "Workflows filtered",
  "correlation_id": "uuid"
}
```

---

### 3. Workflow Oluştur
**POST** `/api/bff/workflows/`

#### Amaç
Yeni bir workflow oluşturur.

#### Girdi
```json
{
  "name": "Yeni Workflow",
  "description": "Workflow açıklaması",
  "priority": 10
}
```

**Zorunlu Alanlar:**
- `name`: string (1-100 karakter, benzersiz)

**Opsiyonel Alanlar:**
- `description`: string (max 1000 karakter)
- `priority`: integer (0-100, default: 0)

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "WF-XXXXXXXXXXXXX",
    "message": "Workflow creation successful"
  },
  "message": "Workflow created",
  "correlation_id": "uuid"
}
```

---

### 4. Workflow'ları Listele
**GET** `/api/bff/workflows/`

#### Amaç
Sistemdeki tüm workflow'ları sayfalama ile listeler.

#### Girdi (Query Parametreleri)
- `skip`: integer (default: 0) - Atlanacak kayıt sayısı
- `limit`: integer (default: 100, max: 1000) - Maksimum kayıt sayısı
- `order_by`: string (opsiyonel) - Sıralama alanı
- `include_relationships`: boolean (default: false) - İlişkili verileri dahil et
- `exclude_fields`: string (opsiyonel) - Hariç tutulacak alanlar (virgülle ayrılmış)

#### Çıktı
```json
{
  "data": {
    "items": [
      {
        "id": "WF-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "name": "Test Workflow",
        "description": "Test açıklaması",
        "priority": 10,
        "status": "ACTIVE",
        "status_message": null
      }
    ],
    "total": 100,
    "skip": 0,
    "limit": 100
  },
  "message": "Workflows retrieved",
  "correlation_id": "uuid"
}
```

---

### 5. Workflow Detay Getir
**GET** `/api/bff/workflows/{workflow_id}`

#### Amaç
Belirli bir workflow'un detay bilgilerini getirir.

#### Girdi
- **Path Parameter:** `workflow_id` (string) - Workflow ID'si
- **Query Parameters:**
  - `include_relationships` (boolean, optional) - İlişkili verileri dahil et (default: false)
  - `exclude_fields` (string, optional) - Hariç tutulacak alanlar (virgülle ayrılmış)

#### Örnekler
```bash
# Temel kullanım
GET /api/bff/workflows/WF-123456789

# İlişkili verilerle
GET /api/bff/workflows/WF-123456789?include_relationships=true

# Belirli alanları hariç tutarak
GET /api/bff/workflows/WF-123456789?exclude_fields=description,status_message

# Her iki parametre birlikte
GET /api/bff/workflows/WF-123456789?include_relationships=true&exclude_fields=status_message
```

#### Çıktı
```json
{
  "data": {
    "id": "WF-XXXXXXXXXXXXX",
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:00:00.000Z",
    "name": "Test Workflow",
    "description": "Test açıklaması",
    "priority": 10,
    "status": "ACTIVE",
    "status_message": null
  },
  "message": "Workflow retrieved",
  "correlation_id": "uuid"
}
```

---

### 6. Workflow Güncelle
**PUT** `/api/bff/workflows/{workflow_id}`

#### Amaç
Mevcut bir workflow'u günceller.

#### Girdi
- **Path Parameter:** `workflow_id` (string) - Workflow ID'si
- **Request Body:**
```json
{
  "name": "Güncellenmiş Workflow",
  "description": "Yeni açıklama",
  "priority": 20,
  "status": "INACTIVE"
}
```

**Tüm Alanlar Opsiyonel:**
- `name`: string (1-100 karakter)
- `description`: string (max 1000 karakter)
- `priority`: integer (0-100)
- `status`: WorkflowStatus enum

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "WF-XXXXXXXXXXXXX",
    "message": "Workflow update successful"
  },
  "message": "Workflow updated",
  "correlation_id": "uuid"
}
```

---

### 7. Workflow Sil
**DELETE** `/api/bff/workflows/{workflow_id}`

#### Amaç
Bir workflow'u ve ilişkili tüm verilerini (nodes, edges, executions) siler.

#### Girdi
- **Path Parameter:** `workflow_id` (string) - Workflow ID'si

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "WF-XXXXXXXXXXXXX",
    "message": "Workflow deletion successful"
  },
  "message": "Workflow deleted",
  "correlation_id": "uuid"
}
```

**Önemli Notlar:**
- Aktif execution'ları olan workflow'lar silinemez
- Silme işlemi cascade olarak gerçekleşir (tüm ilişkili veriler silinir)

---

### 8. Workflow İstatistikleri
**GET** `/api/bff/workflows/{workflow_id}/stats`

#### Amaç
Belirli bir workflow'un execution istatistiklerini getirir.

#### Girdi
- **Path Parameter:** `workflow_id` (string) - Workflow ID'si

#### Çıktı
```json
{
  "data": {
    "total_executions": 150,
    "successful_executions": 140,
    "failed_executions": 8,
    "cancelled_executions": 2,
    "avg_execution_duration": 120.5,
    "min_execution_duration": 45.2,
    "max_execution_duration": 300.8,
    "last_executed_at": "2025-01-01T00:00:00.000Z",
    "last_successful_execution_at": "2025-01-01T00:00:00.000Z",
    "last_failed_execution_at": "2024-12-30T00:00:00.000Z"
  },
  "message": "Workflow Stats",
  "correlation_id": "uuid"
}
```

## Hata Durumları

### 404 Not Found
```json
{
  "error": {
    "code": "WORKFLOW_NOT_FOUND",
    "message": "Workflow not found",
    "details": {"workflow_id": "WF-XXXXXXXXXXXXX"}
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
    "details": {"field": "name", "error": "Name is required"}
  },
  "correlation_id": "uuid"
}
```

### 409 Conflict
```json
{
  "error": {
    "code": "WORKFLOW_HAS_ACTIVE_EXECUTIONS",
    "message": "Cannot delete workflow with active executions",
    "details": {"workflow_id": "WF-XXXXXXXXXXXXX"}
  },
  "correlation_id": "uuid"
}
```
