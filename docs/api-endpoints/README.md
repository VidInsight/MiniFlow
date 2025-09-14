# MiniFlow BFF API Endpoints Dokümantasyonu

Bu dizin, MiniFlow BFF (Backend for Frontend) API endpoint'lerinin detaylı dokümantasyonunu içerir.

## Endpoint Kategorileri

### 1. [Workflow Endpoints](./workflow-endpoints.md)
Workflow yönetimi için endpoint'ler - CRUD işlemleri ve istatistikler

### 2. [Script Endpoints](./script-endpoints.md)
Script yönetimi için endpoint'ler - Dosya işlemleri, test ve performans istatistikleri

### 3. [Node Endpoints](./node-endpoints.md)
Workflow node yönetimi için endpoint'ler

### 4. [Edge Endpoints](./edge-endpoints.md)
Workflow edge/bağlantı yönetimi için endpoint'ler

### 5. [Execution Endpoints](./execution-endpoints.md)
Execution monitoring için endpoint'ler (Sadece okuma)

### 6. [File Upload Endpoints](./file-endpoints.md)
Dosya yükleme ve yönetimi için endpoint'ler

### 7. [Environment Variable Endpoints](./envar-endpoints.md)
Ortam değişkeni yönetimi için endpoint'ler

### 8. [Execution Input Endpoints](./execution-input-endpoints.md)
Execution girdi verilerini okuma için endpoint'ler (Sadece okuma)

### 9. [Execution Output Endpoints](./execution-output-endpoints.md)
Execution çıktı verilerini okuma için endpoint'ler (Sadece okuma)

### 10. [Yeni API Parametreleri](./YENI_PARAMETRELER.md) ⭐ **YENİ**
`include_relationships` ve `exclude_fields` parametrelerinin kullanım rehberi

## Endpoint Özetleri

### CRUD Operations Summary

| Endpoint Category | Count | Filter | Create | List | Get | Update | Delete | Special |
|------------------|-------|--------|--------|------|-----|--------|--------|---------|
| Workflows | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Stats |
| Scripts | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Test Stats, Performance Stats |
| Nodes | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| Edges | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| Executions | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | Read-only |
| Files | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | Upload/Delete only |
| Environment Variables | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| Execution Inputs | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | Read-only |
| Execution Outputs | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | Read-only |

### Endpoint Counts by Category

| Category | Total Endpoints |
|----------|----------------|
| Workflows | 8 endpoints |
| Scripts | 9 endpoints |
| Nodes | 7 endpoints |
| Edges | 7 endpoints |
| Executions | 4 endpoints |
| Files | 6 endpoints |
| Environment Variables | 7 endpoints |
| Execution Inputs | 4 endpoints |
| Execution Outputs | 4 endpoints |
| **TOTAL** | **56 endpoints** |

## Genel API Bilgileri

### Base URL
```
http://localhost:8000/api/bff
```

### Ortak Yanıt Formatı
Tüm endpoint'ler aşağıdaki standart yanıt formatını kullanır:

```json
{
  "data": {},
  "message": "İşlem mesajı",
  "correlation_id": "benzersiz-istek-id",
  "timestamp": "2025-01-01T00:00:00.000Z"
}
```

### Hata Yanıt Formatı
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Hata açıklaması",
    "details": {}
  },
  "correlation_id": "benzersiz-istek-id",
  "timestamp": "2025-01-01T00:00:00.000Z"
}
```

### ⭐ Yeni Ortak Query Parametreleri

#### GET by ID Endpoint'leri
- `include_relationships` (boolean): İlişkili verileri dahil et (default: false)
- `exclude_fields` (string): Hariç tutulacak alanlar (virgülle ayrılmış)

#### Listeleme Endpoint'leri
- `skip`: Atlanacak kayıt sayısı (default: 0)
- `limit`: Maksimum kayıt sayısı (default: 100, max: 1000)
- `order_by`: Sıralama alanı (opsiyonel)
- `include_relationships` (boolean): İlişkili verileri dahil et (default: false) ⭐
- `exclude_fields` (string): Hariç tutulacak alanlar (virgülle ayrılmış) ⭐

#### Filter Endpoint'leri
POST endpoint'leri aşağıdaki yapıda filtre parametreleri alır:
```json
{
  "filters": {"alan": "değer"},
  "skip": 0,
  "limit": 100,
  "order_by_field": "created_at",
  "include_relationships": false,
  "exclude_fields": ["field1", "field2"]
}
```

> 💡 **Performans İpucu:** Büyük alanları (content, logs, metadata) `exclude_fields` ile hariç tutarak API yanıt süresini ve network trafiğini önemli ölçüde azaltabilirsiniz.

### Yetkilendirme
Tüm BFF endpoint'ler `verify_bff_access` dependency'si ile korunmaktadır.

### Correlation ID
Her istek için benzersiz bir correlation ID oluşturulur ve loglarda izlenebilir.
