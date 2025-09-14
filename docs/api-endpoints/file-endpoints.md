# File Upload Endpoints Dokümantasyonu

Dosya yükleme ve yönetimi için endpoint'ler.

**Not:** Bu endpoint'ler sadece dosya oluşturma ve silme işlemlerini destekler. Dosya güncelleme mevcut değildir.

## Endpoint Listesi

### 1. Dosya Sayısını Getir
**GET** `/api/bff/files/count`

#### Amaç
Sistemdeki toplam dosya sayısını getirir.

#### Girdi
- Query parametresi yok
- Request body yok

#### Çıktı
```json
{
  "data": {
    "count": 347
  },
  "message": "Files count retrieved",
  "correlation_id": "uuid",
  "timestamp": "2025-01-01T00:00:00.000Z"
}
```

---

### 2. Dosya Filtrele
**POST** `/api/bff/files/filter`

#### Amaç
Belirli kriterlere göre dosyaları filtreler ve sayfalama ile getirir.

#### Girdi
```json
{
  "filters": {
    "file_type": "image/png",
    "is_temporary": false,
    "file_size_min": 1024,
    "file_size_max": 10485760,
    "uploaded_at_from": "2025-01-01T00:00:00.000Z",
    "uploaded_at_to": "2025-01-31T23:59:59.999Z",
    "original_filename": "report"
  },
  "skip": 0,
  "limit": 25,
  "order_by_field": "uploaded_at",
  "include_relationships": false,
  "exclude_fields": ["file_path"]
}
```

#### Çıktı
```json
{
  "data": {
    "items": [
      {
        "id": "FU-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "original_filename": "report_2025.pdf",
        "stored_filename": "FU-XXXXXXXXXXXXX_report_2025.pdf",
        "file_type": "application/pdf",
        "file_size": 2097152,
        "file_hash": "sha256:abc123def456...",
        "is_temporary": false,
        "uploaded_at": "2025-01-01T00:00:00.000Z",
        "expires_at": null,
        "metadata": {
          "upload_source": "web_interface",
          "uploaded_by": "user123"
        }
      }
    ],
    "total": 15,
    "skip": 0,
    "limit": 25
  },
  "message": "Files filtered",
  "correlation_id": "uuid"
}
```

---

### 3. Dosya Yükle
**POST** `/api/bff/files/`

#### Amaç
Yeni bir dosya yükler ve sisteme kaydeder.

#### Girdi
- **Form Data:**
  - `file`: File (Zorunlu) - Yüklenecek dosya
- **Query Parameters:**
  - `is_temporary`: boolean (default: true) - Geçici dosya olarak işaretle

#### Content-Type
`multipart/form-data`

#### Örnek Request
```http
POST /api/bff/files/?is_temporary=false
Content-Type: multipart/form-data

--boundary
Content-Disposition: form-data; name="file"; filename="data.csv"
Content-Type: text/csv

name,age,city
John,25,Istanbul
Jane,30,Ankara
--boundary--
```

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "FU-XXXXXXXXXXXXX",
    "message": "File upload successful",
    "file_details": {
      "original_filename": "data.csv",
      "stored_filename": "FU-XXXXXXXXXXXXX_data.csv",
      "file_type": "text/csv",
      "file_size": 1024,
      "file_hash": "sha256:def789abc123...",
      "file_path": "/uploads/files/FU-XXXXXXXXXXXXX_data.csv",
      "is_temporary": false,
      "expires_at": null
    }
  },
  "message": "File uploaded",
  "correlation_id": "uuid"
}
```

**Önemli Notlar:**
- Maksimum dosya boyutu: 100MB
- Desteklenen dosya tipleri: Tüm MIME types
- Geçici dosyalar 24 saat sonra otomatik silinir
- Dosya hash'i duplicate kontrolü için kullanılır

---

### 4. Dosyaları Listele
**GET** `/api/bff/files/`

#### Amaç
Sistemdeki tüm dosyaları sayfalama ile listeler.

#### Girdi (Query Parametreleri)
- `skip`: integer (default: 0)
- `limit`: integer (default: 100, max: 1000)
- `order_by`: string (opsiyonel, önerilen: "uploaded_at")
- `include_relationships`: boolean (default: false)
- `exclude_fields`: string (opsiyonel)

#### Çıktı
```json
{
  "data": {
    "items": [
      {
        "id": "FU-XXXXXXXXXXXXX",
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "original_filename": "workflow_config.json",
        "stored_filename": "FU-XXXXXXXXXXXXX_workflow_config.json",
        "file_type": "application/json",
        "file_size": 512,
        "file_hash": "sha256:123abc456def...",
        "file_path": "/uploads/files/FU-XXXXXXXXXXXXX_workflow_config.json",
        "is_temporary": true,
        "uploaded_at": "2025-01-01T00:00:00.000Z",
        "expires_at": "2025-01-02T00:00:00.000Z",
        "metadata": {
          "upload_source": "api",
          "uploaded_by": "system",
          "content_preview": {
            "lines": 25,
            "encoding": "utf-8"
          }
        }
      }
    ],
    "total": 347,
    "skip": 0,
    "limit": 100
  },
  "message": "Files retrieved",
  "correlation_id": "uuid"
}
```

---

### 5. Dosya Detay Getir
**GET** `/api/bff/files/{file_id}`

#### Amaç
Belirli bir dosyanın detay bilgilerini getirir.

#### Girdi
- **Path Parameter:** `file_id` (string) - File Upload ID'si

#### Çıktı
```json
{
  "data": {
    "id": "FU-XXXXXXXXXXXXX",
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:00:00.000Z",
    "original_filename": "dataset.xlsx",
    "stored_filename": "FU-XXXXXXXXXXXXX_dataset.xlsx",
    "file_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "file_size": 5242880,
    "file_hash": "sha256:456def789abc...",
    "file_path": "/uploads/files/FU-XXXXXXXXXXXXX_dataset.xlsx",
    "is_temporary": false,
    "uploaded_at": "2025-01-01T00:00:00.000Z",
    "expires_at": null,
    "metadata": {
      "upload_source": "web_interface",
      "uploaded_by": "data_analyst",
      "upload_ip": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "file_analysis": {
        "sheets": 3,
        "total_rows": 10000,
        "total_columns": 25,
        "estimated_records": 9999
      },
      "virus_scan": {
        "scanned": true,
        "clean": true,
        "scan_date": "2025-01-01T00:00:05.000Z"
      }
    }
  },
  "message": "File retrieved",
  "correlation_id": "uuid"
}
```

---

### 6. Dosya Sil
**DELETE** `/api/bff/files/{file_id}`

#### Amaç
Bir dosyayı ve fiziksel dosyasını siler.

#### Girdi
- **Path Parameter:** `file_id` (string) - File Upload ID'si

#### Çıktı
```json
{
  "data": {
    "action_status": true,
    "record_id": "FU-XXXXXXXXXXXXX",
    "message": "File deletion successful",
    "file_operations": {
      "physical_file_deleted": true,
      "file_path": "/uploads/files/FU-XXXXXXXXXXXXX_dataset.xlsx",
      "file_size": 5242880,
      "original_filename": "dataset.xlsx",
      "warnings": null
    }
  },
  "message": "File deleted",
  "correlation_id": "uuid"
}
```

**Önemli Notlar:**
- Silme işlemi geri alınamaz
- Fiziksel dosya ve database kaydı birlikte silinir
- Referans edilen dosyalar silinmeden önce uyarı verilir

## Dosya Yönetimi

### Dosya Depolama Yapısı
```
/uploads/files/{file_id}_{original_filename}
```

Örnek:
```
/uploads/files/FU-123456789ABCDE_report.pdf
/uploads/files/FU-987654321ZYXWV_data.csv
```

### Desteklenen Dosya Tipleri
- **Dökümanlar**: PDF, DOC, DOCX, TXT, RTF
- **Spreadsheets**: XLS, XLSX, CSV, TSV
- **Resimler**: JPG, JPEG, PNG, GIF, BMP, SVG
- **Videolar**: MP4, AVI, MOV, WMV
- **Arşivler**: ZIP, RAR, 7Z, TAR, GZ
- **Kod Dosyaları**: JS, PY, JSON, XML, HTML, CSS
- **Diğer**: Tüm MIME types desteklenir

### Dosya Boyut Limitleri
- **Maksimum**: 100MB
- **Önerilen**: 10MB altı
- **Büyük dosyalar**: Chunk upload ile desteklenecek (gelecek versiyon)

### Geçici Dosya Yönetimi
- Geçici dosyalar (`is_temporary: true`) 24 saat sonra otomatik silinir
- `expires_at` alanı ile süre takibi yapılır
- Sistem düzenli olarak süresi dolan dosyaları temizler

### Güvenlik
- Dosya hash'i ile duplicate kontrolü
- Virüs tarama (opsiyonel)
- Dosya tipi doğrulama
- Boyut kontrolü
- Upload rate limiting

## Filtre Kriterleri

### Desteklenen Filter Alanları
- `file_type`: string - MIME type
- `is_temporary`: boolean - Geçici dosya durumu
- `file_size_min`: integer - Minimum dosya boyutu (byte)
- `file_size_max`: integer - Maksimum dosya boyutu (byte)
- `uploaded_at_from`: datetime - Upload tarihi (den)
- `uploaded_at_to`: datetime - Upload tarihi (e)
- `original_filename`: string - Dosya adı içerir
- `file_hash`: string - Dosya hash'i

### Örnek Advanced Filter
```json
{
  "filters": {
    "file_type": ["image/jpeg", "image/png"],
    "is_temporary": false,
    "file_size_min": 10240,
    "file_size_max": 1048576,
    "uploaded_at_from": "2025-01-01T00:00:00.000Z",
    "original_filename": "profile"
  },
  "order_by_field": "file_size",
  "limit": 50
}
```

## Hata Durumları

### 404 Not Found
```json
{
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "File not found",
    "details": {"file_id": "FU-XXXXXXXXXXXXX"}
  },
  "correlation_id": "uuid"
}
```

### 400 Bad Request
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "File validation failed",
    "details": {"error": "File size exceeds maximum limit of 100MB"}
  },
  "correlation_id": "uuid"
}
```

### 413 Payload Too Large
```json
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "File size exceeds maximum allowed limit",
    "details": {"max_size": "100MB", "received_size": "150MB"}
  },
  "correlation_id": "uuid"
}
```

### 415 Unsupported Media Type
```json
{
  "error": {
    "code": "UNSUPPORTED_FILE_TYPE",
    "message": "File type not supported",
    "details": {"file_type": "application/x-malware", "supported_types": ["image/*", "text/*", "application/pdf"]}
  },
  "correlation_id": "uuid"
}
```

### 409 Conflict
```json
{
  "error": {
    "code": "DUPLICATE_FILE",
    "message": "File with same hash already exists",
    "details": {"existing_file_id": "FU-YYYYYYYYYYYYY", "file_hash": "sha256:abc123..."}
  },
  "correlation_id": "uuid"
}
```

### 507 Insufficient Storage
```json
{
  "error": {
    "code": "STORAGE_FULL",
    "message": "Insufficient storage space",
    "details": {"available_space": "50MB", "required_space": "100MB"}
  },
  "correlation_id": "uuid"
}
```

## File Data Model

### Temel Alanlar
- `id`: Benzersiz file upload ID'si (FU-XXXXXXXXXXXXX)
- `original_filename`: Orijinal dosya adı
- `stored_filename`: Sistemde saklanan dosya adı
- `file_type`: MIME type
- `file_size`: Dosya boyutu (byte)
- `file_hash`: SHA256 hash
- `file_path`: Fiziksel dosya yolu

### Temporal Alanlar
- `uploaded_at`: Upload zamanı
- `expires_at`: Süre dolan geçici dosyalar için
- `is_temporary`: Geçici dosya flag'i

### Metadata
- `upload_source`: Upload kaynağı (web, api, system)
- `uploaded_by`: Upload eden kullanıcı
- `upload_ip`: Upload IP adresi
- `user_agent`: Browser/client bilgisi
- `file_analysis`: Dosya içerik analizi
- `virus_scan`: Virüs tarama sonuçları
