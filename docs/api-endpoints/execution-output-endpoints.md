# Execution Output Endpoints Dokümantasyonu

Execution çıktı verilerini okuma için endpoint'ler (Sadece Okuma).

**Not:** Bu endpoint'ler sadece okuma amaçlı olup, execution output oluşturma veya güncelleme işlemi yapılamaz.

## Endpoint Listesi

### 1. Execution Output Sayısını Getir
**GET** `/api/bff/execution-outputs/count`

#### Amaç
Sistemdeki toplam execution output sayısını getirir.

#### Girdi
- Query parametresi yok
- Request body yok

#### Çıktı
```json
{
  "data": {
    "count": 2891
  },
  "correlation_id": "uuid"
}
```

---

### 2. Execution Output Filtrele
**POST** `/api/bff/execution-outputs/filter`

#### Amaç
Belirli kriterlere göre execution output'larını filtreler.

#### Girdi
```json
{
  "filters": {
    "execution_id": "EX-XXXXXXXXXXXXX",
    "node_id": "ND-PROCESSXXXXXX",
    "data_type": "json",
    "size_min": 500,
    "size_max": 50000,
    "success": true
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
        "id": "EO-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:05:00.000Z",
        "execution_id": "EX-XXXXXXXXXXXXX",
        "node_id": "ND-PROCESSXXXXXX",
        "data": {
          "processed_records": 1000,
          "success_count": 985,
          "error_count": 15,
          "output_file": "/results/processed_data.json"
        },
        "data_type": "json",
        "size_bytes": 2048,
        "success": true,
        "error_message": null,
        "checksum": "sha256:def789..."
      }
    ],
    "total": 25,
    "skip": 0,
    "limit": 50
  },
  "message": "Retrieved successfully",
  "correlation_id": "uuid"
}
```

---

### 3. Execution Output'ları Listele
**GET** `/api/bff/execution-outputs/`

#### Amaç
Sistemdeki tüm execution output'larını listeler.

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
        "id": "EO-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:05:30.000Z",
        "execution_id": "EX-XXXXXXXXXXXXX",
        "node_id": "ND-ENDXXXXXXXXX",
        "data": {
          "final_result": {
            "status": "completed",
            "total_processing_time": 330,
            "summary": {
              "input_files": 2,
              "output_files": 1,
              "records_processed": 2000,
              "errors": 0
            }
          }
        },
        "data_type": "json",
        "size_bytes": 1024,
        "success": true,
        "error_message": null,
        "checksum": "sha256:abc123...",
        "execution_duration_ms": 330000
      }
    ],
    "total": 2891,
    "skip": 0,
    "limit": 100
  },
  "message": "Retrieved successfully",
  "correlation_id": "uuid"
}
```

---

### 4. Execution Output Detay Getir
**GET** `/api/bff/execution-outputs/{execution_output_id}`

#### Amaç
Belirli bir execution output'unun detay bilgilerini getirir.

#### Girdi
- **Path Parameter:** `execution_output_id` (string)

#### Çıktı
```json
{
  "data": {
    "id": "EO-XXXXXXXXXXXXX",
    "created_at": "2025-01-01T00:03:45.000Z",
    "execution_id": "EX-XXXXXXXXXXXXX",
    "node_id": "ND-ANALYZERXXXXX",
    "data": {
      "analysis_results": {
        "data_quality_score": 92.5,
        "completeness": {
          "total_fields": 20,
          "complete_fields": 18,
          "missing_fields": ["phone", "secondary_email"]
        },
        "statistics": {
          "total_records": 1000,
          "valid_records": 925,
          "invalid_records": 75,
          "duplicate_records": 12
        },
        "quality_issues": [
          {
            "type": "missing_value",
            "field": "phone",
            "count": 45,
            "percentage": 4.5
          },
          {
            "type": "invalid_format",
            "field": "email",
            "count": 30,
            "percentage": 3.0
          }
        ],
        "recommendations": [
          "Implement phone number validation",
          "Add email format validation",
          "Consider data enrichment for missing values"
        ]
      },
      "performance_metrics": {
        "processing_time_ms": 15000,
        "memory_usage_mb": 45,
        "cpu_usage_percent": 25
      }
    },
    "data_type": "json",
    "size_bytes": 4096,
    "success": true,
    "error_message": null,
    "checksum": "sha256:456def789abc...",
    "execution_duration_ms": 15000,
    "metadata": {
      "output_format": "detailed_analysis",
      "analysis_version": "2.1.0",
      "generated_at": "2025-01-01T00:03:45.000Z",
      "node_configuration": {
        "quality_threshold": 0.8,
        "include_recommendations": true,
        "detailed_statistics": true
      }
    }
  },
  "message": "Retrieved successfully",
  "correlation_id": "uuid"
}
```

## Data Model

### Temel Alanlar
- `id`: Execution output ID (EO-XXXXXXXXXXXXX)
- `execution_id`: İlişkili execution ID
- `node_id`: İlişkili node ID
- `data`: Çıktı verisi (JSON format)
- `data_type`: Veri tipi (json, text, binary)
- `size_bytes`: Veri boyutu
- `success`: İşlem başarı durumu
- `error_message`: Hata mesajı (varsa)
- `checksum`: Veri kontrolsüm değeri

### Performans Alanları
- `execution_duration_ms`: İşlem süresi (milisaniye)
- `created_at`: Çıktı oluşturulma zamanı

### Veri Tipleri
- **json**: Yapılandırılmış JSON verisi
- **text**: Plain text verisi
- **binary**: Binary/dosya verisi

### Success/Error Handling
- `success: true`: İşlem başarılı, `data` alanında sonuç
- `success: false`: İşlem başarısız, `error_message` alanında hata detayı

## Typical Output Patterns

### Successful Processing Output
```json
{
  "data": {
    "result": {
      "processed_items": 1000,
      "successful_items": 985,
      "failed_items": 15
    },
    "output_files": [
      "/results/success_records.json",
      "/results/failed_records.json"
    ],
    "summary": {
      "processing_time": 45.7,
      "throughput": "22 items/second"
    }
  },
  "success": true,
  "error_message": null
}
```

### Error Output
```json
{
  "data": {
    "partial_results": {
      "processed_before_error": 450
    },
    "error_context": {
      "failed_at_record": 451,
      "input_data": "invalid_format"
    }
  },
  "success": false,
  "error_message": "Data validation failed: Invalid date format in record 451"
}
```

## Filtre Kriterleri

### Desteklenen Filter Alanları
- `execution_id`: string - Belirli execution'ın output'ları
- `node_id`: string - Belirli node'un output'ları
- `data_type`: enum - Veri tipi
- `success`: boolean - Başarılı/başarısız output'lar
- `size_min`: integer - Minimum veri boyutu
- `size_max`: integer - Maksimum veri boyutu
- `created_at_from`: datetime - Oluşturulma tarihi (den)
- `created_at_to`: datetime - Oluşturulma tarihi (e)
- `execution_duration_min`: integer - Minimum işlem süresi (ms)
- `execution_duration_max`: integer - Maksimum işlem süresi (ms)

## Hata Durumları

### 404 Not Found
```json
{
  "error": {
    "code": "EXECUTION_OUTPUT_NOT_FOUND",
    "message": "Execution output not found",
    "details": {"execution_output_id": "EO-XXXXXXXXXXXXX"}
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
    "details": {"field": "size_min", "error": "Must be positive integer"}
  },
  "correlation_id": "uuid"
}
```
