"""
Log handlers for MiniFlow logging system.
"""

import os
import sys
import glob
import asyncio
import threading
from pathlib import Path
from typing import Optional, List, TextIO

from .formatters import JSONFormatter
from .utils import handle_logging_error
from .levels import LogLevel


class ConsoleHandler:
    """Console'a yazan handler"""
    
    def __init__(self, stream: Optional[TextIO] = None, *, level: str = 'INFO', formatter=None):
        self.stream = stream or sys.stdout
        self._lock = threading.Lock()
        self.level = LogLevel.from_string(level) if isinstance(level, str) else level
        self.formatter = formatter  # optional formatter override
    
    def emit_sync(self, message: str) -> None:
        """Mesajı console'a yaz (sync)"""
        # Thread-safe yazma
        with self._lock:
            print(message, file=self.stream)
            self.stream.flush()  # Buffer'ı temizle
    
    async def emit(self, message: str) -> None:
        """Mesajı console'a yaz (async wrapper)"""
        self.emit_sync(message)
    
    async def start(self) -> None:
        """Handler'ı başlat (console için gerekli değil)"""
        pass
    
    async def stop(self) -> None:
        """Handler'ı durdur (console için gerekli değil)"""
        pass


class RotatingFileHandler:
    """
    Rotating file handler - maksimum dosya sayısı (max_files) kadar backup tutar.
    
    Her dosya belirlenen maksimum boyuta (max_size_mb) ulaştığında,
    mevcut dosya yeniden adlandırılır (.1, .2, ...) ve yeni dosya açılır.
    En eski dosya sınırı aşıldığında silinir.
    """
    
    def __init__(
        self,
        filename: str,
        max_size_mb: int = 100,
        max_files: int = 5,
        encoding: str = 'utf-8',
        *,
        level: str = 'INFO',
        formatter=None,
        queue_size: int = 10000,
        queue_timeout: float = 5.0,
        worker_timeout: float = 1.0
    ):
        """
        Args:
            filename: Log dosyasının adı
            max_lines_per_file: Her dosyada maksimum satır sayısı
            max_files: Tutulacak maksimum dosya sayısı
            encoding: Dosya encoding'i
        """
        if max_files < 1:
            raise ValueError("max_files 1'den küçük olamaz")
        if max_size_mb < 1:
            raise ValueError("max_size_mb 1'den küçük olamaz")
            
        self.filename = filename
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_files = max_files
        self.encoding = encoding
        self.level = LogLevel.from_string(level) if isinstance(level, str) else level
        self.formatter = formatter  # optional formatter override
        
        # Performance tuning parameters
        self.queue_size = queue_size
        self.queue_timeout = queue_timeout
        self.worker_timeout = worker_timeout
        
        # Dosya yolu ve pattern
        self.file_path = Path(filename).resolve()  # Absolute path kullan
        self.file_pattern = f"{self.file_path.stem}*{self.file_path.suffix}"
        self.file_dir = self.file_path.parent
        
        # Mevcut dosya bilgileri
        self.current_file: Optional[str] = None
        self.current_size = 0
        
        # Thread safety için lock
        self._file_lock = threading.Lock()
        
        # Async queue
        self.queue: Optional[asyncio.Queue] = None
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._closed = False
        
        # İlk dosyayı hazırla
        self._prepare_current_file()
    

    
    def _prepare_current_file(self) -> None:
        """Mevcut dosyayı hazırla"""
        with self._file_lock:
            if not self.current_file:
                self.current_file = str(self.file_path)
            else:
                # Boyut kontrolü
                self._update_current_size()
                if self.current_size >= self.max_size_bytes:
                    self._rotate_files()
            
            # Dizin yoksa oluştur
            self.file_dir.mkdir(parents=True, exist_ok=True)
            
            # Mevcut dosyanın boyutunu belirle
            self._update_current_size()
    
    def _update_current_size(self) -> None:
        """Mevcut dosyanın byte cinsinden boyutunu güncelle"""
        try:
            if os.path.exists(self.current_file):
                self.current_size = os.path.getsize(self.current_file)
            else:
                self.current_size = 0
        except Exception as e:
            handle_logging_error(e, f"File size read error ({self.current_file})")
            self.current_size = 0
    
    def _rotate_files(self) -> None:
        """Dosyaları rotate et"""
        try:
            # Mevcut dosyayı yeniden adlandır
            if os.path.exists(self.current_file):
                backup_name = self._get_backup_filename()
                try:
                    os.rename(self.current_file, backup_name)
                except OSError as e:
                    handle_logging_error(e, "File rename error")
            
            # Yeni dosya için reset
            self.current_file = str(self.file_path)
            self.current_size = 0

            # Güncel dosya listesini al ve limit aşımında buda
            pattern = str(self.file_dir / f"{self.file_path.stem}.*{self.file_path.suffix}")
            existing_files = glob.glob(pattern)
            existing_files.sort(key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0)
            while len(existing_files) > self.max_files:
                try:
                    oldest_file = existing_files.pop(0)
                    if os.path.exists(oldest_file):
                        os.remove(oldest_file)
                except OSError as e:
                    handle_logging_error(e, f"Old file deletion error ({oldest_file})")
                    break
            
        except Exception as e:
            handle_logging_error(e, "File rotation error")
    
    def _get_backup_filename(self) -> str:
        """Sıralı numara ile backup dosya adı oluştur"""
        # Mevcut dosyaları bul (sadece numaralı dosyalar)
        pattern = str(self.file_dir / f"{self.file_path.stem}.*{self.file_path.suffix}")
        existing_files = glob.glob(pattern)
        
        # En yüksek numarayı bul
        max_num = 0
        for file_path in existing_files:
            try:
                # Dosya adından numarayı çıkar: test_26.1.log -> 1
                filename = os.path.basename(file_path)
                if '.' in filename:
                    parts = filename.split('.')
                    if len(parts) >= 2:
                        num_str = parts[-2]  # test_26.1.log -> 1
                        if num_str.isdigit():
                            max_num = max(max_num, int(num_str))
            except (ValueError, IndexError):
                continue
        
        # Yeni numara (1'den başla)
        new_num = max_num + 1
        return str(self.file_path.parent / f"{self.file_path.stem}.{new_num}{self.file_path.suffix}")
    
    def _write_to_file(self, message: str) -> None:
        """Ortak dosya yazma metodu"""
        if self._closed:
            return
            
        with self._file_lock:
            try:
                # Mevcut dosyayı boyuta göre kontrol et
                if self.current_size >= self.max_size_bytes:
                    self._rotate_files()
                    self.current_size = 0  # Reset size after rotation
                
                # Dosyaya yaz
                with open(self.current_file, 'a', encoding=self.encoding, errors='replace') as f:
                    data = (message + '\n')
                    f.write(data)
                    f.flush()  # Buffer'ı temizle
                
                try:
                    self.current_size += len(data.encode(self.encoding, errors='replace'))
                except Exception:
                    # Encode ölçümü başarısız olursa dosyadan gerçek boyutu al
                    self._update_current_size()
                
            except Exception as e:
                # Robust error handling
                handle_logging_error(e, f"Log write error ({self.current_file})")
    
    async def _write_async(self, message: str) -> None:
        """Asenkron olarak dosyaya yaz"""
        # Use sync method which includes rotation logic
        self._write_to_file(message)
    
    async def _worker(self) -> None:
        """Async worker - queue'dan mesajları alıp dosyaya yazar"""
        while self.running and not self._closed:
            try:
                # Queue'dan mesaj al (configurable timeout ile)
                message = await asyncio.wait_for(self.queue.get(), timeout=self.worker_timeout)
                if message is None:  # Poison pill - durdurma sinyali
                    break
                    
                await self._write_async(message)
                self.queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                # Robust error handling
                handle_logging_error(e, "Worker")
    
    async def emit(self, message: str) -> None:
        """Log mesajını queue'ya ekle"""
        if self._closed:
            return
            
        if not self.running:
            await self.start()
        
        if self.queue:
            try:
                await asyncio.wait_for(self.queue.put(message), timeout=self.queue_timeout)
            except asyncio.TimeoutError:
                handle_logging_error(TimeoutError("Log queue full"), "Queue timeout")
            except Exception as e:
                # Robust error handling
                handle_logging_error(e, "Queue message enqueue error")
    
    def emit_sync(self, message: str) -> None:
        """Senkron olarak dosyaya yaz"""
        self._write_to_file(message)
    
    async def start(self) -> None:
        """Handler'ı başlat"""
        if not self.running and not self._closed:
            self.running = True
            self.queue = asyncio.Queue(maxsize=self.queue_size)  # Configurable queue size
            self._task = asyncio.create_task(self._worker())
    
    async def stop(self) -> None:
        """Handler'ı durdur"""
        if not self.running:
            return
            
        self.running = False
        
        if self.queue:
            # Poison pill gönder
            try:
                await asyncio.wait_for(self.queue.put(None), timeout=1.0)
            except asyncio.TimeoutError:
                pass
            
            # Queue'daki kalan mesajları işle
            remaining_messages = []
            while not self.queue.empty():
                try:
                    message = self.queue.get_nowait()
                    if message is not None:
                        remaining_messages.append(message)
                    self.queue.task_done()
                except asyncio.QueueEmpty:
                    break
            
            # Kalan mesajları senkron olarak yaz
            for message in remaining_messages:
                await self._write_async(message)
        
        # Worker task'ını bekle
        if self._task and not self._task.done():
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
    
    async def close(self) -> None:
        """Handler'ı kapat"""
        if not self._closed:
            self._closed = True
            await self.stop()
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    def __del__(self):
        """Destructor - cleanup"""
        # Sadece uyarı ver, async işlem yapma
        if self.running and not self._closed:
            handle_logging_error(
                RuntimeError("Handler not properly closed"), 
                f"RotatingFileHandler ({self.filename})"
            )


