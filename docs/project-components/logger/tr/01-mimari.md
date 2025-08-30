# Logger Modül Mimarisi

## Genel Bakış
MiniFlow Logger modülü, production-grade asenkron logging sistemi sağlayan kapsamlı bir modüldür. Hem performans hem de güvenilirlik açısından kritik iş yüklerini desteklemek üzere tasarlanmıştır.

## Temel Mimari

### 1. Modül Yapısı
```
miniflow/core/logger/
├── __init__.py              # Public API exports
├── logger.py                # AsyncLogger ana sınıfı
├── registry.py              # LoggerRegistry merkezi yönetim
├── levels.py                # LogLevel enum tanımları
├── handlers/                # Log handler'ları
│   ├── console.py          # Konsol çıktısı handler'ı
│   ├── file.py             # Dosya çıktısı handler'ı
│   └── rotating_file.py    # Dönen dosya handler'ı
├── formatters/              # Log formatleyicileri
│   ├── json.py             # JSON formatleyici
│   └── plain.py            # Düz metin formatleyici
├── config.py               # Konfigürasyon modelleri
├── context.py              # Correlation ID context
└── utils.py                # Yardımcı fonksiyonlar
```

### 2. Temel Bileşenler

#### AsyncLogger (logger.py)
**Amaç**: Asenkron logging operasyonları için ana arayüz
**Algoritma Mantığı**:
```python
# Hibrit Async-Sync Deseni
class AsyncLogger:
    def info(self, message, **kwargs):  # Sync arayüz
        # 1. Sync doğrulama ve ön işleme
        # 2. Async queue'ya log record gönder
        # 3. Arka plan görev log'u işler
        # 4. Çağıran bloke olmaz
```

**Temel Özellikler**:
- **Bloklamayan Arayüz**: Çağıran thread'i bloke etmez
- **Async İşleme**: Arka planda log işleme
- **Context Yayılımı**: Correlation ID otomatik yayılım
- **Handler Yönetimi**: Çoklu handler desteği
- **Seviye Filtreleme**: Verimli seviye tabanlı filtreleme

#### LoggerRegistry (registry.py)
**Amaç**: Tüm logger instance'larının merkezi yönetimi
**Algoritma Mantığı**:
```python
# Singleton Registry Deseni
class LoggerRegistry:
    _instance = None
    _loggers = {}           # Logger önbelleği
    _configs = {}           # Konfigürasyon önbelleği
    _strategy = Strategy    # Logging stratejisi
    
    def get_or_create_logger(self, name):
        # 1. Önbellekten kontrol et
        # 2. Yoksa yeni logger oluştur
        # 3. Config ile yapılandır
        # 4. Önbelleğe kaydet
        # 5. Logger'ı döndür
```

**Tasarım Desenleri**:
- **Singleton Deseni**: Tek registry instance
- **Factory Deseni**: Logger oluşturma
- **Strateji Deseni**: Farklı logging stratejileri
- **Observer Deseni**: Config değişiklikleri bildirimi

#### Handler Sistemi (handlers/)
**Amaç**: Log çıktı hedeflerini yönet
**Handler Türleri**:

1. **ConsoleHandler**: STDOUT/STDERR çıktısı
2. **FileHandler**: Statik dosya çıktısı  
3. **RotatingFileHandler**: Boyut tabanlı döndürme

**Handler Yaşam Döngüsü**:
```python
# Handler İşleme Pipeline'ı
def emit_sync(self, record):
    # 1. Seviye filtreleme
    # 2. Record formatla
    # 3. Hedefe yaz
    # 4. Hataları nazikçe ele al
    # 5. Performans metrikleri
```

### 3. Konfigürasyon Sistemi

#### ModuleLoggerConfig
**Yapı**:
```python
@dataclass
class ModuleLoggerConfig:
    module_name: str
    level: str = "INFO"
    filename: Optional[str] = None
    max_size_mb: int = 100
    max_files: int = 5
    console_output: bool = True
    console_level: str = "ERROR"
    file_formatter: str = "json"
    console_formatter: str = "plain"
    enabled: bool = True
    tags: Set[str] = field(default_factory=set)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
```

**Konfigürasyon Stratejileri**:
- **Merkezi**: Tüm modüller için tek config
- **Modül Tabanlı**: Her modül kendi config'i
- **Hibrit**: Karışık yaklaşım
- **Özel**: Özel konfigürasyon mantığı

### 4. Async Mimarisi

#### Thread Modeli
```python
# Ana Thread (Çağıran)
logger.info("mesaj")  # Bloklamayan çağrı
    ↓
# Arka Plan Thread (İşleyici)  
async def _process_log_record():
    # 1. Record formatla
    # 2. Handler'lara gönder
    # 3. Hataları ele al
    # 4. Metrikleri güncelle
```

**Async Faydaları**:
- **Performans**: Ana thread'de I/O bloklaması yok
- **Ölçeklenebilirlik**: Yüksek hacimli logging'i idare eder
- **Güvenilirlik**: Hata izolasyonu
- **İzleme**: Performans metrikleri toplama

### 5. Context Yönetimi

#### Correlation ID Sistemi
**Amaç**: Dağıtık bileşenler arasında istek takibi
**Uygulama**:
```python
# Context Variables (asyncio.context)
correlation_id_var: ContextVar[str] = ContextVar('correlation_id')

# Otomatik Yayılım
def set_correlation_id(correlation_id: str):
    correlation_id_var.set(correlation_id)
    
def get_correlation_id() -> str:
    return correlation_id_var.get("unknown")
```

**Akış**:
1. **İstek Girişi**: Middleware'de Correlation ID ayarla
2. **Yayılım**: Async context'te otomatik
3. **Logging**: Tüm log record'larına otomatik ekleme
4. **Servisler Arası**: Header'larda Correlation ID

### 6. Performans Optimizasyonları

#### Toplu İşleme Stratejisi
```python
# Log Record Toplu İşleme
class AsyncLogger:
    def __init__(self):
        self._batch = []
        self._batch_size = 100
        self._batch_timeout = 1.0  # saniye
    
    async def _process_batch(self):
        # Birden fazla record'ı birlikte işle
        # I/O overhead'ını azalt
        # Throughput'u artır
```

#### Bellek Yönetimi
- **Dairesel Bufferlar**: Sabit bellek ayak izi
- **Tembel Yükleme**: Talep üzerine handler yükleme
- **Zayıf Referanslar**: Bellek sızıntılarını önle
- **Çöp Toplama**: Açık temizlik

### 7. Hata İşleme

#### Çok Seviyeli Hata İşleme
```python
# 1. Handler Seviyesi
def emit_sync(self, record):
    try:
        self._write_record(record)
    except Exception as e:
        self._handle_error(e, record)

# 2. Logger Seviyesi  
def _send_to_handler(self, handler, record):
    try:
        handler.emit_sync(record)
    except Exception as e:
        self._fallback_logging(e, record)

# 3. Registry Seviyesi
def handle_logger_error(self, logger_name, error):
    # Sistem geneli hata işleme
    # Yöneticileri uyar
    # Fallback mekanizmaları
```

**Hata Kurtarma**:
- **Nazik Bozulma**: Mevcut handler'larla devam et
- **Yedek Logging**: Kritik hatalar için sistem logger'ı
- **Devre Kesici**: Başarısız handler'ları geçici devre dışı bırak
- **Sağlık İzleme**: Handler sağlık durumunu takip et

### 8. Entegrasyon Noktaları

#### Uygulama Entegrasyonu

```python
# Fast API Entegrasyonu
from miniflow.core.logger import get_logger

logger = get_logger("api_service")


@app.middleware("http")
async def logging_middleware(request, call_next):
# 1. Correlation ID ayarla
# 2. İsteği logla
# 3. İsteği işle
# 4. Yanıtı logla
# 5. Context'i temizle
```

#### Operations Entegrasyonu
```python
# Operations Katman Entegrasyonu
class LoggerOperations:
    def __init__(self):
        self.registry = get_logger_registry()
        self.logger = get_logger("operations")
    
    def get_available_loggers(self):
        # Logger yönetimi için iş mantığı
        # Keşif, konfigürasyon, izleme
```

## Tasarım İlkeleri

### 1. **Endişelerin Ayrılması**
- **Logging Mantığı**: AsyncLogger
- **Konfigürasyon**: LoggerRegistry + Config modelleri
- **Çıktı**: Handler sistemi
- **Formatlama**: Formatter sistemi
- **Context**: Context yönetimi

### 2. **Genişletilebilirlik**
- **Plugin Mimarisi**: Özel handler'lar/formatter'lar
- **Strateji Deseni**: Farklı logging stratejileri
- **Hook Sistemi**: Ön/son işleme hook'ları
- **Event Sistemi**: Konfigürasyon değişiklik eventleri

### 3. **Performans Öncelikli**
- **Async Tasarım**: Bloklamayan operasyonlar
- **Tembel Yükleme**: Talep üzerine yükle
- **Verimli Filtreleme**: Erken seviye filtreleme
- **Bellek Bilinçli**: Sınırlı bellek kullanımı

### 4. **Production Hazır**
- **Hata Dayanıklılığı**: Çok seviyeli hata işleme
- **İzleme**: Yerleşik metrikler ve sağlık kontrolleri
- **Konfigürasyon**: Çalışma zamanı konfigürasyon güncellemeleri
- **Güvenlik**: Hassas veri filtreleme

### 5. **Geliştirici Deneyimi**
- **Basit API**: Sezgisel logging arayüzü
- **Zengin Context**: Otomatik context yayılımı
- **Debugging**: Kapsamlı debug bilgisi
- **Test Edilebilirlik**: Mock dostu tasarım

## Mimari Faydaları

### Performans
- **Bloklamayan**: Ana thread asla I/O'da bloke olmaz
- **Ölçeklenebilir**: Binlerce log/saniye idare eder
- **Verimli**: Minimal bellek ve CPU overhead'ı
- **Optimize**: Toplu işleme ve önbellekleme

### Güvenilirlik
- **Hata Toleranslı**: Handler hatalarında işleme devam eder
- **Veri Güvenliği**: Uygulama çökmelerinde log kaybı olmaz
- **İzleme**: Gerçek zamanlı sağlık ve performans metrikleri
- **Kurtarma**: Otomatik hata kurtarma mekanizmaları

### Sürdürülebilirlik
- **Modüler Tasarım**: Net bileşen sınırları
- **Test Edilebilir**: Kapsamlı unit ve entegrasyon testleri
- **Yapılandırılabilir**: Yeniden başlatma olmadan çalışma zamanı konfigürasyonu
- **Gözlemlenebilir**: Zengin debugging ve izleme yetenekleri

### Ölçeklenebilirlik
- **Dağıtık**: Dağıtık izleme için correlation ID
- **Yüksek Hacim**: Yüksek throughput için async işleme
- **Kaynak Verimli**: Sınırlı kaynak kullanımı
- **Bulut Dostu**: Container ve orkestrasyon dostu
