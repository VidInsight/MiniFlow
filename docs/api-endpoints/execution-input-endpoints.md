# Execution Input Endpoints Dokümantasyonu

Execution girdi verilerini okuma için endpoint'ler (Sadece Okuma).

**Not:** Bu endpoint'ler sadece okuma amaçlı olup, execution input oluşturma veya güncelleme işlemi yapılamaz.

## Endpoint Listesi

### 1. Execution Input Sayısını Getir
**GET** `/api/bff/execution-inputs/count`

#### Amaç
Sistemdeki toplam execution input sayısını getirir.

#### Girdi
- Query parametresi yok
- Request body yok

#### Çıktı
```json
{
  "data": {
    "count": 3247
  },
  "correlation_id": "uuid"
}
```

---

### 2. Execution Input Filtrele
**POST** `/api/bff/execution-inputs/filter`

#### Amaç
Belirli kriterlere göre execution input'larını filtreler.

#### Girdi
```json
{
  "filters": {
    "execution_id": "EX-XXXXXXXXXXXXX",
    "node_id": "ND-PROCESSXXXXXX",
    "data_type": "json",
    "size_min": 100,
    "size_max": 10000
  },
  "skip": 0,
  "limit": 50,
  "order_by_field": "created_at",
  "include_relationships": true
}
```

#### Çıktı
```json
{
  "data": {
    "items": [
      {
        "id": "EI-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:00:00.000Z",
        "execution_id": "EX-XXXXXXXXXXXXX",
        "node_id": "ND-PROCESSXXXXXX",
        "data": {
          "input_file": "/data/input.csv",
          "parameters": {
            "delimiter": ",",
            "encoding": "utf-8"
          }
        },
        "data_type": "json",
        "size_bytes": 1024,
        "checksum": "sha256:abc123..."
      }
    ],
    "total": 15,
    "skip": 0,
    "limit": 50
  },
  "message": "Retrieved successfully",
  "correlation_id": "uuid"
}
```

---

### 3. Execution Input'ları Listele
**GET** `/api/bff/execution-inputs/`

#### Amaç
Sistemdeki tüm execution input'larını listeler.

#### Girdi (Query Parametreleri)
- `skip`: integer (default: 0)
- `limit`: integer (default: 100, max: 1000)
- `order_by`: string
- `include_relationships`: boolean (default: false)
- `exclude_fields`: string

#### Çıktı
```json
{
  "data": {
    "items": [
      {
        "id": "EI-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:00:00.000Z",
        "execution_id": "EX-XXXXXXXXXXXXX",
        "node_id": "ND-STARTXXXXXXXX",
        "data": {
          "workflow_trigger": {
            "type": "manual",
            "user_id": "user123",
            "timestamp": "2025-01-01T00:00:00.000Z"
          }
        },
        "data_type": "json",
        "size_bytes": 256,
        "checksum": "sha256:def456..."
      }
    ],
    "total": 3247,
    "skip": 0,
    "limit": 100
  },
  "message": "Retrieved successfully",
  "correlation_id": "uuid"
}
```

---

### 4. Execution Input Detay Getir
**GET** `/api/bff/execution-inputs/{execution_input_id}`

#### Amaç
Belirli bir execution input'unun detay bilgilerini getirir.

#### Girdi
- **Path Parameter:** `execution_input_id` (string)

#### Çıktı
```json
{
  "data": {
    "id": "EI-XXXXXXXXXXXXX",
    "created_at": "2025-01-01T00:00:00.000Z",
    "execution_id": "EX-XXXXXXXXXXXXX",
    "node_id": "ND-PROCESSXXXXXX",
    "data": {
      "file_paths": [
        "/uploads/data1.csv",
        "/uploads/data2.csv"
      ],
      "processing_config": {
        "batch_size": 1000,
        "parallel_workers": 4,
        "timeout": 300
      },
      "validation_rules": {
        "required_columns": ["id", "name", "date"],
        "date_format": "YYYY-MM-DD",
        "allow_duplicates": false
      }
    },
    "data_type": "json",
    "size_bytes": 2048,
    "checksum": "sha256:789abc123def...",
    "metadata": {
      "source": "user_upload",
      "validated": true,
      "validation_timestamp": "2025-01-01T00:00:05.000Z"
    }
  },
  "message": "Retrieved successfully",
  "correlation_id": "uuid"
}
```

## Data Model

### Temel Alanlar
- `id`: Execution input ID (EI-XXXXXXXXXXXXX)
- `execution_id`: İlişkili execution ID
- `node_id`: İlişkili node ID
- `data`: Girdi verisi (JSON format)
- `data_type`: Veri tipi (json, text, binary)
- `size_bytes`: Veri boyutu
- `checksum`: Veri kontrolsüm değeri

### Veri Tipleri
- **json**: Yapılandırılmış JSON verisi
- **text**: Plain text verisi
- **binary**: Binary/dosya verisi

## Hata Durumları

### 404 Not Found
```json
{
  "error": {
    "code": "EXECUTION_INPUT_NOT_FOUND",
    "message": "Execution input not found",
    "details": {"execution_input_id": "EI-XXXXXXXXXXXXX"}
  },
  "correlation_id": "uuid"
}
```
