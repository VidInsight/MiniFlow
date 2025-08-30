# Monitoring Kullanım Örnekleri

## Temel Sistem İzleme

### 1. Sistem İzlemeyi Başlatma

```python
from miniflow.core.monitoring import SystemMonitor, MonitoringConfig

# Temel izleme kurulumu
config = MonitoringConfig(
    monitoring_interval=10.0,  # Her 10 saniyede bir kontrol
    memory_warning_threshold=70.0,
    memory_critical_threshold=85.0,
    cpu_warning_threshold=70.0,
    cpu_critical_threshold=85.0
)

# Monitor oluştur ve başlat
monitor = SystemMonitor(config)
await monitor.start()

# Monitor arka planda sürekli çalışacak
print(f"İzleme {monitor.get_component_count()} bileşen ile başlatıldı")
```

### 2. Sistem Metriklerini Alma

```python
from miniflow.core.monitoring import get_system_monitor_instance

# Global monitor instance'ını al
monitor = get_system_monitor_instance()

# Mevcut sistem metriklerini al
metrikler = monitor.get_system_metrics()
print(f"CPU Kullanımı: {metrikler['system_cpu_percent']}%")
print(f"Bellek Kullanımı: {metrikler['system_memory_percent']}%")
print(f"Disk Kullanımı: {metrikler['disk_usage_percent']}%")
print(f"Aktif Thread'ler: {metrikler['active_threads']}")

# İzleme çalışma süresi
calisma_suresi = monitor.get_system_uptime()
print(f"İzleme çalışma süresi: {calisma_suresi:.2f} saniye")
```

### 3. Temel Alert İşleme

```python
from miniflow.core.monitoring import AlertLevel, AlertType

monitor = get_system_monitor_instance()

# Son alert'leri al
son_alertler = monitor.alert_manager.get_recent_alerts(10)
for alert in son_alertler:
    print(f"[{alert.level.value}] {alert.message}")
    print(f"  Bileşen: {alert.component}")
    print(f"  Zaman: {alert.timestamp}")
    print(f"  Detaylar: {alert.metadata}")

# Alert özeti al
ozet = monitor.alert_manager.get_alert_summary()
print(f"Toplam alert: {len(monitor.alert_manager.alerts)}")
print(f"Kritik: {ozet.get('CRITICAL', 0)}")
print(f"Uyarılar: {ozet.get('WARNING', 0)}")
```

## Gelişmiş İzleme Kullanımı

### 4. Özel Bileşen İzleme

```python
from miniflow.core.monitoring import MonitorableComponent, ComponentMetrics


class VeritabaniBileseni(MonitorableComponent):
    def __init__(self, name: str, db_baglanti):
        super().__init__(name)
        self.db = db_baglanti
        self.baglanti_havuz_boyutu = 10

    def saglik_kontrolu(self):
        try:
            # Veritabanı bağlantısını kontrol et
            self.db.ping()

            # Bağlantı havuzunu kontrol et
            aktif_baglanti = self.db.get_active_connections()
            havuz_kullanimi = (aktif_baglanti / self.baglanti_havuz_boyutu) * 100

            # Metriklere göre sağlığı değerlendir
            if havuz_kullanimi > 90:
                return {
                    "durum": "CRITICAL",
                    "mesaj": "Veritabanı bağlantı havuzu neredeyse tükendi",
                    "detaylar": {"havuz_kullanimi": havuz_kullanimi}
                }
            elif havuz_kullanimi > 70:
                return {
                    "durum": "WARNING",
                    "mesaj": "Yüksek veritabanı bağlantı havuzu kullanımı",
                    "detaylar": {"havuz_kullanimi": havuz_kullanimi}
                }
            else:
                return {
                    "durum": "HEALTHY",
                    "mesaj": "Veritabanı normal çalışıyor",
                    "detaylar": {"havuz_kullanimi": havuz_kullanimi}
                }

        except Exception as e:
            return {
                "durum": "CRITICAL",
                "mesaj": f"Veritabanı sağlık kontrolü başarısız: {str(e)}",
                "detaylar": {"hata": str(e)}
            }


# Özel bileşeni kaydet ve kullan
db_bileseni = VeritabaniBileseni("birincil_veritabani", db_baglanti)
monitor.register_component(db_bileseni)


# Veritabanı işlemlerini izle
def veritabani_sorgusu_isle(sorgu):
    baslangic_zamanı = time.time()
    try:
        sonuc = db.execute(sorgu)
        sure = time.time() - baslangic_zamanı

        # Başarılı işlemi kaydet
        db_bileseni.record_request(sure, success=True)
        return sonuc

    except Exception as e:
        sure = time.time() - baslangic_zamanı

        # Başarısız işlemi kaydet
        db_bileseni.record_request(sure, success=False)
        raise
```

### 5. Gerçek Zamanlı Metrik Panosu

```python
import asyncio
from miniflow.core.monitoring import get_system_monitor_instance


class IzlemePanosu:
    def __init__(self):
        self.monitor = get_system_monitor_instance()
        self.calisiyor = False

    async def pano_baslat(self):
        self.calisiyor = True
        while self.calisiyor:
            await self.ekrani_guncelle()
            await asyncio.sleep(5)  # Her 5 saniyede güncelle

    async def ekrani_guncelle(self):
        # Ekranı temizle (basit versiyon)
        print("\033[2J\033[H")  # ANSI ekran temizleme

        # Sistem metriklerini göster
        metrikler = self.monitor.get_system_metrics()
        print("=== MiniFlow Sistem İzleyicisi ===")
        print(f"Zaman Damgası: {metrikler.get('timestamp', 'N/A')}")
        print(f"CPU Kullanımı: {metrikler.get('system_cpu_percent', 0):.1f}%")
        print(f"Bellek Kullanımı: {metrikler.get('system_memory_percent', 0):.1f}%")
        print(f"Disk Kullanımı: {metrikler.get('disk_usage_percent', 0):.1f}%")
        print(f"Aktif Thread'ler: {metrikler.get('active_threads', 0)}")
        print(f"Toplam Process'ler: {metrikler.get('total_processes', 0)}")

        # Bileşen sağlığını göster
        bilesenler = self.monitor.get_all_components_metrics()
        print("\n=== Bileşen Sağlığı ===")
        for isim, bilesen_metrikleri in bilesenler.items():
            durum = bilesen_metrikleri.get('component_health', 'UNKNOWN')
            print(f"{isim}: {durum}")

        # Son alert'leri göster
        alertler = self.monitor.alert_manager.get_recent_alerts(5)
        print("\n=== Son Alert'ler ===")
        if alertler:
            for alert in alertler[-5:]:  # Son 5 alert
                print(f"[{alert.level.value}] {alert.message[:50]}...")
        else:
            print("Son alert yok")

        # İzleme durumunu göster
        calisma_suresi = self.monitor.get_system_uptime()
        print(f"\nİzleme Çalışma Süresi: {calisma_suresi:.2f}s")


# Panoyu başlat
pano = IzlemePanosu()
await pano.pano_baslat()
```

## Production İzleme Senaryoları

### 6. Yüksek Yük Sistem İzleme

```python
from miniflow.core.monitoring import MonitoringConfig, SystemMonitor

# Production-grade konfigürasyon
production_config = MonitoringConfig(
    monitoring_interval=5.0,  # Daha sık kontroller

    # Production için daha sıkı eşikler
    memory_warning_threshold=60.0,
    memory_critical_threshold=75.0,
    cpu_warning_threshold=60.0,
    cpu_critical_threshold=80.0,
    disk_warning_threshold=70.0,
    disk_critical_threshold=85.0,

    # Genişletilmiş alert geçmişi
    max_alerts_history=500,
    enable_alerts=True
)


class ProductionIzlemeServisi:
    def __init__(self):
        self.monitor = SystemMonitor(production_config)
        self.performans_gecmisi = []

    async def production_izleme_baslat(self):
        # Gelişmiş hata işleme ile izlemeyi başlat
        try:
            await self.monitor.start()
        except Exception as e:
            # Dış izleme servisine logla
            await self.operasyon_ekibini_bilgilendir(
                f"Kritik: İzleme sistemi başlatılamadı: {e}"
            )
            raise

    async def performans_verisi_topla(self):
        """Analiz için performans verisi topla ve sakla"""
        while True:
            try:
                metrikler = self.monitor.get_system_metrics()
                zaman_damgasi = datetime.utcnow()

                # Performans verisi sakla
                perf_verisi = {
                    "zaman_damgasi": zaman_damgasi,
                    "cpu_kullanimi": metrikler.get('system_cpu_percent', 0),
                    "bellek_kullanimi": metrikler.get('system_memory_percent', 0),
                    "disk_kullanimi": metrikler.get('disk_usage_percent', 0),
                    "aktif_baglantilar": self.aktif_baglanti_sayisi_getir(),
                    "istek_orani": self.mevcut_istek_orani_getir()
                }

                self.performans_gecmisi.append(perf_verisi)

                # Sadece son 24 saatlik veriyi tut
                kesim_zamani = zaman_damgasi - timedelta(hours=24)
                self.performans_gecmisi = [
                    veri for veri in self.performans_gecmisi
                    if veri["zaman_damgasi"] > kesim_zamani
                ]

                # Performans trendlerini kontrol et
                await self.performans_trendlerini_analiz_et()

            except Exception as e:
                print(f"Performans verisi toplama hatası: {e}")

            await asyncio.sleep(60)  # Her dakika topla

    async def performans_trendlerini_analiz_et(self):
        """Performans trendlerini analiz et ve sorunları öngör"""
        if len(self.performans_gecmisi) < 10:
            return

        # Son verileri al
        son_veriler = self.performans_gecmisi[-10:]

        # Trendleri hesapla
        cpu_trendi = self.trend_hesapla([v['cpu_kullanimi'] for v in son_veriler])
        bellek_trendi = self.trend_hesapla([v['bellek_kullanimi'] for v in son_veriler])

        # Potansiyel sorunları öngör
        if cpu_trendi > 5:  # CPU ölçüm başına %5 artıyor
            await self.ongorucu_alert_olustur(
                "CPU kullanımı yukarı trend gösteriyor",
                {"trend": cpu_trendi, "mevcut": son_veriler[-1]['cpu_kullanimi']}
            )

        if bellek_trendi > 3:  # Bellek ölçüm başına %3 artıyor
            await self.ongorucu_alert_olustur(
                "Bellek kullanımı yukarı trend gösteriyor",
                {"trend": bellek_trendi, "mevcut": son_veriler[-1]['bellek_kullanimi']}
            )
```

### 7. Mikroservis İzleme

```python
from miniflow.core.monitoring import MonitorableComponent


class MikroservisIzleyici:
    def __init__(self, servis_adi: str):
        self.servis_adi = servis_adi
        self.bilesen = MonitorableComponent(servis_adi)
        self.monitor = get_system_monitor_instance()
        self.monitor.register_component(self.bilesen)

        # Servise özel metrikler
        self.istek_metrikleri = {
            "toplam_istekler": 0,
            "basarili_istekler": 0,
            "basarisiz_istekler": 0,
            "ortalama_yanit_suresi": 0.0,
            "min_yanit_suresi": float('inf'),
            "max_yanit_suresi": 0.0
        }

    def api_istegi_kaydet(self, endpoint: str, method: str, status_kod: int, sure: float):
        """API istek metriklerini kaydet"""
        self.istek_metrikleri["toplam_istekler"] += 1

        # Başarı/başarısızlık takibi
        if 200 <= status_kod < 400:
            self.istek_metrikleri["basarili_istekler"] += 1
            basarili = True
        else:
            self.istek_metrikleri["basarisiz_istekler"] += 1
            basarili = False

        # Yanıt süresi metriklerini güncelle
        self.istek_metrikleri["min_yanit_suresi"] = min(
            self.istek_metrikleri["min_yanit_suresi"], sure
        )
        self.istek_metrikleri["max_yanit_suresi"] = max(
            self.istek_metrikleri["max_yanit_suresi"], sure
        )

        # Kayan ortalama hesapla
        toplam_istekler = self.istek_metrikleri["toplam_istekler"]
        mevcut_ortalama = self.istek_metrikleri["ortalama_yanit_suresi"]
        self.istek_metrikleri["ortalama_yanit_suresi"] = (
                (mevcut_ortalama * (toplam_istekler - 1) + sure) / toplam_istekler
        )

        # Bileşende kaydet
        self.bilesen.record_request(sure, basarili)

        # Sorunlar için alert oluştur
        if not basarili and status_kod >= 500:
            self.hata_alerti_olustur(endpoint, method, status_kod, sure)

        if sure > 5.0:  # Yavaş istek eşiği
            self.performans_alerti_olustur(endpoint, method, sure)

    def hata_alerti_olustur(self, endpoint: str, method: str, status_kod: int, sure: float):
        """Servis hataları için alert oluştur"""
        alert = Alert(
            level=AlertLevel.WARNING if status_kod < 500 else AlertLevel.CRITICAL,
            type=AlertType.COMPONENT,
            message=f"{self.servis_adi} servisinde hata",
            component=self.servis_adi,
            metadata={
                "endpoint": endpoint,
                "method": method,
                "status_kod": status_kod,
                "yanit_suresi": sure,
                "hata_orani": self.hata_orani_getir()
            }
        )
        self.monitor.alert_manager.process_alert(alert)

    def hata_orani_getir(self) -> float:
        """Mevcut hata oranını hesapla"""
        toplam = self.istek_metrikleri["toplam_istekler"]
        if toplam == 0:
            return 0.0
        return (self.istek_metrikleri["basarisiz_istekler"] / toplam) * 100


# FastAPI uygulamasında kullanım
from fastapi import FastAPI, Request
import time

app = FastAPI()
servis_izleyici = MikroservisIzleyici("kullanici-servisi")


@app.middleware("http")
async def izleme_middleware(request: Request, call_next):
    baslangic_zamani = time.time()

    response = await call_next(request)

    sure = time.time() - baslangic_zamani
    servis_izleyici.api_istegi_kaydet(
        endpoint=request.url.path,
        method=request.method,
        status_kod=response.status_code,
        sure=sure
    )

    return response
```

## Operations Entegrasyonu

### 8. İzleme Operations Kullanımı

```python
from miniflow.app.operations.monitoring_operations import MonitoringOperations


class SistemSaglikServisi:
    def __init__(self):
        self.monitoring_ops = MonitoringOperations()

    async def kapsamli_saglik_raporu_getir(self):
        """Kapsamlı sistem sağlık raporu oluştur"""
        try:
            # Sistem metriklerini al
            sistem_metrikleri = self.monitoring_ops.get_system_metrics()

            # Bileşen sağlığını al
            bilesen_metrikleri = self.monitoring_ops.get_all_components_metrics()

            # Alert özetini al
            alert_ozeti = self.monitoring_ops.get_alert_summary()

            # İzleme durumunu al
            izleme_durumu = self.monitoring_ops.get_monitoring_status()

            # Genel sağlığı analiz et
            genel_saglik = self.genel_saglik_analiz_et(
                sistem_metrikleri, bilesen_metrikleri, alert_ozeti
            )

            return {
                "genel_saglik": genel_saglik,
                "sistem_metrikleri": sistem_metrikleri,
                "bilesenler": bilesen_metrikleri,
                "alertler": alert_ozeti,
                "izleme_durumu": izleme_durumu,
                "zaman_damgasi": datetime.utcnow().isoformat()
            }

        except Exception as e:
            # Yedek sağlık kontrolü
            return {
                "genel_saglik": "UNKNOWN",
                "hata": str(e),
                "zaman_damgasi": datetime.utcnow().isoformat()
            }

    def genel_saglik_analiz_et(self, sistem_metrikleri, bilesen_metrikleri, alert_ozeti):
        """Genel sistem sağlığını analiz et"""
        # Sistem metriklerini kontrol et
        cpu_kullanimi = sistem_metrikleri.get('system_cpu_percent', 0)
        bellek_kullanimi = sistem_metrikleri.get('system_memory_percent', 0)
        disk_kullanimi = sistem_metrikleri.get('disk_usage_percent', 0)

        # Sistem sağlık değerlendirmesi
        if cpu_kullanimi > 85 or bellek_kullanimi > 85 or disk_kullanimi > 90:
            return "CRITICAL"

        # Bileşen sağlığını kontrol et
        kritik_bilesenler = sum(
            1 for comp in bilesen_metrikleri.values()
            if comp.get('component_health') == 'CRITICAL'
        )

        if kritik_bilesenler > 0:
            return "CRITICAL"

        # Alert'leri kontrol et
        kritik_alertler = alert_ozeti.get('critical_count', 0)
        if kritik_alertler > 0:
            return "WARNING"

        uyari_bilesenleri = sum(
            1 for comp in bilesen_metrikleri.values()
            if comp.get('component_health') == 'WARNING'
        )

        if uyari_bilesenleri > 0 or cpu_kullanimi > 70 or bellek_kullanimi > 70:
            return "WARNING"

        return "HEALTHY"

    async def izleme_konfigurasyonu_guncelle(self, guncellemeler: dict):
        """İzleme konfigürasyonunu güncelle"""
        try:
            # Güncellemeleri doğrula
            self.config_guncellemelerini_dogrula(guncellemeler)

            # Güncellemeleri uygula
            guncellenmis_config = self.monitoring_ops.update_monitoring_config(guncellemeler)

            # Konfigürasyon değişikliğini logla
            print(f"İzleme konfigürasyonu güncellendi: {guncellemeler}")

            return {
                "basarili": True,
                "guncellenmis_config": guncellenmis_config,
                "mesaj": "Konfigürasyon başarıyla güncellendi"
            }

        except Exception as e:
            return {
                "basarili": False,
                "hata": str(e),
                "mesaj": "Konfigürasyon güncellemesi başarısız"
            }
```

### 9. Alert Yönetim İşlemleri
```python
class AlertYonetimiServisi:
    def __init__(self):
        self.monitoring_ops = MonitoringOperations()
    
    async def alert_kurallarini_kur(self):
        """Özel alert kurallarını kur"""
        alert_kurallari = [
            {
                "isim": "Yüksek CPU Kullanımı",
                "kosul": "cpu_kullanimi > 80",
                "seviye": "WARNING",
                "bekleme_suresi": 300  # 5 dakika
            },
            {
                "isim": "Kritik CPU Kullanımı", 
                "kosul": "cpu_kullanimi > 90",
                "seviye": "CRITICAL",
                "bekleme_suresi": 60   # 1 dakika
            },
            {
                "isim": "Yüksek Hata Oranı",
                "kosul": "hata_orani > 5",
                "seviye": "WARNING",
                "bekleme_suresi": 180  # 3 dakika
            }
        ]
        
        for kural in alert_kurallari:
            await self.alert_kurali_kaydet(kural)
    
    async def alert_is_akisi_isle(self, alert):
        """Alert'i iş akışından geçir"""
        # 1. Alert'i doğrula
        if not self.gecerli_alert_mi(alert):
            return
        
        # 2. Alert bastırılmalı mı kontrol et
        if self.alert_bastirilmali_mi(alert):
            return
        
        # 3. Alert'i ek context ile zenginleştir
        zenginlestirilmis_alert = await self.alert_zenginlestir(alert)
        
        # 4. Alert'i uygun işleyicilere yönlendir
        await self.alert_yonlendir(zenginlestirilmis_alert)
        
        # 5. Alert metriklerini güncelle
        self.alert_metriklerini_guncelle(zenginlestirilmis_alert)
    
    async def alert_zenginlestir(self, alert):
        """Alert'i ek context ile zenginleştir"""
        # Sistem context'i ekle
        sistem_metrikleri = self.monitoring_ops.get_system_metrics()
        
        # Bileşen context'i ekle
        if alert.component:
            bilesen_metrikleri = self.monitoring_ops.get_component_metrics(alert.component)
            alert.metadata['bilesen_metrikleri'] = bilesen_metrikleri
        
        # Geçmiş context'i ekle
        benzer_alertler = self.monitoring_ops.get_alerts_by_component(alert.component)
        alert.metadata['son_benzer_alertler'] = len(benzer_alertler)
        
        # Sistem yük context'i ekle
        alert.metadata['sistem_yuku'] = {
            'cpu': sistem_metrikleri.get('system_cpu_percent'),
            'bellek': sistem_metrikleri.get('system_memory_percent'),
            'zaman_damgasi': sistem_metrikleri.get('timestamp')
        }
        
        return alert
    
    async def alert_yonlendir(self, alert):
        """Alert'i uygun işleyicilere yönlendir"""
        if alert.level == AlertLevel.CRITICAL:
            # Kritik alert'ler için anında bildirim
            await self.aninda_bildirim_gonder(alert)
            await self.olay_bileti_olustur(alert)
        
        elif alert.level == AlertLevel.WARNING:
            # Uyarılar için toplu bildirim
            await self.uyari_toplumuna_ekle(alert)
        
        # Her zaman alert'i logla
        await self.alert_logla(alert)
    
    async def alert_raporu_olustur(self, zaman_araligi: str = "24h"):
        """Alert analiz raporu oluştur"""
        # Zaman aralığı için alert'leri al
        tum_alertler = self.monitoring_ops.get_all_alerts()
        
        # Zaman aralığına göre filtrele
        kesim_zamani = self.kesim_zamani_hesapla(zaman_araligi)
        aralik_alertleri = [
            alert for alert in tum_alertler
            if datetime.fromisoformat(alert['alert_timestamp']) > kesim_zamani
        ]
        
        # Alert'leri analiz et
        analiz = {
            "zaman_araligi": zaman_araligi,
            "toplam_alert": len(aralik_alertleri),
            "seviyeye_gore_alertler": self.alertleri_seviyeye_gore_grupla(aralik_alertleri),
            "bilesene_gore_alertler": self.alertleri_bilesene_gore_grupla(aralik_alertleri),
            "en_cok_alert_veren_kaynaklar": self.en_cok_alert_veren_kaynaklari_getir(aralik_alertleri),
            "alert_sikligini": self.alert_sikligini_hesapla(aralik_alertleri),
            "cozum_istatistikleri": self.cozum_istatistiklerini_hesapla(aralik_alertleri)
        }
        
        return analiz
```

## Test ve Geliştirme

### 10. Test için Mock İzleme

```python
import pytest
from unittest.mock import Mock, patch
from miniflow.core.monitoring import SystemMonitor, MonitoringConfig


class TestIzlemeEntegrasyonu:
    @pytest.fixture
    def mock_sistem_monitor(self):
        """Test için mock sistem monitörü"""
        monitor = Mock(spec=SystemMonitor)

        # Mock sistem metrikleri
        monitor.get_system_metrics.return_value = {
            "timestamp": "2023-01-01T12:00:00",
            "system_cpu_percent": 45.0,
            "system_memory_percent": 60.0,
            "disk_usage_percent": 30.0,
            "active_threads": 10,
            "total_processes": 25
        }

        # Mock bileşen metrikleri
        monitor.get_all_components_metrics.return_value = {
            "veritabani": {
                "component_health": "HEALTHY",
                "request_count": 1000,
                "error_count": 5,
                "avg_response_time": 0.05
            }
        }

        # Mock alert manager
        mock_alert_manager = Mock()
        mock_alert_manager.get_recent_alerts.return_value = []
        mock_alert_manager.alerts = []
        monitor.alert_manager = mock_alert_manager

        return monitor

    def test_saglik_kontrol_servisi(self, mock_sistem_monitor):
        """Mock izleme ile sağlık kontrol servisini test et"""
        with patch('miniflow.core.monitoring.get_system_monitor_instance',
                   return_value=mock_sistem_monitor):
            saglik_servisi = SistemSaglikServisi()
            saglik_raporu = saglik_servisi.kapsamli_saglik_raporu_getir()

            assert saglik_raporu["genel_saglik"] == "HEALTHY"
            assert saglik_raporu["sistem_metrikleri"]["system_cpu_percent"] == 45.0
            mock_sistem_monitor.get_system_metrics.assert_called_once()
```

### 11. Geliştirme İzleme Kurulumu
```python
def gelistirme_izleme_kur():
    """Geliştirme ortamı için izleme kur"""
    # Geliştirme için gevşek eşikler
    gelistirme_config = MonitoringConfig(
        monitoring_interval=30.0,  # Daha az sık kontroller
        memory_warning_threshold=80.0,
        memory_critical_threshold=90.0,
        cpu_warning_threshold=80.0,
        cpu_critical_threshold=90.0,
        max_alerts_history=50,     # Daha küçük geçmiş
        enable_alerts=True
    )
    
    # Monitor oluştur
    monitor = SystemMonitor(gelistirme_config)
    
    # Geliştirme özel bileşenleri ekle
    gelistirme_bileseni = MonitorableComponent("gelistirme_araclari")
    monitor.register_component(gelistirme_bileseni)
    
    return monitor

# Geliştirmede kullanım
if __name__ == "__main__":
    import asyncio
    
    # Geliştirme izlemeyi kur
    gelistirme_monitor = gelistirme_izleme_kur()
    
    # İzlemeyi başlat
    asyncio.run(gelistirme_monitor.start())
```

Bu örnekler MiniFlow'un kapsamlı izleme yeteneklerini, temel sistem izlemeden karmaşık production senaryolarına, özel bileşenler, alert yönetimi ve operations entegrasyonu ile göstermektedir.
