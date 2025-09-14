# Environment Variable Endpoints Dokümantasyonu

Ortam değişkeni yönetimi için tüm CRUD işlemleri.

## Endpoint Listesi

### 1. Environment Variable Sayısını Getir
**GET** `/api/bff/envar/count`

#### Amaç
Sistemdeki toplam ortam değişkeni sayısını getirir.

#### Girdi
- Query parametresi yok
- Request body yok

#### Çıktı
```json
{
  "data": {
    "count": 45
  },
  "message": "Count retrieved",
  "correlation_id": "uuid",
  "timestamp": "2025-01-01T00:00:00.000Z"
}
```

---

### 2. Environment Variable Filtrele
**POST** `/api/bff/envar/filter`

#### Amaç
Belirli kriterlere göre ortam değişkenlerini filtreler ve sayfalama ile getirir.

#### Girdi
```json
{
  "filters": {
    "key": "DATABASE",
    "scope": "GLOBAL",
    "is_secret": true,
    "category": "database",
    "created_by": "admin"
  },
  "skip": 0,
  "limit": 25,
  "order_by_field": "created_at",
  "include_relationships": false,
  "exclude_fields": ["value"]
}
```

#### Çıktı
```json
{
  "data": {
    "items": [
      {
        "id": "EV-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "key": "DATABASE_URL",
        "scope": "GLOBAL",
        "is_secret": true,
        "category": "database",
        "description": "Primary database connection URL",
        "created_by": "admin",
        "last_modified_by": "admin",
        "usage_count": 15
      }
    ],
    "total": 8,
    "skip": 0,
    "limit": 25
  },
  "message": "Environment variables filtered",
  "correlation_id": "uuid"
}
```

---

### 3. Environment Variable Oluştur
**POST** `/api/bff/envar/`

#### Amaç
Yeni bir ortam değişkeni oluşturur.

#### Girdi
```json
{
  "key": "API_SECRET_KEY",
  "value": "sk_test_123456789abcdef",
  "scope": "WORKFLOW",
  "workflow_id": "WF-XXXXXXXXXXXXX",
  "is_secret": true,
  "category": "api",
  "description": "External API secret key",
  "metadata": {
    "expires_at": "2025-12-31T23:59:59.999Z",
    "rotation_required": true,
    "last_rotation": "2025-01-01T00:00:00.000Z"
  }
}
```

**Zorunlu Alanlar:**
- `key`: string (1-100 karakter, benzersiz scope içinde)
- `value`: string (1-5000 karakter)
- `scope`: enum (GLOBAL, WORKFLOW, EXECUTION)

**Opsiyonel Alanlar:**
- `workflow_id`: string (WORKFLOW scope için gerekli)
- `is_secret`: boolean (default: false)
- `category`: string (max 50 karakter)
- `description`: string (max 500 karakter)
- `metadata`: object (Ek bilgiler)

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "EV-XXXXXXXXXXXXX",
    "message": "Environment variable creation successful"
  },
  "message": "Environment variable created",
  "correlation_id": "uuid"
}
```

---

### 4. Environment Variable'ları Listele
**GET** `/api/bff/envar/`

#### Amaç
Sistemdeki tüm ortam değişkenlerini sayfalama ile listeler.

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
        "id": "EV-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "key": "LOG_LEVEL",
        "value": "INFO",
        "scope": "GLOBAL",
        "workflow_id": null,
        "is_secret": false,
        "category": "logging",
        "description": "Application log level",
        "created_by": "system",
        "last_modified_by": "admin",
        "usage_count": 0,
        "metadata": {
          "valid_values": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
          "default_value": "INFO"
        }
      },
      {
        "id": "EV-YYYYYYYYYYYYY",
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "key": "WORKFLOW_TIMEOUT",
        "value": "****",
        "scope": "WORKFLOW",
        "workflow_id": "WF-ZZZZZZZZZZZZZ",
        "is_secret": true,
        "category": "execution",
        "description": "Default workflow timeout in seconds",
        "created_by": "developer",
        "last_modified_by": "developer",
        "usage_count": 5,
        "metadata": {
          "data_type": "integer",
          "min_value": 30,
          "max_value": 3600
        }
      }
    ],
    "total": 45,
    "skip": 0,
    "limit": 100
  },
  "message": "Environment variables retrieved",
  "correlation_id": "uuid"
}
```

**Önemli Not:** Secret değişkenlerin `value` alanı `****` olarak maskelenir.

---

### 5. Environment Variable Detay Getir
**GET** `/api/bff/envar/{envar_id}`

#### Amaç
Belirli bir ortam değişkeninin detay bilgilerini getirir.

#### Girdi
- **Path Parameter:** `envar_id` (string) - Environment Variable ID'si

#### Çıktı
```json
{
  "data": {
    "id": "EV-XXXXXXXXXXXXX",
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:05:00.000Z",
    "key": "SMTP_PASSWORD",
    "value": "****",
    "scope": "GLOBAL",
    "workflow_id": null,
    "is_secret": true,
    "category": "email",
    "description": "SMTP server password for email notifications",
    "created_by": "admin",
    "last_modified_by": "admin",
    "usage_count": 25,
    "last_used_at": "2025-01-01T00:04:30.000Z",
    "metadata": {
      "smtp_server": "smtp.example.com",
      "smtp_port": 587,
      "encryption": "TLS",
      "last_password_change": "2024-12-01T00:00:00.000Z",
      "password_expires_at": "2025-06-01T00:00:00.000Z",
      "rotation_policy": "every_6_months"
    }
  },
  "message": "Environment variable retrieved",
  "correlation_id": "uuid"
}
```

**Önemli Not:** Secret değişkenlerin gerçek değeri API'den döndürülmez.

---

### 6. Environment Variable Güncelle
**PUT** `/api/bff/envar/{envar_id}`

#### Amaç
Mevcut bir ortam değişkenini günceller.

#### Girdi
- **Path Parameter:** `envar_id` (string) - Environment Variable ID'si
- **Request Body:**
```json
{
  "value": "new_secret_value_123",
  "description": "Güncellenmiş SMTP password",
  "category": "email-notifications",
  "metadata": {
    "smtp_server": "smtp.newprovider.com",
    "smtp_port": 465,
    "encryption": "SSL",
    "last_password_change": "2025-01-01T00:00:00.000Z",
    "password_expires_at": "2025-07-01T00:00:00.000Z",
    "rotation_policy": "every_6_months",
    "change_reason": "Security policy update"
  }
}
```

**Güncellenebilir Alanlar:**
- `value`: string
- `description`: string
- `category`: string
- `metadata`: object

**Güncellenemeyen Alanlar:**
- `key`: Değiştirilemez
- `scope`: Değiştirilemez
- `workflow_id`: Değiştirilemez
- `is_secret`: Değiştirilemez

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "EV-XXXXXXXXXXXXX",
    "message": "Environment variable update successful"
  },
  "message": "Environment variable updated",
  "correlation_id": "uuid"
}
```

---

### 7. Environment Variable Sil
**DELETE** `/api/bff/envar/{envar_id}`

#### Amaç
Bir ortam değişkenini siler.

#### Girdi
- **Path Parameter:** `envar_id` (string) - Environment Variable ID'si

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "EV-XXXXXXXXXXXXX",
    "message": "Environment variable deletion successful"
  },
  "message": "Environment variable deleted",
  "correlation_id": "uuid"
}
```

**Önemli Notlar:**
- Aktif kullanımda olan değişkenler silinmeden önce uyarı verilir
- Silme işlemi geri alınamaz
- Secret değişkenler silinirken audit log oluşturulur

## Environment Variable Kapsamları

### Scope Tipleri
- **GLOBAL**: Tüm sistem genelinde kullanılır
- **WORKFLOW**: Belirli bir workflow'a özel
- **EXECUTION**: Belirli bir execution'a özel (gelecek versiyon)

### Scope Kuralları
- **GLOBAL**: Tüm workflow'lar ve execution'lar tarafından erişilebilir
- **WORKFLOW**: Sadece belirtilen workflow_id'ye sahip işlemler tarafından erişilebilir
- Her scope içinde key benzersiz olmalıdır

## Güvenlik ve Secret Yönetimi

### Secret Değişkenler
- `is_secret: true` olan değişkenlerin değeri API'den döndürülmez
- Secret değişkenler `****` ile maskelenir
- Secret değişkenlerin güncellemesi audit log oluşturur
- Secret değişkenler encrypted olarak saklanır

### Audit Logging
Secret değişkenler için şu işlemler loglanır:
- Oluşturma
- Güncelleme
- Silme
- Erişim denemeleri

### Best Practices
- API key'ler için `is_secret: true` kullanın
- Password'lar için `is_secret: true` kullanın
- Environment-specific değerler için scope kullanın
- Metadata'da expiration bilgilerini saklayın

## Kategoriler

### Önerilen Kategori İsimleri
- `database`: Veritabanı bağlantı bilgileri
- `api`: Harici API key'leri ve secret'ları
- `email`: Email/SMTP konfigürasyonu
- `logging`: Log ayarları
- `execution`: Execution parametreleri
- `security`: Güvenlik ayarları
- `integration`: Entegrasyon ayarları

## Filtre Kriterleri

### Desteklenen Filter Alanları
- `key`: string - Key içerir
- `scope`: enum - Değişken kapsamı
- `is_secret`: boolean - Secret durumu
- `category`: string - Kategori
- `workflow_id`: string - Belirli workflow'un değişkenleri
- `created_by`: string - Oluşturan kullanıcı
- `created_at_from`: datetime - Oluşturulma tarihi (den)
- `created_at_to`: datetime - Oluşturulma tarihi (e)

### Örnek Complex Filter
```json
{
  "filters": {
    "scope": ["GLOBAL", "WORKFLOW"],
    "is_secret": false,
    "category": "execution",
    "key": "TIMEOUT",
    "created_at_from": "2025-01-01T00:00:00.000Z"
  },
  "order_by_field": "usage_count",
  "exclude_fields": ["metadata"]
}
```

## Hata Durumları

### 404 Not Found
```json
{
  "error": {
    "code": "ENVAR_NOT_FOUND",
    "message": "Environment variable not found",
    "details": {"envar_id": "EV-XXXXXXXXXXXXX"}
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
    "details": {"field": "key", "error": "Key already exists in this scope"}
  },
  "correlation_id": "uuid"
}
```

### 409 Conflict
```json
{
  "error": {
    "code": "ENVAR_IN_USE",
    "message": "Cannot delete environment variable that is currently in use",
    "details": {"envar_id": "EV-XXXXXXXXXXXXX", "usage_count": 5}
  },
  "correlation_id": "uuid"
}
```

### 403 Forbidden
```json
{
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "Insufficient permissions to access secret environment variable",
    "details": {"envar_id": "EV-XXXXXXXXXXXXX", "required_permission": "secret_read"}
  },
  "correlation_id": "uuid"
}
```

## Environment Variable Data Model

### Temel Alanlar
- `id`: Benzersiz environment variable ID'si (EV-XXXXXXXXXXXXX)
- `key`: Değişken anahtarı (scope içinde benzersiz)
- `value`: Değişken değeri (secret ise maskelenir)
- `scope`: Değişken kapsamı (GLOBAL, WORKFLOW, EXECUTION)
- `workflow_id`: İlişkili workflow (WORKFLOW scope için)

### Güvenlik Alanları
- `is_secret`: Secret değişken flag'i
- `created_by`: Oluşturan kullanıcı
- `last_modified_by`: Son güncelleyen kullanıcı

### Metadata
- `category`: Değişken kategorisi
- `description`: Açıklama
- `usage_count`: Kullanım sayısı
- `last_used_at`: Son kullanım zamanı
- `metadata`: Ek bilgiler (expiration, validation rules, etc.)

### Validation Rules
Metadata içinde saklanabilir:
- `data_type`: Veri tipi (string, integer, boolean, json)
- `min_value`/`max_value`: Sayısal değerler için
- `valid_values`: Enum değerler için
- `regex_pattern`: Format validasyonu için
- `expires_at`: Değişkenin süre dolumu
