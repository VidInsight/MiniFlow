# Script Endpoints Dokümantasyonu

Script yönetimi için tüm CRUD işlemleri, dosya operasyonları ve istatistik endpoint'leri.

## Endpoint Listesi

### 1. Script Sayısını Getir
**GET** `/api/bff/scripts/count`

#### Amaç
Sistemdeki toplam script sayısını getirir.

#### Girdi
- Query parametresi yok
- Request body yok

#### Çıktı
```json
{
  "data": {
    "count": 84
  },
  "message": "Scripts count retrieved",
  "correlation_id": "uuid",
  "timestamp": "2025-01-01T00:00:00.000Z"
}
```

---

### 2. Script Filtrele
**POST** `/api/bff/scripts/filter`

#### Amaç
Belirli kriterlere göre script'leri filtreler ve sayfalama ile getirir.

#### Girdi
```json
{
  "filters": {
    "category": "automation",
    "subcategory": "data-processing",
    "author": "admin",
    "file_extension": ".py"
  },
  "skip": 0,
  "limit": 25,
  "order_by_field": "created_at",
  "include_relationships": false,
  "exclude_fields": ["content"]
}
```

#### Çıktı
```json
{
  "data": {
    "items": [
      {
        "id": "SC-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "name": "Data Processor",
        "description": "CSV data processing script",
        "version": "1.2.0",
        "category": "automation",
        "subcategory": "data-processing",
        "file_extension": ".py",
        "author": "admin",
        "input_schema": {},
        "output_schema": {},
        "test_input_params": {},
        "test_output_params": {}
      }
    ],
    "total": 12,
    "skip": 0,
    "limit": 25
  },
  "message": "Scripts filtered",
  "correlation_id": "uuid"
}
```

---

### 3. Script Oluştur
**POST** `/api/bff/scripts/`

#### Amaç
Yeni bir script oluşturur ve fiziksel dosyayı oluşturur.

#### Girdi
```json
{
  "name": "Yeni Script",
  "category": "automation",
  "content": "print('Hello World')",
  "subcategory": "test",
  "description": "Test script açıklaması",
  "version": "1.0.0",
  "author": "developer",
  "file_extension": ".py",
  "input_schema": {
    "type": "object",
    "properties": {
      "input_text": {"type": "string"}
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "result": {"type": "string"}
    }
  },
  "test_input_params": {
    "input_text": "test"
  },
  "test_output_params": {
    "result": "processed test"
  }
}
```

**Zorunlu Alanlar:**
- `name`: string (1-100 karakter, benzersiz)
- `category`: string (1-50 karakter)
- `content`: string (min 1 karakter)

**Opsiyonel Alanlar:**
- `subcategory`: string (max 50 karakter)
- `description`: string (max 1000 karakter)
- `version`: string (default: "1.0.0", max 20 karakter)
- `author`: string (max 100 karakter)
- `file_extension`: string (default: ".py", max 10 karakter)
- `input_schema`: object (JSON schema)
- `output_schema`: object (JSON schema)
- `test_input_params`: object
- `test_output_params`: object

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "SC-XXXXXXXXXXXXX",
    "message": "Script creation successful",
    "file_operations": {
      "physical_file_created": true,
      "file_path": "scripts/automation/test/Yeni Script.py",
      "file_size": 18,
      "checksum": "abc123def456"
    }
  },
  "message": "Script created",
  "correlation_id": "uuid"
}
```

---

### 4. Script'leri Listele
**GET** `/api/bff/scripts/`

#### Amaç
Sistemdeki tüm script'leri sayfalama ile listeler.

#### Girdi (Query Parametreleri)
- `skip`: integer (default: 0)
- `limit`: integer (default: 100, max: 1000)
- `order_by`: string (opsiyonel)
- `include_relationships`: boolean (default: false)
- `exclude_fields`: string (opsiyonel) - Virgülle ayrılmış

#### Çıktı
```json
{
  "data": {
    "items": [
      {
        "id": "SC-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "name": "Data Processor",
        "description": "CSV processing script",
        "version": "1.2.0",
        "category": "automation",
        "subcategory": "data-processing",
        "file_extension": ".py",
        "content": "import pandas as pd\n...",
        "author": "admin",
        "input_schema": {},
        "output_schema": {},
        "test_input_params": {},
        "test_output_params": {}
      }
    ],
    "total": 84,
    "skip": 0,
    "limit": 100
  },
  "message": "Scripts retrieved",
  "correlation_id": "uuid"
}
```

---

### 5. Script Detay Getir
**GET** `/api/bff/scripts/{script_id}`

#### Amaç
Belirli bir script'in detay bilgilerini getirir.

#### Girdi
- **Path Parameter:** `script_id` (string) - Script ID'si
- **Query Parameters:**
  - `include_relationships` (boolean, optional) - İlişkili verileri dahil et (default: false)
  - `exclude_fields` (string, optional) - Hariç tutulacak alanlar (virgülle ayrılmış)

#### Örnekler
```bash
# Temel kullanım
GET /api/bff/scripts/SC-123456789

# Büyük alanları hariç tutarak (performans için)
GET /api/bff/scripts/SC-123456789?exclude_fields=content,input_schema,output_schema

# İlişkili verilerle
GET /api/bff/scripts/SC-123456789?include_relationships=true

# Kombinasyon
GET /api/bff/scripts/SC-123456789?include_relationships=true&exclude_fields=test_input_params,test_output_params
```

#### Çıktı
```json
{
  "data": {
    "id": "SC-XXXXXXXXXXXXX",
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:00:00.000Z",
    "name": "Data Processor",
    "description": "CSV processing script",
    "version": "1.2.0",
    "category": "automation",
    "subcategory": "data-processing",
    "file_extension": ".py",
    "content": "import pandas as pd\ndef process_data(file_path):\n    return df.head()",
    "author": "admin",
    "input_schema": {
      "type": "object",
      "properties": {
        "file_path": {"type": "string"}
      }
    },
    "output_schema": {
      "type": "object",
      "properties": {
        "result": {"type": "object"}
      }
    },
    "test_input_params": {
      "file_path": "/data/test.csv"
    },
    "test_output_params": {
      "result": {"rows": 5}
    }
  },
  "message": "Script retrieved",
  "correlation_id": "uuid"
}
```

---

### 6. Script Güncelle
**PUT** `/api/bff/scripts/{script_id}`

#### Amaç
Mevcut bir script'i günceller ve fiziksel dosyayı senkronize eder.

#### Girdi
- **Path Parameter:** `script_id` (string) - Script ID'si
- **Request Body:**
```json
{
  "content": "import pandas as pd\n\ndef updated_function():\n    return 'updated'",
  "description": "Güncellenmiş açıklama",
  "version": "1.3.0",
  "author": "updated_author",
  "input_schema": {
    "type": "object",
    "properties": {
      "new_param": {"type": "string"}
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "new_result": {"type": "string"}
    }
  },
  "test_input_params": {
    "new_param": "test_value"
  },
  "test_output_params": {
    "new_result": "test_output"
  }
}
```

**Tüm Alanlar Opsiyonel:**
- `content`: string (min 1 karakter)
- `description`: string (max 1000 karakter)
- `version`: string (max 20 karakter)
- `author`: string (max 100 karakter)
- `input_schema`: object
- `output_schema`: object
- `test_input_params`: object
- `test_output_params`: object

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "SC-XXXXXXXXXXXXX",
    "message": "Script update successful",
    "file_operations": {
      "physical_file_updated": true,
      "file_path": "scripts/automation/data-processing/Data Processor.py",
      "file_size": 156,
      "checksum": "def789abc123"
    }
  },
  "message": "Script updated",
  "correlation_id": "uuid"
}
```

---

### 7. Script Sil
**DELETE** `/api/bff/scripts/{script_id}`

#### Amaç
Bir script'i ve fiziksel dosyasını siler.

#### Girdi
- **Path Parameter:** `script_id` (string) - Script ID'si

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "SC-XXXXXXXXXXXXX",
    "message": "Script deletion successful",
    "file_operations": {
      "physical_file_deleted": true,
      "file_path": "scripts/automation/data-processing/Data Processor.py",
      "file_size": 156,
      "checksum": "def789abc123",
      "warnings": null
    }
  },
  "message": "Script deleted",
  "correlation_id": "uuid"
}
```

**Önemli Notlar:**
- Silme işlemi atomik olarak gerçekleşir (database ve fiziksel dosya)
- Fiziksel dosya silinemezse uyarı verilir ancak database kaydı silinir

---

### 8. Script Test İstatistikleri
**GET** `/api/bff/scripts/{script_id}/test-stats`

#### Amaç
Belirli bir script'in test istatistiklerini getirir.

#### Girdi
- **Path Parameter:** `script_id` (string) - Script ID'si

#### Çıktı
```json
{
  "data": {
    "test_status": "PASSED",
    "test_coverage": 85.5,
    "last_test_run_at": "2025-01-01T00:00:00.000Z",
    "test_results": {
      "total_tests": 15,
      "passed_tests": 14,
      "failed_tests": 1,
      "execution_time": 2.5,
      "details": {
        "test_function_1": "PASSED",
        "test_function_2": "FAILED"
      }
    }
  },
  "message": "Test Stats",
  "correlation_id": "uuid"
}
```

---

### 9. Script Performans İstatistikleri
**GET** `/api/bff/scripts/{script_id}/performance-stats`

#### Amaç
Belirli bir script'in performans istatistiklerini getirir.

#### Girdi
- **Path Parameter:** `script_id` (string) - Script ID'si

#### Çıktı
```json
{
  "data": {
    "avg_execution_time": 45.7,
    "min_execution_time": 12.3,
    "max_execution_time": 89.2,
    "success_rate": 96.8,
    "total_executions": 1250,
    "performance_metrics": {
      "memory_usage": {
        "avg": "128MB",
        "peak": "256MB"
      },
      "cpu_usage": {
        "avg": "15%",
        "peak": "45%"
      }
    }
  },
  "message": "Performance Stats",
  "correlation_id": "uuid"
}
```

## Dosya İşlemleri

### Dosya Yolu Yapısı
Script'ler şu klasör yapısında saklanır:
```
scripts/{category}/{subcategory}/{name}.{extension}
```

Örnek:
```
scripts/automation/data-processing/CSV Processor.py
scripts/utils/text-processing/Text Cleaner.js
```

### Atomik İşlemler
- **Create**: İlk database kaydı, sonra fiziksel dosya (hata durumunda rollback)
- **Update**: Content değişikliği varsa fiziksel dosya güncellenir
- **Delete**: Database kaydı silinir, sonra fiziksel dosya temizlenir

## Hata Durumları

### 404 Not Found
```json
{
  "error": {
    "code": "SCRIPT_NOT_FOUND",
    "message": "Script not found",
    "details": {"script_id": "SC-XXXXXXXXXXXXX"}
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
    "details": {"field": "content", "error": "Content is required"}
  },
  "correlation_id": "uuid"
}
```

### 500 Internal Server Error (Dosya İşlemleri)
```json
{
  "error": {
    "code": "FILE_OPERATION_ERROR",
    "message": "Failed to create physical file",
    "details": {"file_path": "scripts/test/test.py", "error": "Permission denied"}
  },
  "correlation_id": "uuid"
}
```
