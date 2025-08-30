# Logger Tasarım Prensipleri

## Ne Nerede ve Neden

### Neden Asenkron Logger?

#### Problem
Geleneksel synchronous logging yaklaşımları, production ortamlarında ciddi performans sorunlarına yol açar:

```python
# ❌ Sorunlu Synchronous Yaklaşım
def kullanici_istegi_isle():
    logger.info("İstek işleniyor")         # BURADA BLOKLANIR
    # Dosya I/O: 5-10ms gecikme
    # Ağ I/O: 50-100ms gecikme
    # Ana thread bekler...
    
    is_mantigi()                           # Gecikmeli çalışma
    
    logger.info("İstek tamamlandı")        # TEKRAR BLOKLANIR
```

**Sorunlar**:
- **Gecikme**: Her log 5-100ms delay
- **Throughput**: İstek/saniye dramatik düşüş
- **Kaynak İsrafı**: Thread'ler I/O'da bekliyor
- **Kullanıcı Deneyimi**: Yavaş response time'lar

#### Çözüm: Async Logger Architecture
```python
# ✅ MiniFlow Async Yaklaşımı
def kullanici_istegi_isle():
    logger.info("İstek işleniyor")         # Bloklamayan (< 1ms)
    # Log anında kuyruğa alınır
    # Ana thread devam eder
    
    is_mantigi()                           # Anında çalışma
    
    logger.info("İstek tamamlandı")        # Bloklamayan (< 1ms)

# Arka Plan: Async log işleme
async def arka_plan_log_isleyici():
    # Tüm I/O'yu asenkron olarak idare eder
    # Verimlilik için toplu işleme
    # Hata işleme ve yeniden deneme mantığı
```

### Ne Nerede: Bileşen Sorumluluk Matrisi

#### 1. AsyncLogger (miniflow/core/logger/logger.py)
**Nerede**: Ana logging arayüzü
**Ne**: Uygulama kodu ile logging sistemi arasındaki köprü
**Neden Burada**:
```python
# Tek Sorumluluk: Logging Arayüzü
class AsyncLogger:
    def info(self, message, **kwargs):
        # ✅ Kullanım kolaylığı için sync arayüz
        # ✅ Performans için async işleme
        # ✅ İzleme için context yönetimi
        
    def _process_async(self, record):
        # ✅ Arka plan işleme
        # ✅ Hata izolasyonu
        # ✅ Performans optimizasyonu
```

**Tasarım Gerekçesi**:
- **Geliştirici Deneyimi**: Geliştiricilere tanıdık sync arayüz
- **Performans**: Async işleme bloklamaz
- **Güvenilirlik**: Hata izolasyonu uygulama çökmelerini önler
- **Uyumluluk**: Mevcut kod tabanları ile çalışır

#### 2. LoggerRegistry (miniflow/core/logger/registry.py)
**Nerede**: Logger yaşam döngüsü yönetimi
**Ne**: Factory, önbellek, konfigürasyon yöneticisi
**Neden Burada**:
```python
# Merkezi Yönetim Deseni
class LoggerRegistry:
    def get_or_create_logger(self, name):
        # ✅ Yinelenen logger'ları önler
        # ✅ Konfigürasyon tutarlılığını zorlar
        # ✅ Önbellekleme ile bellek verimliliği
        # ✅ Yaşam döngüsü yönetimi
```

**Neden Singleton Deseni**:
- **Tutarlılık**: Tüm logger'lar için tek doğruluk kaynağı
- **Bellek Verimliliği**: Paylaşılan logger instance'ları
- **Konfigürasyon**: Merkezi config yönetimi
- **İzleme**: Global logger sağlık takibi

#### 3. Handler Sistemi (miniflow/core/logger/handlers/)
**Nerede**: Çıktı hedefi yönetimi
**Ne**: Dosya, konsol, ağ çıktı handler'ları
**Neden Ayrı Modüller**:
```python
# Endişelerin Ayrılması: Her handler kendi alanını bilir
class ConsoleHandler:
    # ✅ STDOUT/STDERR özellikleri
    # ✅ Renk formatlama
    # ✅ Terminal yetenekleri
    
class RotatingFileHandler:
    # ✅ Dosya sistemi operasyonları
    # ✅ Döndürme mantığı
    # ✅ Disk alanı yönetimi
    
class NetworkHandler:
    # ✅ Ağ protokolleri
    # ✅ Yeniden deneme mekanizmaları
    # ✅ Buffer yönetimi
```

**Faydalar**:
- **Modülerlik**: Bağımsız geliştirme ve test
- **Genişletilebilirlik**: Yeni handler türlerini kolayca ekleme
- **Konfigürasyon**: Handler'a özel ayarlar
- **Performans**: Her çıktı türü için optimize

### Neden Bu Tasarım Kararları?

#### 1. Context Propagation: ContextVar vs Thread-Local
**Karar**: `asyncio.ContextVar` kullanımı
**Neden Thread-Local Değil**:
```python
# ❌ Thread-Local'in Async'deki Sorunları
import threading
thread_local = threading.local()

async def handler1():
    thread_local.correlation_id = "123"
    await handler2()  # Farklı task context!

async def handler2():
    # ❌ correlation_id kayboldu! Aynı thread, farklı task
    print(thread_local.correlation_id)  # AttributeError
```

**✅ ContextVar Çözümü**:
```python
# ✅ Async Context Aware
from contextvars import ContextVar
correlation_id_var: ContextVar[str] = ContextVar('correlation_id')

async def handler1():
    correlation_id_var.set("123")
    await handler2()  # Context korundu!

async def handler2():
    # ✅ correlation_id async sınırlar boyunca mevcut
    print(correlation_id_var.get())  # "123"
```

#### 2. Sync Arayüz + Async İşleme
**Karar**: Hibrit yaklaşım
**Neden Pure Async Değil**:
```python
# ❌ Pure Async Sorunları
async def is_mantigi():
    await logger.info("mesaj")  # Garip
    # Her yerde async yayılımını zorlar
    # Mevcut kod için breaking change
    
# ❌ Async fonksiyonda her yerde sync
def sync_yardimci():
    await logger.info("mesaj")  # SyntaxError!
```

**✅ Hibrit Çözüm**:
```python
# ✅ İkisinin de en iyisi
def is_mantigi():
    logger.info("mesaj")  # Doğal, tanıdık
    # Sync ve async context'lerde çalışır
    # Breaking change yok
    # Async işlemenin performans faydaları
```

#### 3. Hata İşleme: Çok Seviyeli Strateji
**Neden Çoklu Seviye**:
```python
# Seviye 1: Handler Hata İzolasyonu
class FileHandler:
    def emit_sync(self, record):
        try:
            self._dosyaya_yaz(record)
        except PermissionError:
            # ✅ Handler'a özel kurtarma
            self._gecici_dosyaya_yedek(record)
        except DiskFullError:
            # ✅ Nazik bozulma
            self._handler_devre_disi_birak()

# Seviye 2: Logger Hata Kurtarma  
class AsyncLogger:
    def _handler_lara_gonder(self, record):
        for handler in self.handlers:
            try:
                handler.emit_sync(record)
            except Exception:
                # ✅ Diğer handler'larla devam et
                self._handler_hatasi_logla(handler, record)

# Seviye 3: Sistem Geneli Yedek
class LoggerRegistry:
    def kritik_hata_ele_al(self, hata, context):
        # ✅ Son çare logging
        # ✅ Sistem yöneticisi bildirim
        # ✅ Gerekirse acil durum kapanması
```

### Performans Tasarım Kararları

#### 1. Toplu İşleme Stratejisi
**Neden Gerekli**:
```python
# ❌ Tekil İşleme (Yüksek Overhead)
def tekil_log_isle(record):
    record_formatla(record)      # 0.1ms
    dosyaya_yaz(record)         # 5ms I/O
    diske_senkronize(record)    # 10ms I/O
    # Toplam: 15.1ms per log

# 1000 log/saniye ile: 15,100ms = 15 saniye gecikme!
```

**✅ Toplu İşleme**:
```python
def log_toplulugu_isle(records):
    formatlanmis = [record_formatla(r) for r in records]  # 10ms 100 record için
    toplu_dosyaya_yaz(formatlanmis)                       # 8ms I/O
    diske_senkronize()                                    # 10ms I/O
    # Toplam: 28ms 100 record için = 0.28ms per log

# 1000 log/saniye ile: 280ms toplam = 72x iyileştirme!
```

#### 2. Bellek Yönetimi
**Problem**: Sınırsız bellek büyümesi
**Çözüm**: Dairesel bufferlar ve backpressure
```python
# ✅ Sınırlı Bellek Tasarımı
class AsyncLogger:
    def __init__(self):
        self._queue = asyncio.Queue(maxsize=10000)  # Sınırlı
        self._batch_buffer = CircularBuffer(1000)   # Sabit boyut
        
    def info(self, message, **kwargs):
        try:
            self._queue.put_nowait(record)
        except asyncio.QueueFull:
            # ✅ Backpressure: En eskiyi düşür veya rate limiting uygula
            self._kuyruk_dolu_ele_al(record)
```

### Konfigürasyon Tasarımı

#### Neden Modüler Konfigürasyon?
**Problem**: Monolitik config zorluğu
```python
# ❌ Monolitik Konfigürasyon Sorunları
LOGGING_CONFIG = {
    "version": 1,
    "loggers": {
        "root": {...},
        "app": {...},
        "db": {...},
        "auth": {...},
        # 50+ logger konfigürasyonu...
    }
}
# Sürdürülmesi, doğrulanması ve güncellenmesi zor
```

**✅ Modüler Yaklaşım**:
```python
# Her modül kendi konfigürasyonuna sahip
class KullaniciServisi:
    def __init__(self):
        config = ModuleLoggerConfig(
            module_name="kullanici_servisi",
            level="INFO",
            tags={"kullanici", "kimlik-dogrulama"},
            custom_fields={
                "servis_versiyonu": "1.2.3",
                "takim": "auth-takim"
            }
        )
        self.logger = get_logger("kullanici_servisi", config)
```

**Faydalar**:
- **Sahiplik**: Her takım kendi logger'larını yapılandırır
- **Doğrulama**: Type-safe konfigürasyon
- **Runtime Güncellemeler**: Yeniden başlatma olmadan config değişikliği
- **Test**: Mock ve test konfigürasyonları kolay

### Güvenlik ve Gizlilik

#### 1. Hassas Veri Filtreleme
**Neden Gerekli**:
```python
# ❌ Kazara Hassas Veri Loglama
kullanici_verisi = {
    "email": "kullanici@ornek.com",
    "sifre": "gizli123",              # ❌ Hassas!
    "kredi_karti": "1234-5678-9012"  # ❌ Hassas!
}
logger.info("Kullanıcı verisi", extra={"kullanici": kullanici_verisi})
# Loglar hassas bilgi içeriyor!
```

**✅ Otomatik Filtreleme**:
```python
# Yerleşik hassas veri tespiti
class LogRecord:
    def veri_temizle(self, data):
        # ✅ Otomatik tespit ve maskeleme
        hassas_desenler = ["sifre", "token", "kredi_karti", "tc_no"]
        return hassas_alanlari_maskele(data, hassas_desenler)

# Loglardaki sonuç:
# {"kullanici": {"email": "kullanici@ornek.com", "sifre": "***", "kredi_karti": "****-****-9012"}}
```

#### 2. Denetim İzi
**Gereksinim**: Uyumluluk ve debugging
```python
# ✅ Değiştirilemez Denetim Logları
class DenetimLogger:
    def kullanici_eylemi_logla(self, kullanici_id, eylem, kaynak):
        # Kurcalamaya karşı dayanıklı loglama
        record = {
            "zaman_damgasi": utc_simdi(),
            "kullanici_id": kullanici_id,
            "eylem": eylem,
            "kaynak": kaynak,
            "checksum": checksum_hesapla(...)  # Bütünlük kontrolü
        }
        self.denetim_handler.emit(record)
```

### Entegrasyon Tasarımı

#### Neden Operations Katmanı?
**Problem**: İş mantığı ve teknik logging karışımı
```python
# ❌ Karışık Endişeler
def kullanici_olustur(kullanici_verisi):
    # İş mantığı teknik logging ile karışık
    logger.debug("Kullanıcı oluşturma başlatılıyor")
    kullanici_verisi_dogrula(kullanici_verisi)
    logger.debug("Doğrulama tamamlandı")
    kullanici = veritabanina_kaydet(kullanici_verisi)
    logger.info(f"Kullanıcı {kullanici.id} oluşturuldu")
    hosgeldin_emaili_gonder(kullanici)
    logger.debug("Hoşgeldin emaili gönderildi")
    return kullanici
```

**✅ Operations ile Ayrılım**:
```python
# İş Operasyon Katmanı
class KullaniciOperations:
    def kullanici_olustur(self, kullanici_verisi):
        self.logger.info("Kullanıcı oluşturma başlatıldı", extra={"email": kullanici_verisi.email})
        
        try:
            kullanici = self.kullanici_servisi.kullanici_olustur(kullanici_verisi)
            self.logger.info("Kullanıcı başarıyla oluşturuldu", extra={"kullanici_id": kullanici.id})
            return kullanici
        except ValidationError as e:
            self.logger.warning("Kullanıcı oluşturma başarısız - doğrulama", extra={"hatalar": e.hatalar})
            raise
        except Exception as e:
            self.logger.error("Kullanıcı oluşturma başarısız - sistem hatası", exc_info=True)
            raise

# Saf İş Mantığı
class KullaniciServisi:
    def kullanici_olustur(self, kullanici_verisi):
        # ✅ Sadece iş mantığına odaklan
        kullanici_verisi_dogrula(kullanici_verisi)
        kullanici = veritabanina_kaydet(kullanici_verisi)
        hosgeldin_emaili_gonder(kullanici)
        return kullanici
```

### İzleme ve Gözlemlenebilirlik

#### Yerleşik Metrikler
**Neden Gerekli**: Production logger'ının kendisi izlenmeli
```python
# ✅ Kendi Kendini İzleyen Logger
class AsyncLogger:
    def __init__(self):
        self.metrikler = {
            "islenen_loglar": 0,
            "dusurlen_loglar": 0,
            "ortalama_isleme_zamani": 0,
            "handler_hatalari": defaultdict(int),
            "kuyruk_boyutu": 0
        }
    
    def saglik_durumu_getir(self):
        return {
            "durum": "saglikli" if self.metrikler["dusurlen_loglar"] < 100 else "bozulmus",
            "metrikler": self.metrikler,
            "handler_durumlari": [h.durum_getir() for h in self.handlers]
        }
```

### Geleceğe Hazırlık

#### Genişletilebilirlik Noktaları
**Değişim için Tasarım**:
```python
# ✅ Plugin Mimarisi
class LoggerRegistry:
    def formatter_kaydet(self, isim, formatter_class):
        # Özel formatter'lar
        
    def handler_kaydet(self, isim, handler_class):
        # Özel handler'lar
        
    def filtre_kaydet(self, isim, filtre_class):
        # Özel filtreler
        
    def strateji_kaydet(self, isim, strateji_class):
        # Özel logging stratejileri
```

**Hook Sistemi**:
```python
# ✅ Ön/Son İşleme Hook'ları
class AsyncLogger:
    def on_log_hook_ekle(self, hook_func):
        # İşlemeden önce record'ları değiştir
        
    def post_log_hook_ekle(self, hook_func):
        # Loglamadan sonra eylemler (bildirimler, vb.)
```

## Sonuç

MiniFlow Logger tasarımı, modern production sistemlerin gereksinimlerini karşılamak için dikkatli bir şekilde planlanmış mimari prensiplere dayanır:

1. **Performans Öncelikli**: Async tasarım ile bloklamayan operasyonlar
2. **Geliştirici Deneyimi**: Tanıdık sync arayüz
3. **Production Hazır**: Kapsamlı hata işleme ve izleme
4. **Ölçeklenebilir**: Modüler tasarım ve verimli kaynak kullanımı
5. **Sürdürülebilir**: Net endişe ayrılımı
6. **Genişletilebilir**: Plugin mimarisi ve hook sistemi
7. **Güvenli**: Yerleşik hassas veri koruması
8. **Gözlemlenebilir**: Zengin metrikler ve sağlık izleme

Bu prensipler, sistemi hem geliştirme hem production ortamlarında güvenilir ve performanslı hale getirir.
