# Execution Endpoints Dokümantasyonu

Execution monitoring ve sorgulama için endpoint'ler (Sadece Okuma).

**Not:** Bu endpoint'ler sadece okuma amaçlı olup, execution oluşturma veya güncelleme işlemi yapılamaz.

## Endpoint Listesi

### 1. Execution Sayısını Getir
**GET** `/api/bff/executions/count`

#### Amaç
Sistemdeki toplam execution sayısını getirir.

#### Girdi
- Query parametresi yok
- Request body yok

#### Çıktı
```json
{
  "data": {
    "count": 1542
  },
  "message": "Executions count retrieved",
  "correlation_id": "uuid",
  "timestamp": "2025-01-01T00:00:00.000Z"
}
```

---

### 2. Execution Filtrele
**POST** `/api/bff/executions/filter`

#### Amaç
Belirli kriterlere göre execution'ları filtreler ve sayfalama ile getirir.

#### Girdi
```json
{
  "filters": {
    "workflow_id": "WF-XXXXXXXXXXXXX",
    "status": "COMPLETED",
    "started_at_from": "2025-01-01T00:00:00.000Z",
    "started_at_to": "2025-01-31T23:59:59.999Z",
    "duration_min": 10,
    "duration_max": 300
  },
  "skip": 0,
  "limit": 50,
  "order_by_field": "started_at",
  "include_relationships": true,
  "exclude_fields": ["logs"]
}
```

#### Çıktı
```json
{
  "data": {
    "items": [
      {
        "id": "EX-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:05:00.000Z",
        "workflow_id": "WF-XXXXXXXXXXXXX",
        "status": "COMPLETED",
        "started_at": "2025-01-01T00:00:00.000Z",
        "completed_at": "2025-01-01T00:05:00.000Z",
        "duration_seconds": 300,
        "success": true,
        "error_message": null,
        "result_summary": {
          "processed_nodes": 5,
          "successful_nodes": 5,
          "failed_nodes": 0
        }
      }
    ],
    "total": 25,
    "skip": 0,
    "limit": 50
  },
  "message": "Executions filtered",
  "correlation_id": "uuid"
}
```

---

### 3. Execution'ları Listele
**GET** `/api/bff/executions/`

#### Amaç
Sistemdeki tüm execution'ları sayfalama ile listeler.

#### Girdi (Query Parametreleri)
- `skip`: integer (default: 0)
- `limit`: integer (default: 100, max: 1000)
- `order_by`: string (opsiyonel, önerilen: "started_at")
- `include_relationships`: boolean (default: false)
- `exclude_fields`: string (opsiyonel)

#### Çıktı
```json
{
  "data": {
    "items": [
      {
        "id": "EX-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:05:00.000Z",
        "workflow_id": "WF-XXXXXXXXXXXXX",
        "status": "RUNNING",
        "started_at": "2025-01-01T00:00:00.000Z",
        "completed_at": null,
        "duration_seconds": null,
        "success": null,
        "error_message": null,
        "current_node_id": "ND-PROCESSXXXXXX",
        "progress_percentage": 60,
        "result_summary": null,
        "metadata": {
          "trigger_type": "manual",
          "triggered_by": "user123"
        }
      },
      {
        "id": "EX-YYYYYYYYYYYYY",
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:03:00.000Z",
        "workflow_id": "WF-ZZZZZZZZZZZZZ",
        "status": "FAILED",
        "started_at": "2025-01-01T00:00:00.000Z",
        "completed_at": "2025-01-01T00:03:00.000Z",
        "duration_seconds": 180,
        "success": false,
        "error_message": "Node ND-VALIDATOR failed: Invalid input data",
        "current_node_id": "ND-VALIDATOR",
        "progress_percentage": 40,
        "result_summary": {
          "processed_nodes": 2,
          "successful_nodes": 1,
          "failed_nodes": 1
        }
      }
    ],
    "total": 1542,
    "skip": 0,
    "limit": 100
  },
  "message": "Executions retrieved",
  "correlation_id": "uuid"
}
```

---

### 4. Execution Detay Getir
**GET** `/api/bff/executions/{execution_id}`

#### Amaç
Belirli bir execution'ın detay bilgilerini getirir.

#### Girdi
- **Path Parameter:** `execution_id` (string) - Execution ID'si
- **Query Parameters:**
  - `include_relationships` (boolean, optional) - İlişkili verileri dahil et (default: false)
  - `exclude_fields` (string, optional) - Hariç tutulacak alanlar (virgülle ayrılmış)

#### Çıktı
```json
{
  "data": {
    "id": "EX-XXXXXXXXXXXXX",
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:05:30.000Z",
    "workflow_id": "WF-XXXXXXXXXXXXX",
    "status": "COMPLETED",
    "started_at": "2025-01-01T00:00:00.000Z",
    "completed_at": "2025-01-01T00:05:30.000Z",
    "duration_seconds": 330,
    "success": true,
    "error_message": null,
    "current_node_id": null,
    "progress_percentage": 100,
    "result_summary": {
      "processed_nodes": 8,
      "successful_nodes": 8,
      "failed_nodes": 0,
      "total_processing_time": 330,
      "data_processed": {
        "input_records": 1000,
        "output_records": 985,
        "filtered_records": 15
      }
    },
    "execution_log": [
      {
        "timestamp": "2025-01-01T00:00:00.000Z",
        "node_id": "ND-START",
        "status": "STARTED",
        "message": "Execution started"
      },
      {
        "timestamp": "2025-01-01T00:00:05.000Z",
        "node_id": "ND-START",
        "status": "COMPLETED",
        "message": "Start node completed",
        "duration": 5
      },
      {
        "timestamp": "2025-01-01T00:00:05.000Z",
        "node_id": "ND-LOADER",
        "status": "STARTED",
        "message": "Data loading started"
      }
    ],
    "metadata": {
      "trigger_type": "schedule",
      "triggered_by": "system",
      "trigger_time": "2025-01-01T00:00:00.000Z",
      "environment": "production",
      "execution_context": {
        "cpu_cores": 4,
        "memory_limit": "2GB",
        "timeout": 1800
      }
    }
  },
  "message": "Execution retrieved",
  "correlation_id": "uuid"
}
```

## Execution Durumları

### Execution Status'ları
- **PENDING**: Beklemede
- **RUNNING**: Çalışıyor
- **COMPLETED**: Tamamlandı
- **FAILED**: Başarısız
- **CANCELLED**: İptal edildi
- **TIMEOUT**: Zaman aşımı
- **PAUSED**: Duraklatıldı

### Execution Sonuçları
- **success**: `true` (başarılı), `false` (başarısız), `null` (devam ediyor)

## Filtre Kriterleri

### Desteklenen Filter Alanları
- `workflow_id`: string - Belirli workflow'un execution'ları
- `status`: enum - Execution durumu
- `success`: boolean - Başarılı/başarısız execution'lar
- `started_at_from`: datetime - Başlangıç tarihi (den)
- `started_at_to`: datetime - Başlangıç tarihi (e)
- `completed_at_from`: datetime - Bitiş tarihi (den)
- `completed_at_to`: datetime - Bitiş tarihi (e)
- `duration_min`: integer - Minimum süre (saniye)
- `duration_max`: integer - Maksimum süre (saniye)
- `current_node_id`: string - Şu anda çalışan node

### Örnek Complex Filter
```json
{
  "filters": {
    "workflow_id": "WF-XXXXXXXXXXXXX",
    "status": ["COMPLETED", "FAILED"],
    "started_at_from": "2025-01-01T00:00:00.000Z",
    "started_at_to": "2025-01-31T23:59:59.999Z",
    "duration_min": 60,
    "success": false
  },
  "skip": 0,
  "limit": 25,
  "order_by_field": "duration_seconds",
  "include_relationships": false,
  "exclude_fields": ["execution_log", "metadata"]
}
```

## Execution Monitoring

### Real-time Status
Execution'ları gerçek zamanlı takip etmek için:
```json
{
  "filters": {
    "status": ["RUNNING", "PENDING"],
    "started_at_from": "2025-01-01T00:00:00.000Z"
  },
  "order_by_field": "started_at",
  "limit": 50
}
```

### Performance Analysis
Performans analizi için:
```json
{
  "filters": {
    "workflow_id": "WF-XXXXXXXXXXXXX",
    "status": "COMPLETED",
    "started_at_from": "2025-01-01T00:00:00.000Z"
  },
  "include_relationships": true,
  "exclude_fields": ["execution_log"],
  "order_by_field": "duration_seconds"
}
```

## Hata Durumları

### 404 Not Found
```json
{
  "error": {
    "code": "EXECUTION_NOT_FOUND",
    "message": "Execution not found",
    "details": {"execution_id": "EX-XXXXXXXXXXXXX"}
  },
  "correlation_id": "uuid"
}
```

### 400 Bad Request
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid filter criteria",
    "details": {"field": "started_at_from", "error": "Invalid datetime format"}
  },
  "correlation_id": "uuid"
}
```

### 403 Forbidden
```json
{
  "error": {
    "code": "READ_ONLY_ENDPOINT",
    "message": "This endpoint is read-only",
    "details": {"operation": "create", "endpoint": "/executions"}
  },
  "correlation_id": "uuid"
}
```

## Execution Data Model

### Temel Alanlar
- `id`: Benzersiz execution ID'si (EX-XXXXXXXXXXXXX)
- `workflow_id`: İlişkili workflow ID'si
- `status`: Mevcut execution durumu
- `started_at`: Başlangıç zamanı
- `completed_at`: Bitiş zamanı (null ise devam ediyor)
- `duration_seconds`: Toplam süre (saniye)
- `success`: Başarı durumu
- `error_message`: Hata mesajı (varsa)

### İlerleme Takibi
- `current_node_id`: Şu anda işlem gören node
- `progress_percentage`: İlerleme yüzdesi (0-100)
- `result_summary`: Özet sonuçlar

### Metadata
- `trigger_type`: Tetikleme türü (manual, schedule, api)
- `triggered_by`: Tetikleyen kullanıcı/sistem
- `execution_context`: Çalışma ortamı bilgileri
