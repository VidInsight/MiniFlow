# MiniFlow Trigger ve Handler Sistemi - Türkçe Dokümantasyon

## Genel Bakış

MiniFlow'da trigger sistemi, iş akışlarını farklı yöntemlerle tetiklemek için kullanılır. Sistem 3 ana trigger türünü destekler:

- **MANUAL**: Manuel tetikleme
- **WEBHOOK**: HTTP webhook tetikleme  
- **SCHEDULED**: Zamanlanmış tetikleme

## Trigger Türleri

### 1. Manual Trigger (Manuel Tetikleme)

Manuel trigger'lar, API çağrıları veya programatik olarak tetiklenir.

#### Özellikler:
- Otomatik çalışmaz
- İsteğe bağlı input verisi alabilir
- Anında çalıştırılabilir

#### Kullanım:
```bash
curl -X POST "http://127.0.0.1:8000/api/bff/triggers/{trigger_id}/execute" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_data": {
      "user_id": "user123",
      "action": "process_data"
    }
  }'
```

#### Oluşturma:
```bash
curl -X POST "http://127.0.0.1:8000/api/bff/triggers/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Manuel İşlem",
    "description": "Manuel tetiklenen iş akışı",
    "workflow_id": "WF-123456789",
    "trigger_type": "MANUAL",
    "config": {},
    "status": "ACTIVE"
  }'
```

### 2. Webhook Trigger (Webhook Tetikleme)

Webhook trigger'lar, HTTP istekleri ile tetiklenir.

#### Özellikler:
- HTTP endpoint'i sağlar
- Signature doğrulama destekler
- JSON payload alabilir
- Güvenlik için secret key kullanabilir

#### Kullanım:
```bash
curl -X POST "http://127.0.0.1:8000/api/bff/triggers/webhook/{webhook_id}" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: sha256=signature" \
  -d '{
    "event": "user_created",
    "user_id": "user123",
    "email": "user@example.com"
  }'
```

#### Oluşturma:
```bash
curl -X POST "http://127.0.0.1:8000/api/bff/triggers/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Webhook İşlem",
    "description": "Webhook ile tetiklenen iş akışı",
    "workflow_id": "WF-123456789",
    "trigger_type": "WEBHOOK",
    "config": {
      "webhook_id": "webhook-123",
      "secret": "your-secret-key",
      "content_type": "application/json",
      "signature_validation": true
    },
    "status": "ACTIVE"
  }'
```

#### Signature Doğrulama:
Webhook güvenliği için HMAC-SHA256 signature doğrulama:
```python
import hmac
import hashlib
import json

def create_signature(payload, secret):
    payload_bytes = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"
```

### 3. Scheduled Trigger (Zamanlanmış Tetikleme)

Scheduled trigger'lar, belirli zamanlarda otomatik olarak çalışır.

#### Özellikler:
- Cron expression desteği
- Interval (saniye) desteği
- Timezone desteği
- Otomatik çalışma

#### Cron Expression Örnekleri:
- `"0 9 * * *"` - Her gün saat 09:00
- `"0 */2 * * *"` - Her 2 saatte bir
- `"0 0 * * 1"` - Her Pazartesi saat 00:00
- `"0 0 1 * *"` - Her ayın 1'inde saat 00:00

#### Oluşturma:
```bash
curl -X POST "http://127.0.0.1:8000/api/bff/triggers/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Günlük Rapor",
    "description": "Her gün saat 09:00 çalışan rapor",
    "workflow_id": "WF-123456789",
    "trigger_type": "SCHEDULED",
    "config": {
      "cron": "0 9 * * *",
      "timezone": "Europe/Istanbul"
    },
    "status": "ACTIVE"
  }'
```

#### Interval ile Oluşturma:
```bash
curl -X POST "http://127.0.0.1:8000/api/bff/triggers/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Saatlik Kontrol",
    "description": "Her saat çalışan kontrol",
    "workflow_id": "WF-123456789",
    "trigger_type": "SCHEDULED",
    "config": {
      "interval_seconds": 3600,
      "timezone": "UTC"
    },
    "status": "ACTIVE"
  }'
```

## Handler Sistemi

### BaseTriggerHandler

Tüm trigger handler'ların temel sınıfıdır.

#### Ana Metodlar:
- `start()`: Handler'ı başlatır
- `stop()`: Handler'ı durdurur
- `execute_workflow()`: İş akışını çalıştırır
- `get_trigger_type()`: Trigger türünü döndürür

### Handler Türleri

#### 1. ManualTriggerHandler
- Manuel tetikleme için
- `trigger_manually()` metodu ile çalıştırılır

#### 2. WebhookTriggerHandler
- Webhook tetikleme için
- `handle_webhook()` metodu ile çalıştırılır
- Signature doğrulama yapar

#### 3. ScheduledTriggerHandler
- Zamanlanmış tetikleme için
- Cron veya interval ile çalışır
- Background task olarak çalışır

## Trigger Manager

### TriggerManager Sınıfı

Tüm trigger'ları yöneten merkezi sistem.

#### Ana Metodlar:
- `start()`: Tüm aktif trigger'ları başlatır
- `stop()`: Tüm trigger'ları durdurur
- `reload_trigger()`: Belirli bir trigger'ı yeniden yükler
- `trigger_manual()`: Manuel trigger çalıştırır
- `handle_webhook()`: Webhook isteğini işler

#### Kullanım:
```python
from miniflow.triggers.manager import TriggerManager

# TriggerManager'ı başlat
trigger_manager = TriggerManager(database_orchestrator)
await trigger_manager.start()

# Manuel trigger çalıştır
result = await trigger_manager.trigger_manual("TR-123", {"data": "test"})

# Webhook işle
result = await trigger_manager.handle_webhook("webhook-123", payload, headers)
```

## Input Mapping

Trigger'lar, gelen veriyi iş akışına uygun formata dönüştürebilir.

### Örnek:
```json
{
  "input_mapping": {
    "user_id": "payload.user.id",
    "email": "payload.user.email",
    "action": "event_type",
    "timestamp": "2025-09-17T12:00:00Z"
  }
}
```

### Nested Value Erişimi:
- `"payload.user.id"` → `payload["user"]["id"]`
- `"headers.authorization"` → `headers["authorization"]`

## API Endpoint'leri

### Trigger Yönetimi:
- `GET /api/bff/triggers/` - Tüm trigger'ları listele
- `POST /api/bff/triggers/` - Yeni trigger oluştur
- `GET /api/bff/triggers/{trigger_id}` - Trigger detayı
- `PUT /api/bff/triggers/{trigger_id}` - Trigger güncelle
- `DELETE /api/bff/triggers/{trigger_id}` - Trigger sil

### Trigger Çalıştırma:
- `POST /api/bff/triggers/{trigger_id}/execute` - Manuel trigger çalıştır
- `POST /api/bff/triggers/webhook/{webhook_id}` - Webhook tetikle

### Trigger Durumu:
- `GET /api/bff/triggers/{trigger_id}/status` - Trigger durumu
- `POST /api/bff/triggers/{trigger_id}/activate` - Trigger aktif et
- `POST /api/bff/triggers/{trigger_id}/deactivate` - Trigger deaktif et

### Webhook Bilgileri:
- `GET /api/bff/triggers/webhooks` - Tüm webhook'ları listele
- `GET /api/bff/triggers/webhooks/{webhook_id}/info` - Webhook bilgisi
- `POST /api/bff/triggers/webhooks/{webhook_id}/validate` - Webhook doğrula

## Monitoring ve Logging

### Metrics:
- `active_triggers`: Aktif trigger sayısı
- `total_executions`: Toplam çalıştırma sayısı
- `failed_executions`: Başarısız çalıştırma sayısı
- `by_type`: Trigger türüne göre sayılar

### Logging:
- Tüm trigger işlemleri loglanır
- Execution ID ile takip edilir
- Hata durumları detaylı loglanır

## Güvenlik

### Webhook Güvenliği:
- HMAC-SHA256 signature doğrulama
- Secret key ile güvenlik
- Header validation

### Input Validation:
- JSON schema validation
- Type checking
- Sanitization

## Hata Yönetimi

### Hata Türleri:
- `ValueError`: Geçersiz parametreler
- `RuntimeError`: Trigger aktif değil
- `Exception`: Genel hatalar

### Hata İşleme:
- Tüm hatalar loglanır
- Execution durumu güncellenir
- Retry mekanizması (gelecekte)

## Örnek Kullanım Senaryoları

### 1. E-ticaret Sipariş İşleme:
```json
{
  "name": "Sipariş İşleme",
  "trigger_type": "WEBHOOK",
  "config": {
    "webhook_id": "order-webhook",
    "secret": "order-secret-key"
  },
  "input_mapping": {
    "order_id": "payload.order.id",
    "customer_email": "payload.customer.email",
    "total_amount": "payload.order.total"
  }
}
```

### 2. Günlük Rapor Oluşturma:
```json
{
  "name": "Günlük Rapor",
  "trigger_type": "SCHEDULED",
  "config": {
    "cron": "0 6 * * *",
    "timezone": "Europe/Istanbul"
  }
}
```

### 3. Manuel Veri İşleme:
```json
{
  "name": "Manuel Veri İşleme",
  "trigger_type": "MANUAL",
  "config": {}
}
```

## Troubleshooting

### Yaygın Sorunlar:

1. **Trigger çalışmıyor:**
   - Status'u ACTIVE mi kontrol et
   - Handler başlatıldı mı kontrol et
   - Log'ları kontrol et

2. **Webhook signature hatası:**
   - Secret key doğru mu kontrol et
   - Header format'ı kontrol et
   - Payload format'ı kontrol et

3. **Scheduled trigger çalışmıyor:**
   - Cron expression doğru mu kontrol et
   - Timezone ayarı kontrol et
   - Handler başlatıldı mı kontrol et

### Debug Komutları:
```bash
# Trigger durumu
curl -X GET "http://127.0.0.1:8000/api/bff/triggers/{trigger_id}/status"

# Handler durumu
curl -X GET "http://127.0.0.1:8000/api/bff/triggers/{trigger_id}/reload"

# Webhook bilgisi
curl -X GET "http://127.0.0.1:8000/api/bff/triggers/webhooks/{webhook_id}/info"
```

## Sonuç

MiniFlow trigger sistemi, farklı tetikleme yöntemleri ile iş akışlarını çalıştırmak için kapsamlı bir çözüm sunar. Manual, webhook ve scheduled trigger'lar ile esnek ve güvenli bir sistem sağlar.

Sistem, monitoring, logging ve hata yönetimi ile production-ready bir çözümdür.
