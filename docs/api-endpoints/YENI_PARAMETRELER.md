# Yeni API Parametreleri - include_relationships ve exclude_fields

Bu doküman, tüm BFF endpoint'lerinde kullanılabilen yeni parametreleri açıklar.

## Genel Bakış

Tüm BFF API endpoint'lerinde aşağıdaki yeni parametreler eklenmiştir:

### 1. include_relationships (boolean)
- **Amaç:** İlişkili verilerin response'a dahil edilmesini kontrol eder
- **Default:** `false`
- **Kullanım:** Query parameter olarak
- **Destekleyen Endpoint'ler:** Tüm GET by ID, LIST ve FILTER endpoint'leri

### 2. exclude_fields (string)
- **Amaç:** Response'dan belirli alanların çıkarılmasını sağlar
- **Format:** Virgülle ayrılmış alan isimleri
- **Kullanım:** 
  - GET/LIST endpoint'lerinde: Query parameter olarak
  - FILTER endpoint'lerinde: Request body'de array olarak
- **Destekleyen Endpoint'ler:** Tüm GET by ID, LIST ve FILTER endpoint'leri

## Kullanım Örnekleri

### GET by ID Endpoint'leri

```bash
# Temel kullanım
GET /api/bff/{entity}/{id}

# İlişkili verilerle
GET /api/bff/{entity}/{id}?include_relationships=true

# Belirli alanları hariç tutarak
GET /api/bff/{entity}/{id}?exclude_fields=field1,field2,field3

# Her iki parametre birlikte
GET /api/bff/{entity}/{id}?include_relationships=true&exclude_fields=large_field,unused_field
```

### LIST Endpoint'leri

```bash
# Sayfalama ile
GET /api/bff/{entity}/?skip=0&limit=50

# Belirli alanları hariç tutarak
GET /api/bff/{entity}/?exclude_fields=content,input_schema,output_schema

# İlişkili verilerle
GET /api/bff/{entity}/?include_relationships=true&exclude_fields=large_fields
```

### FILTER Endpoint'leri

```json
POST /api/bff/{entity}/filter
{
  "filters": {
    "status": "ACTIVE",
    "category": "TEST"
  },
  "skip": 0,
  "limit": 100,
  "include_relationships": false,
  "exclude_fields": ["description", "content", "metadata"]
}
```

## Entity-Specific Örnekler

### Workflow Endpoint'leri

```bash
# Workflow detayı - açıklama ve status mesajı olmadan
GET /api/bff/workflows/WF-123?exclude_fields=description,status_message

# Workflow listesi - ilişkili verilerle ama büyük alanlar olmadan  
GET /api/bff/workflows/?include_relationships=true&exclude_fields=status_message
```

### Script Endpoint'leri

```bash
# Script detayı - büyük alanlar olmadan (performans için)
GET /api/bff/scripts/SC-123?exclude_fields=content,input_schema,output_schema,test_input_params,test_output_params

# Script listesi - sadece temel bilgiler
GET /api/bff/scripts/?exclude_fields=content,input_schema,output_schema
```

### Node Endpoint'leri

```bash
# Node detayı - konfigürasyon olmadan
GET /api/bff/nodes/ND-123?exclude_fields=configuration,metadata

# Node listesi - pozisyon bilgileri ile
GET /api/bff/nodes/?include_relationships=true&exclude_fields=configuration
```

### Edge Endpoint'leri

```bash
# Edge detayı - konfigürasyon olmadan
GET /api/bff/edges/ED-123?exclude_fields=configuration

# Edge listesi - ilişkili node bilgileri ile
GET /api/bff/edges/?include_relationships=true
```

### Execution Endpoint'leri

```bash
# Execution detayı - log'lar olmadan
GET /api/bff/executions/EX-123?exclude_fields=logs,detailed_status

# Execution listesi - sadece temel durum bilgisi
GET /api/bff/executions/?exclude_fields=logs,detailed_status,execution_context
```

### File Upload Endpoint'leri

```bash
# File detayı - metadata olmadan
GET /api/bff/files/FU-123?exclude_fields=metadata,file_content

# File listesi - temel bilgiler
GET /api/bff/files/?exclude_fields=metadata,file_content
```

### Environment Variable Endpoint'leri

```bash
# Envar detayı - değer olmadan (güvenlik için)
GET /api/bff/envar/EV-123?exclude_fields=value

# Envar listesi - sadece isimler ve tiplerr
GET /api/bff/envar/?exclude_fields=value,description
```

## Performans Optimizasyonu

### Büyük Alanları Exclude Etme

Script ve dosya endpoint'lerinde büyük içerik alanlarını hariç tutarak performansı artırabilirsiniz:

```bash
# Script içeriği olmadan
GET /api/bff/scripts/SC-123?exclude_fields=content

# Dosya içeriği olmadan  
GET /api/bff/files/FU-123?exclude_fields=file_content

# Execution log'ları olmadan
GET /api/bff/executions/EX-123?exclude_fields=logs,execution_context
```

### Network Trafiği Azaltma

Sadece ihtiyaç duyulan alanları alarak network trafiğini azaltabilirsiniz:

```bash
# Sadece temel bilgiler
GET /api/bff/workflows/?exclude_fields=description,status_message,metadata

# Listeler için minimal bilgi
GET /api/bff/scripts/?exclude_fields=content,input_schema,output_schema,test_input_params,test_output_params
```

## Hata Durumları

### Geçersiz Alan İsimleri
Exclude edilmeye çalışılan alan mevcut değilse, sessizce yok sayılır ve hata döndürülmez.

### İlişkili Veri Bulunamama
`include_relationships=true` durumunda ilişkili veri bulunamazsa, sadece temel veri döndürülür.

## Desteklenen Endpoint'ler

Aşağıdaki tüm endpoint'ler bu parametreleri destekler:

### Workflow Endpoints
- ✅ GET `/api/bff/workflows/{id}` 
- ✅ GET `/api/bff/workflows/`
- ✅ POST `/api/bff/workflows/filter`

### Script Endpoints
- ✅ GET `/api/bff/scripts/{id}`
- ✅ GET `/api/bff/scripts/`
- ✅ POST `/api/bff/scripts/filter`

### Node Endpoints
- ✅ GET `/api/bff/nodes/{id}`
- ✅ GET `/api/bff/nodes/`
- ✅ POST `/api/bff/nodes/filter`

### Edge Endpoints
- ✅ GET `/api/bff/edges/{id}`
- ✅ GET `/api/bff/edges/`
- ✅ POST `/api/bff/edges/filter`

### Execution Endpoints
- ✅ GET `/api/bff/executions/{id}`
- ✅ GET `/api/bff/executions/`
- ✅ POST `/api/bff/executions/filter`

### File Upload Endpoints
- ✅ GET `/api/bff/files/{id}`
- ✅ GET `/api/bff/files/`
- ✅ POST `/api/bff/files/filter`

### Environment Variable Endpoints
- ✅ GET `/api/bff/envar/{id}`
- ✅ GET `/api/bff/envar/`
- ✅ POST `/api/bff/envar/filter`

### Execution Input Endpoints
- ✅ GET `/api/bff/execution-inputs/{id}`
- ✅ GET `/api/bff/execution-inputs/`
- ✅ POST `/api/bff/execution-inputs/filter`

### Execution Output Endpoints
- ✅ GET `/api/bff/execution-outputs/{id}`
- ✅ GET `/api/bff/execution-outputs/`
- ✅ POST `/api/bff/execution-outputs/filter`

**TOPLAM: 27 endpoint bu yeni parametreleri destekliyor!**

## Implementation Notları

- Parametreler tüm orchestration katmanında desteklenmektedir
- Base operations sınıfında generic implementasyon mevcuttur
- Her entity-specific operations sınıfında parametreler override edilebilir
- Route seviyesinde query parameter → list dönüşümü otomatik yapılır
- Filter request'lerinde array formatında parametre alınır

Bu güncellemeler API'nin esnekliğini ve performansını önemli ölçüde artırmaktadır.
