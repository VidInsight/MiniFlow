# Monitoring Modül Mimarisi

## Genel Bakış
MiniFlow Monitoring modülü, production-grade sistem izleme ve alerting sistemi sağlayan kapsamlı bir modüldür. Gerçek zamanlı sistem metrikleri, bileşen sağlık takibi, alert yönetimi ve performans izleme işlevselliği sunar.

## Temel Mimari

### 1. Modül Yapısı
```
miniflow/core/monitoring/
├── __init__.py                  # Public API exports
├── system_monitor.py            # SystemMonitor ana sınıfı
├── alert_manager.py             # Alert ve AlertManager
├── config.py                    # Konfigürasyon modelleri
├── components.py                # Bileşen izleme
├── metrics/                     # Metrik toplama
│   ├── system_metrics.py       # İşletim sistemi seviyesi metrikler
│   ├── process_metrics.py      # Process metrikleri
│   └── custom_metrics.py       # Uygulama metrikleri
└── strategies/                  # İzleme stratejileri
    ├── centralized.py          # Merkezi izleme
    ├── distributed.py          # Dağıtık izleme
    └── hybrid.py               # Hibrit yaklaşım
```

### 2. Temel Bileşenler

#### SystemMonitor (system_monitor.py)
**Amaç**: Sistem geneli izleme koordinasyonu ve merkezi kontrol
**Algoritma Mantığı**:
```python
# Gerçek Zamanlı İzleme Döngüsü
class SystemMonitor:
    async def _monitoring_loop(self):
        while self.running:
            # 1. Sistem metriklerini topla
            metrikler = await self._sistem_metriklerini_topla()
            
            # 2. Bileşen sağlığını kontrol et
            bileşen_sagligi = await self._bilesenleri_kontrol_et()
            
            # 3. Eşik değerlerini değerlendir
            alertler = self._alert_degerlendir(metrikler, bileşen_sagligi)
            
            # 4. Alert'leri işle
            await self._alert_isle(alertler)
            
            # 5. Performans istatistiklerini güncelle
            self._performans_istatistikleri_guncelle()
            
            # 6. Sonraki interval için bekle
            await asyncio.sleep(self.config.monitoring_interval)
```

**Temel Özellikler**:
- **Gerçek Zamanlı İzleme**: Sürekli sistem gözlemi
- **Alert Üretimi**: Eşik tabanlı alert oluşturma
- **Bileşen Kayıt Defteri**: Kayıtlı bileşenleri takip etme
- **Performans Takibi**: Geçmiş performans verisi
- **Sağlık Değerlendirmesi**: Genel sistem sağlık durumu

#### AlertManager (alert_manager.py)
**Amaç**: Alert yaşam döngüsü yönetimi ve alert işleme
**Alert Veri Modeli**:
```python
@dataclass
class Alert:
    level: AlertLevel          # INFO, WARNING, CRITICAL
    type: AlertType           # SYSTEM, COMPONENT, DEVICE, NETWORK
    message: str              # İnsan tarafından okunabilir açıklama
    timestamp: str            # ISO format zaman damgası
    component: str            # Kaynak bileşen
    metadata: Dict[str, Any]  # Ek context verisi

    def to_dict(self) -> Dict[str, Any]:
        # API yanıtları için serileştirme
        return {
            "alert_level": self.level.value,
            "alert_type": self.type.value,
            "alert_message": self.message,
            "alert_timestamp": self.timestamp,
            "alert_component": self.component,
            "alert_metadata": self.metadata
        }
```

**Alert İşleme Pipeline'ı**:
```python
class AlertManager:
    def alert_isle(self, alert: Alert):
        # 1. Alert yapısını doğrula
        self._alert_dogrula(alert)
        
        # 2. Alert filtrelerini uygula
        if not self._alert_islenmeli_mi(alert):
            return
        
        # 3. Duplikat/gruplama kontrolü
        mevcut = self._benzer_alert_bul(alert)
        if mevcut:
            self._alert_sayisi_guncelle(mevcut)
            return
        
        # 4. Alert'i sakla
        self._alert_sakla(alert)
        
        # 5. Bildirimleri tetikle
        self._bildirimleri_tetikle(alert)
        
        # 6. Metrikleri güncelle
        self._alert_metriklerini_guncelle(alert)
```

#### MonitoringConfig (config.py)
**Amaç**: İzleme sistemi konfigürasyon yönetimi
**Konfigürasyon Yapısı**:
```python
@dataclass
class MonitoringConfig:
    # Zamanlama Konfigürasyonu
    monitoring_interval: float = 10.0          # Kontroller arası saniye
    max_monitoring_interval: float = 30.0      # Maksimum izin verilen interval
    min_monitoring_interval: float = 5.0       # Minimum izin verilen interval
    
    # Sistem Eşikleri
    memory_warning_threshold: float = 70.0     # Bellek kullanımı % uyarı
    memory_critical_threshold: float = 85.0    # Bellek kullanımı % kritik
    cpu_warning_threshold: float = 70.0        # CPU kullanımı % uyarı
    cpu_critical_threshold: float = 85.0       # CPU kullanımı % kritik
    disk_warning_threshold: float = 80.0       # Disk kullanımı % uyarı
    disk_critical_threshold: float = 90.0      # Disk kullanımı % kritik
    
    # Alert Konfigürasyonu
    max_alerts_history: int = 100              # Maksimum saklanan alert
    enable_alerts: bool = True                 # Alert sistemi etkin/pasif
    
    def dogrula(self) -> List[str]:
        # Konfigürasyon doğrulama mantığı
        hatalar = []
        if self.memory_warning_threshold >= self.memory_critical_threshold:
            hatalar.append("Bellek uyarı eşiği kritik eşikten küçük olmalı")
        # ... ek doğrulamalar
        return hatalar
```

### 3. Metrik Toplama Sistemi

#### Sistem Metrikleri (metrics/system_metrics.py)
**Gerçek Zamanlı İşletim Sistemi Metrik Toplama**:
```python
class SystemMetricsCollector:
    def metrikleri_topla(self) -> SystemMetrics:
        return SystemMetrics(
            timestamp=datetime.utcnow().isoformat(),
            
            # CPU Metrikleri
            cpu_percent=psutil.cpu_percent(interval=1),
            cpu_count=psutil.cpu_count(),
            load_average=os.getloadavg(),
            
            # Bellek Metrikleri
            memory=psutil.virtual_memory(),
            swap=psutil.swap_memory(),
            
            # Disk Metrikleri
            disk_usage=psutil.disk_usage('/'),
            disk_io=psutil.disk_io_counters(),
            
            # Ağ Metrikleri
            network_io=psutil.net_io_counters(),
            
            # Process Metrikleri
            process_count=len(psutil.pids()),
            thread_count=threading.active_count()
        )
```

#### Bileşen Metrikleri (components.py)
**Uygulama Seviyesi Bileşen İzleme**:
```python
class MonitorableComponent:
    def __init__(self, name: str):
        self.name = name
        self.metrikler = ComponentMetrics()
        self.son_saglik_kontrolu = None
        self.durum = ComponentStatus.UNKNOWN
    
    def istek_kaydet(self, sure: float, basarili: bool):
        # İstek metriklerini takip et
        self.metrikler.istek_sayisi += 1
        if not basarili:
            self.metrikler.hata_sayisi += 1
        self.metrikler.ortalama_yanit_suresi = self._ortalama_hesapla(sure)
    
    def saglik_kontrolu(self) -> HealthStatus:
        # Bileşen özel sağlık mantığı
        bellek_kullanimi = self._bellek_kullanimi_getir()
        hata_orani = self.metrikler.hata_sayisi / max(self.metrikler.istek_sayisi, 1)
        
        if hata_orani > 0.1:  # %10 hata oranı
            return HealthStatus.CRITICAL
        elif bellek_kullanimi > 80:  # %80 bellek kullanımı
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY
```

### 4. Alert Sistemi Mimarisi

#### Alert Seviyeleri ve Türleri
```python
class AlertLevel(Enum):
    INFO = "INFO"          # Bilgilendirici
    WARNING = "WARNING"    # Dikkat gerekli
    CRITICAL = "CRITICAL"  # Acil eylem gerekli

class AlertType(Enum):
    SYSTEM = "SYSTEM"        # İşletim sistemi seviyesi alertler
    COMPONENT = "COMPONENT"  # Uygulama bileşen alertleri
    DEVICE = "DEVICE"        # Donanım cihaz alertleri
    NETWORK = "NETWORK"      # Ağ ile ilgili alertler
```

#### Alert İşleme Stratejileri
```python
# Alert İşleme için Strateji Deseni
class AlertProcessingStrategy:
    def alert_isle(self, alert: Alert) -> None:
        raise NotImplementedError

class AnindaIslemestratejisi(AlertProcessingStrategy):
    def alert_isle(self, alert: Alert):
        # Alert'i anında işle
        self._bildirim_gonder(alert)
        self._alert_logla(alert)

class TopluIslemestratejisi(AlertProcessingStrategy):
    def alert_isle(self, alert: Alert):
        # Topluya ekle, periyodik olarak işle
        self.toplum.append(alert)
        if len(self.toplum) >= self.toplum_boyutu:
            self._toplumu_isle(self.toplum)

class EsikTabanliStrateji(AlertProcessingStrategy):
    def alert_isle(self, alert: Alert):
        # Sadece ciddiyet eşiğini karşılarsa işle
        if alert.level.value >= self.min_seviye.value:
            self._yuksek_oncelik_isle(alert)
```

### 5. İzleme Stratejileri

#### Merkezi Strateji (strategies/centralized.py)
**Yaklaşım**: Tek izleme instance'ı tüm bileşenleri idare eder
```python
class MerkeziIzlemeStratejisi:
    def __init__(self, monitor: SystemMonitor):
        self.monitor = monitor
        self.bilesenler = {}
    
    def bilesen_kaydet(self, bilesen: MonitorableComponent):
        self.bilesenler[bilesen.name] = bilesen
        # Merkezi kayıt
    
    def tum_metrikleri_topla(self):
        # Tek nokta toplama
        sistem_metrikleri = self.monitor.sistem_metriklerini_topla()
        bilesen_metrikleri = {
            isim: comp.metrikleri_topla() 
            for isim, comp in self.bilesenler.items()
        }
        return {
            "sistem": sistem_metrikleri,
            "bilesenler": bilesen_metrikleri
        }
```

**Faydalar**:
- Basit konfigürasyon ve yönetim
- Merkezi alerting ve raporlama
- Verimli kaynak kullanımı
- Kolay debugging ve sorun giderme

**Dezavantajlar**:
- Tek hata noktası
- Ölçeklenebilirlik sınırlamaları
- Dağıtık sistemlerde ağ overhead'ı

#### Dağıtık Strateji (strategies/distributed.py)
**Yaklaşım**: Her bileşen kendini izler
```python
class DagitikIzlemeStratejisi:
    def __init__(self):
        self.yerel_bilesenler = {}
        self.uzak_endpointler = []
    
    def bilesen_kaydet(self, bilesen: MonitorableComponent):
        # Yerel bileşen kaydı
        self.yerel_bilesenler[bilesen.name] = bilesen
        bilesen.kendi_izleme_baslat()
    
    def dagitik_metrikleri_topla(self):
        # Birden fazla kaynaktan topla
        yerel_metrikler = self._yerel_metrikleri_topla()
        uzak_metrikler = await self._uzak_metrikleri_topla()
        return self._metrikleri_birlestir(yerel_metrikler, uzak_metrikler)
```

**Faydalar**:
- Yüksek ölçeklenebilirlik
- Hata toleransı
- Azaltılmış ağ overhead'ı
- Bağımsız bileşen yaşam döngüsü

**Dezavantajlar**:
- Karmaşık konfigürasyon
- Dağıtık durum yönetimi
- Ağ bölünmesi ele alma
- Koordinasyon karmaşıklığı

### 6. Performans ve Ölçeklenebilirlik

#### Async İzleme Döngüsü
```python
class SystemMonitor:
    async def izleme_baslat(self):
        # Birden fazla eşzamanlı izleme görevi başlat
        gorevler = [
            asyncio.create_task(self._sistem_metrikleri_dongusu()),
            asyncio.create_task(self._bilesen_saglik_dongusu()),
            asyncio.create_task(self._alert_isleme_dongusu()),
            asyncio.create_task(self._performans_takip_dongusu())
        ]
        
        try:
            await asyncio.gather(*gorevler)
        except Exception as e:
            await self._izleme_hatasi_ele_al(e)
    
    async def _sistem_metrikleri_dongusu(self):
        while self.running:
            try:
                metrikler = await self._sistem_metriklerini_async_topla()
                await self._sistem_metriklerini_isle(metrikler)
            except Exception as e:
                await self._metrik_hatasi_ele_al(e)
            
            await asyncio.sleep(self.config.monitoring_interval)
```

#### Bellek Verimli Alert Saklama
```python
class AlertManager:
    def __init__(self, max_alerts: int = 100):
        # Bellek verimliliği için dairesel buffer
        self.alertler = collections.deque(maxlen=max_alerts)
        self.alert_indeks = {}  # Hızlı arama
        self.alert_ozeti = defaultdict(int)
    
    def alert_sakla(self, alert: Alert):
        # Bellek sınırlı saklama
        if len(self.alertler) >= self.max_alerts:
            # En eski alert'i indeksten kaldır
            eski_alert = self.alertler[0]
            self._indeksten_kaldir(eski_alert)
        
        self.alertler.append(alert)
        self._indekse_ekle(alert)
        self._ozeti_guncelle(alert)
```

### 7. Entegrasyon Mimarisi

#### Operations Katman Entegrasyonu
```python
# İş mantığı entegrasyonu
class MonitoringOperations:
    def __init__(self):
        self.system_monitor = self._sistem_monitor_getir()
        self.logger = get_logger("monitoring_operations")
    
    def sistem_sagligi_getir(self) -> Dict[str, Any]:
        # Sistem sağlığı için iş mantığı
        # 1. Ham metrikleri topla
        # 2. İş kurallarını uygula
        # 3. Sağlık değerlendirmesi oluştur
        # 4. Yapılandırılmış yanıt döndür
        
    def izleme_config_guncelle(self, guncellemeler: Dict[str, Any]):
        # Config güncellemeleri için iş mantığı
        # 1. Güncellemeleri doğrula
        # 2. Değişiklikleri uygula
        # 3. Gerekirse izlemeyi yeniden başlat
        # 4. Konfigürasyon değişikliklerini logla
```

#### API Katman Entegrasyonu
```python
# FastAPI entegrasyonu
@router.get("/health")
async def sistem_sagligi_getir():
    # 1. İş mantığı sonucunu al
    saglik_verisi = monitoring_ops.sistem_sagligi_getir()
    
    # 2. API yanıtı için dönüştür
    return APIResponse(
        success=True,
        data=saglik_verisi,
        message="Sistem sağlığı alındı"
    )
```

### 8. Hata İşleme ve Kurtarma

#### Çok Seviyeli Hata İşleme
```python
class SystemMonitor:
    async def _izleme_dongusu(self):
        while self.running:
            try:
                await self._izleme_dongus()
            except KritikSistemHatasi as e:
                # Seviye 1: Kritik sistem hataları
                await self._kritik_hata_ele_al(e)
                await self._acil_durum_kapatma()
                break
            except IzlemeHatasi as e:
                # Seviye 2: İzleme özel hataları
                await self._izleme_hatasi_ele_al(e)
                await self._kurtarma_denemesi()
            except Exception as e:
                # Seviye 3: Beklenmeyen hatalar
                await self._beklenmeyen_hata_ele_al(e)
                await asyncio.sleep(self.config.hata_tekrar_interval)
    
    async def _kurtarma_denemesi(self):
        # Kurtarma stratejileri
        # 1. Başarısız bileşenleri sıfırla
        # 2. İzleme döngülerini yeniden başlat
        # 3. Bozuk durumu temizle
        # 4. Yöneticileri bilgilendir
```

#### Devre Kesici Deseni
```python
class MonitoringCircuitBreaker:
    def __init__(self, basarisizlik_esigi: int = 5, timeout: float = 60.0):
        self.basarisizlik_sayisi = 0
        self.basarisizlik_esigi = basarisizlik_esigi
        self.timeout = timeout
        self.son_basarisizlik_zamani = None
        self.durum = CircuitState.CLOSED
    
    async def kesici_ile_cagir(self, func, *args, **kwargs):
        if self.durum == CircuitState.OPEN:
            if time.time() - self.son_basarisizlik_zamani > self.timeout:
                self.durum = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError()
        
        try:
            sonuc = await func(*args, **kwargs)
            self._basari_durumunda()
            return sonuc
        except Exception as e:
            self._basarisizlik_durumunda()
            raise
```

## Kullanılan Tasarım Desenleri

### 1. **Observer Deseni**
- SystemMonitor bileşen sağlık değişikliklerini gözlemler
- AlertManager alert eventlerinde abonelere bildirim yapar
- Konfigürasyon değişiklikleri izleme döngülerine yayılır

### 2. **Strateji Deseni**
- Farklı izleme stratejileri (merkezi, dağıtık, hibrit)
- Alert işleme stratejileri (anında, toplu, eşik tabanlı)
- Metrik toplama stratejileri (çekme tabanlı, itme tabanlı)

### 3. **Factory Deseni**
- Metrik eşiklerine dayalı alert oluşturma
- Türe göre bileşen izleme instance'ları
- Platforma göre metrik toplayıcı instance'ları

### 4. **Singleton Deseni**
- SystemMonitor instance (uygulama genelinde paylaşılan)
- AlertManager instance (merkezi alert koordinasyonu)
- MonitoringConfig instance (global konfigürasyon)

### 5. **Devre Kesici Deseni**
- Kademeli hatalara karşı izleme döngüsü koruması
- Bileşen sağlık kontrolü koruması
- Dış servis bağımlılığı koruması

## Mimari Faydaları

### Performans
- **Async Operasyonlar**: Bloklamayan izleme döngüleri
- **Verimli Metrikler**: Minimal overhead veri toplama
- **Bellek Sınırlı**: Çalışma süresinden bağımsız sabit bellek ayak izi
- **Toplu İşleme**: Alertler için azaltılmış I/O overhead'ı

### Güvenilirlik
- **Hata Toleransı**: Bileşen hatalarında izlemeye devam etme
- **Kurtarma Mekanizmaları**: Otomatik hata kurtarma
- **Sağlık İzleme**: İzleme sisteminin kendisini izleme
- **Devre Kesici**: Kademeli hataları önleme

### Ölçeklenebilirlik
- **Dağıtık Mimari**: Birden fazla node'da ölçekleme
- **Bileşen Tabanlı**: Bağımsız bileşen izleme
- **Kaynak Verimli**: Minimal CPU ve bellek kullanımı
- **Yapılandırılabilir Intervallar**: İzleme sıklığını ayarlama

### Sürdürülebilirlik
- **Modüler Tasarım**: Net bileşen sınırları
- **Strateji Deseni**: Yeni izleme yaklaşımları ekleme kolaylığı
- **Konfigürasyon Odaklı**: Çalışma zamanı konfigürasyon değişiklikleri
- **Kapsamlı Loglama**: İzleme eventlerinin tam denetim izi

### Gözlemlenebilirlik
- **Kendi Kendini İzleme**: İzleme sistemi performansını izleme
- **Zengin Metrikler**: Detaylı sistem ve uygulama metrikleri
- **Alert Yönetimi**: Kapsamlı alert yaşam döngüsü
- **Sağlık Değerlendirmesi**: Genel sistem sağlık durumu
