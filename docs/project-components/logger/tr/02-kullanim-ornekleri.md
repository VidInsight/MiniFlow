# Logger Kullanım Örnekleri

## Temel Kullanım

### 1. Basit Logging

```python
from miniflow.core.logger import get_logger

# Logger instance al
logger = get_logger("servisim")

# Temel logging
logger.info("Servis başarıyla başlatıldı")
logger.warning("Konfigürasyon dosyası bulunamadı, varsayılanlar kullanılıyor")
logger.error("Veritabanı bağlantısı başarısız")
logger.critical("Sistem kapanıyor")
```

### 2. Yapılandırılmış Logging ve Context

```python
logger = get_logger("kullanici_servisi")

# Ekstra context ile loglama
logger.info(
    "Kullanıcı giriş başarılı",
    extra={
        "kullanici_id": "12345",
        "ip_adresi": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "giris_yontemi": "oauth"
    }
)

# Correlation ID ile loglama
from miniflow.core.logger.context import set_correlation_id

set_correlation_id("req-2023-001")

logger.info("Kullanıcı isteği işleniyor")
# Correlation ID otomatik olarak dahil edilir
```

### 3. Hata Logging ve Exception Detayları
```python
logger = get_logger("odeme_servisi")

try:
    process_payment(tutar, kart_bilgisi)
except PaymentException as e:
    logger.error(
        "Ödeme işleme başarısız",
        extra={
            "hata_kodu": e.code,
            "tutar": tutar,
            "islem_id": e.transaction_id,
            "hata_detayları": str(e)
        },
        exc_info=True  # Stack trace dahil et
    )
except Exception as e:
    logger.critical(
        "Ödeme işlemede beklenmeyen hata",
        extra={
            "tutar": tutar,
            "hata_tipi": type(e).__name__
        },
        exc_info=True
    )
```

## Gelişmiş Kullanım

### 4. Özel Logger Konfigürasyonu

```python
from miniflow.core import get_logger_registry
from miniflow import ModuleLoggerConfig

# Özel konfigürasyon oluştur
config = ModuleLoggerConfig(
    module_name="analitik_servisi",
    level="DEBUG",
    filename="logs/analitik.log",
    max_size_mb=500,  # Analitik için büyük log dosyaları
    max_files=10,
    console_output=True,
    console_level="WARNING",
    file_formatter="json",
    console_formatter="plain",
    enabled=True,
    tags={"servis", "analitik", "veri-isleme"},
    custom_fields={
        "servis_versiyonu": "1.2.3",
        "ortam": "production",
        "veri_merkezi": "tr-west-1"
    }
)

# Konfigürasyonu kaydet
registry = get_logger_registry()
registry.register_module_config(config)

# Yapılandırılmış logger kullan
logger = get_logger("analitik_servisi")
logger.debug("Veri analizi pipeline'ı başlatılıyor")
```

### 5. Performans Kritik Logging
```python
logger = get_logger("yuksek_frekanslı_trading")

# Minimal overhead ile yüksek frekanslı loglama
def islem_isle(islem_verisi):
    # Pahalı operasyonlardan önce hızlı seviye kontrolü
    if logger.isEnabledFor("DEBUG"):
        logger.debug(
            "İşlem işleniyor",
            extra={
                "sembol": islem_verisi.sembol,
                "miktar": islem_verisi.miktar,
                "fiyat": islem_verisi.fiyat,
                "zaman_damgasi": islem_verisi.timestamp.isoformat()
            }
        )
    
    # İşlemi gerçekleştir...
    
    # Kritik olayları her zaman logla
    logger.info(
        "İşlem gerçekleştirildi",
        extra={
            "islem_id": islem_verisi.id,
            "sembol": islem_verisi.sembol,
            "kar_zarar": kar_zarar_hesapla(islem_verisi)
        }
    )
```

### 6. Çoklu Handler Konfigürasyonu

```python
from miniflow.core.logger.handlers import ConsoleHandler, RotatingFileHandler
from miniflow.core.logger.formatters import JSONFormatter, PlainTextFormatter
from miniflow.core import LogLevel

# Çoklu handler ile özel logger oluştur
logger_name = "ozel_servis"
logger = get_logger(logger_name)

# Geliştirme için konsol handler'ı
console_handler = ConsoleHandler()
console_handler.set_level(LogLevel.WARNING)
console_handler.set_formatter(PlainTextFormatter())

# Production logları için dosya handler'ı
file_handler = RotatingFileHandler(
    filename="logs/servis.log",
    max_size_bytes=100 * 1024 * 1024,  # 100MB
    backup_count=5
)
file_handler.set_level(LogLevel.INFO)
file_handler.set_formatter(JSONFormatter())

# Handler'ları ekle
logger.add_handler(console_handler)
logger.add_handler(file_handler)

# Logger'ı kullan
logger.info("Servis konfigürasyonu tamamlandı")
```

## FastAPI Entegrasyonu

### 7. İstek/Yanıt Logging Middleware

```python
from fastapi import FastAPI, Request
from miniflow.core.logger import get_logger
from miniflow.core.logger.context import set_correlation_id
import uuid
import time

app = FastAPI()
logger = get_logger("api")


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # Correlation ID oluştur
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    set_correlation_id(correlation_id)

    # İsteği logla
    start_time = time.time()
    logger.info(
        "API İsteği",
        extra={
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client_ip": request.client.host
        }
    )

    # İsteği işle
    try:
        response = await call_next(request)

        # Başarılı yanıtı logla
        process_time = time.time() - start_time
        logger.info(
            "API Yanıtı",
            extra={
                "status_code": response.status_code,
                "islem_suresi": process_time
            }
        )

        return response

    except Exception as e:
        # Hata yanıtını logla
        process_time = time.time() - start_time
        logger.error(
            "API Hatası",
            extra={
                "hata_tipi": type(e).__name__,
                "hata_mesaji": str(e),
                "islem_suresi": process_time
            },
            exc_info=True
        )
        raise
```

### 8. Endpoint Özel Logging

```python
from fastapi import APIRouter, HTTPException
from miniflow.core.logger import get_logger

router = APIRouter()
logger = get_logger("kullanici_api")


@router.post("/kullanicilar/")
async def kullanici_olustur(kullanici_verisi: UserCreate):
    logger.info(
        "Yeni kullanıcı oluşturuluyor",
        extra={
            "email": kullanici_verisi.email,
            "rol": kullanici_verisi.role
        }
    )

    try:
        kullanici = await kullanici_servisi.kullanici_olustur(kullanici_verisi)

        logger.info(
            "Kullanıcı başarıyla oluşturuldu",
            extra={
                "kullanici_id": kullanici.id,
                "email": kullanici.email
            }
        )

        return kullanici

    except UserExistsException:
        logger.warning(
            "Kullanıcı oluşturma başarısız - kullanıcı zaten mevcut",
            extra={"email": kullanici_verisi.email}
        )
        raise HTTPException(status_code=409, detail="Kullanıcı zaten mevcut")

    except Exception as e:
        logger.error(
            "Kullanıcı oluşturma beklenmeyen hata ile başarısız",
            extra={
                "email": kullanici_verisi.email,
                "hata": str(e)
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="İç sunucu hatası")
```

## İş Mantığı Entegrasyonu

### 9. Servis Katmanı Logging

```python
from miniflow.core.logger import get_logger


class OdemeServisi:
    def __init__(self):
        self.logger = get_logger("odeme_servisi")

    async def odeme_isle(self, odeme_istegi):
        self.logger.info(
            "Ödeme işleme başlatıldı",
            extra={
                "tutar": odeme_istegi.tutar,
                "para_birimi": odeme_istegi.para_birimi,
                "odeme_yontemi": odeme_istegi.yontem
            }
        )

        # Ödeme doğrula
        dogrulama_sonucu = await self._odeme_dogrula(odeme_istegi)
        if not dogrulama_sonucu.gecerli:
            self.logger.warning(
                "Ödeme doğrulama başarısız",
                extra={
                    "dogrulama_hatalari": dogrulama_sonucu.hatalar,
                    "tutar": odeme_istegi.tutar
                }
            )
            raise PaymentValidationException(dogrulama_sonucu.hatalar)

        # Ödeme sağlayıcısı ile işle
        try:
            odeme_sonucu = await self._odeme_yukle(odeme_istegi)

            self.logger.info(
                "Ödeme başarıyla işlendi",
                extra={
                    "odeme_id": odeme_sonucu.id,
                    "tutar": odeme_istegi.tutar,
                    "saglayici_referans": odeme_sonucu.saglayici_referans
                }
            )

            return odeme_sonucu

        except PaymentProviderException as e:
            self.logger.error(
                "Ödeme sağlayıcısı hatası",
                extra={
                    "saglayici": e.saglayici,
                    "hata_kodu": e.kod,
                    "tutar": odeme_istegi.tutar
                }
            )
            raise
```

### 10. Veritabanı İşlemleri Logging

```python
from miniflow.core.logger import get_logger
import time


class KullaniciRepository:
    def __init__(self):
        self.logger = get_logger("kullanici_repository")

    async def email_ile_kullanici_bul(self, email: str):
        self.logger.debug(
            "Email ile kullanıcı aranıyor",
            extra={"email": email}
        )

        start_time = time.time()
        try:
            kullanici = await self.db.kullanicilar.find_one({"email": email})
            sorgu_suresi = time.time() - start_time

            if kullanici:
                self.logger.debug(
                    "Kullanıcı bulundu",
                    extra={
                        "kullanici_id": str(kullanici["_id"]),
                        "email": email,
                        "sorgu_suresi": sorgu_suresi
                    }
                )
            else:
                self.logger.debug(
                    "Kullanıcı bulunamadı",
                    extra={
                        "email": email,
                        "sorgu_suresi": sorgu_suresi
                    }
                )

            return kullanici

        except Exception as e:
            sorgu_suresi = time.time() - start_time
            self.logger.error(
                "Veritabanı sorgusu başarısız",
                extra={
                    "email": email,
                    "sorgu_suresi": sorgu_suresi,
                    "hata": str(e)
                },
                exc_info=True
            )
            raise
```

## Test ve Geliştirme

### 11. Mock Logger'lar ile Test

```python
import pytest
from unittest.mock import Mock, patch
from miniflow.core.logger import get_logger


class TestKullaniciServisi:
    @patch('miniflow.core.logger.get_logger')
    def test_kullanici_olusturma_logging(self, mock_get_logger):
        # Mock logger kurulumu
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Servisi test et
        servis = KullaniciServisi()
        kullanici_verisi = UserCreate(email="test@ornek.com", isim="Test Kullanıcı")

        # Çalıştır
        sonuc = servis.kullanici_olustur(kullanici_verisi)

        # Logging çağrılarını doğrula
        mock_logger.info.assert_called_with(
            "Kullanıcı başarıyla oluşturuldu",
            extra={
                "kullanici_id": sonuc.id,
                "email": "test@ornek.com"
            }
        )
```

### 12. Geliştirme Debug Logging

```python
from miniflow.core.logger import get_logger
from miniflow.core import LogLevel

# Debug çıktılı geliştirme logger'ı
logger = get_logger("gelistirme")

# Geliştirme için geçici debug seviyesi ayarla
logger.set_level(LogLevel.DEBUG)


def kullanici_is_akisi_debug(kullanici_id):
    logger.debug("Kullanıcı iş akışı debug başlatılıyor", extra={"kullanici_id": kullanici_id})

    # Adım adım debugging
    kullanici = kullanici_getir(kullanici_id)
    logger.debug("Kullanıcı alındı", extra={"kullanici": kullanici.to_dict()})

    yetkiler = kullanici_yetkileri_getir(kullanici_id)
    logger.debug("Yetkiler yüklendi", extra={"yetkiler": yetkiler})

    profil = kullanici_profili_olustur(kullanici, yetkiler)
    logger.debug("Profil oluşturuldu", extra={"profil_boyutu": len(profil)})

    logger.debug("Kullanıcı iş akışı tamamlandı", extra={"kullanici_id": kullanici_id})
    return profil
```

## Production Senaryoları

### 13. Yüksek Hacimli Logging

```python
from miniflow.core.logger import get_logger
import asyncio

logger = get_logger("toplu_islemci")


async def toplu_veri_isle(toplu_veri):
    toplu_id = toplu_veri.id
    toplam_kayit = len(toplu_veri.kayitlar)

    logger.info(
        "Toplu işleme başlatıldı",
        extra={
            "toplu_id": toplu_id,
            "toplam_kayit": toplam_kayit
        }
    )

    islenen = 0
    hatalar = 0

    for kayit in toplu_veri.kayitlar:
        try:
            await kayit_isle(kayit)
            islenen += 1

            # Her 1000 kayıtta bir ilerleme logla
            if islenen % 1000 == 0:
                logger.info(
                    "Toplu işleme ilerlemesi",
                    extra={
                        "toplu_id": toplu_id,
                        "islenen": islenen,
                        "toplam": toplam_kayit,
                        "ilerleme_yuzdesi": (islenen / toplam_kayit) * 100
                    }
                )

        except Exception as e:
            hatalar += 1
            # Hatayı logla ama işlemeye devam et
            logger.error(
                "Kayıt işleme başarısız",
                extra={
                    "toplu_id": toplu_id,
                    "kayit_id": kayit.id,
                    "hata": str(e)
                }
            )

    logger.info(
        "Toplu işleme tamamlandı",
        extra={
            "toplu_id": toplu_id,
            "toplam_kayit": toplam_kayit,
            "islenen": islenen,
            "hatalar": hatalar,
            "basari_orani": (islenen / toplam_kayit) * 100
        }
    )
```

### 14. Güvenlik Olay Logging

```python
from miniflow.core.logger import get_logger
from datetime import datetime

guvenlik_logger = get_logger("guvenlik")


class GuvenlikServisi:
    def giris_deneme_logla(self, kullanici_email, ip_adresi, basarili, basarisizlik_nedeni=None):
        if basarili:
            guvenlik_logger.info(
                "Başarılı giriş",
                extra={
                    "olay_tipi": "giris_basarili",
                    "kullanici_email": kullanici_email,
                    "ip_adresi": ip_adresi,
                    "zaman_damgasi": datetime.utcnow().isoformat()
                }
            )
        else:
            guvenlik_logger.warning(
                "Başarısız giriş denemesi",
                extra={
                    "olay_tipi": "giris_basarisiz",
                    "kullanici_email": kullanici_email,
                    "ip_adresi": ip_adresi,
                    "basarisizlik_nedeni": basarisizlik_nedeni,
                    "zaman_damgasi": datetime.utcnow().isoformat()
                }
            )

    def yetki_ihlali_logla(self, kullanici_id, istenen_kaynak, gerekli_yetki):
        guvenlik_logger.critical(
            "Yetki ihlali tespit edildi",
            extra={
                "olay_tipi": "yetki_ihlali",
                "kullanici_id": kullanici_id,
                "istenen_kaynak": istenen_kaynak,
                "gerekli_yetki": gerekli_yetki,
                "zaman_damgasi": datetime.utcnow().isoformat()
            }
        )
```

## Konfigürasyon Örnekleri

### 15. Ortam Özel Konfigürasyon

```python
# config/logging.py
from miniflow import ModuleLoggerConfig
import os


def logging_config_getir():
    ortam = os.getenv("ORTAM", "gelistirme")

    if ortam == "production":
        return ModuleLoggerConfig(
            module_name="app",
            level="INFO",
            filename="logs/app.log",
            max_size_mb=1000,
            max_files=20,
            console_output=False,  # Production'da konsol yok
            file_formatter="json",
            custom_fields={
                "ortam": "production",
                "servis_adi": "miniflow-api"
            }
        )

    elif ortam == "staging":
        return ModuleLoggerConfig(
            module_name="app",
            level="DEBUG",
            filename="logs/app-staging.log",
            max_size_mb=500,
            max_files=10,
            console_output=True,
            console_level="WARNING",
            file_formatter="json",
            console_formatter="plain"
        )

    else:  # gelistirme
        return ModuleLoggerConfig(
            module_name="app",
            level="DEBUG",
            console_output=True,
            console_level="DEBUG",
            console_formatter="plain",
            file_formatter="json"
        )
```

Bu örnekler MiniFlow logger sisteminin esnekliğini ve gücünü göstermektedir. Basit temel kullanımdan karmaşık production senaryolarına kadar logger sistemi tutarlılık ve güvenilirlik sağlayarak ölçeklenmek üzere tasarlanmıştır.
