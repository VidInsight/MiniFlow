# MiniFlow Handler'lar ve Execution Engine Bağlantıları - Türkçe Dokümantasyon

## Genel Bakış

MiniFlow'da handler'lar ve execution engine arasında güçlü bir bağlantı sistemi bulunur. Bu sistem, iş akışlarının verimli bir şekilde işlenmesini sağlar.

## Sistem Mimarisi

```
Trigger → InputHandler → ExecutionEngine → OutputHandler → Database
   ↓           ↓              ↓              ↓
Handler    Queue        Processing      Results
Manager    System       Simulation      Storage
```

## Handler Türleri

### 1. InputHandler (Giriş İşleyici)

InputHandler, hazır execution input'larını işler ve execution engine'e gönderir.

#### Sorumlulukları:
- Ready execution input'ları polling yapar (dependency_count = 0)
- Task context ve parametreleri işler
- Task'ları execution engine'e gönderir
- İşlenen task'ları execution_input tablosundan kaldırır
- Monitoring ve metrics sağlar

#### Engine Bağlantısı:
```python
class InputHandler(MonitorableComponent):
    def __init__(self, config: InputHandlerConfig, orchestrator: DatabaseOrchestrator, exec_engine):
        self.exec_engine = exec_engine  # Execution engine referansı
        # ... diğer initialization
```

#### Engine'e Veri Gönderme:
```python
def _send_tasks_to_engine(self, prepared_payloads: List[Dict[str, Any]]) -> bool:
    """Send prepared tasks to execution engine."""
    try:
        if not self.exec_engine:
            self.logger.error("No execution engine available")
            return False
        
        # Engine'e bulk olarak task'ları gönder
        success = self.exec_engine.put_items_bulk(prepared_payloads)
        
        if success:
            self.logger.info(f"Successfully sent {len(prepared_payloads)} tasks to execution engine")
            return True
        else:
            self.logger.error("Failed to send tasks to execution engine")
            return False
            
    except Exception as e:
        self.logger.error(f"Error sending tasks to engine: {str(e)}")
        return False
```

### 2. OutputHandler (Çıkış İşleyici)

OutputHandler, execution engine'den sonuçları alır ve veritabanına kaydeder.

#### Sorumlulukları:
- Execution engine'den sonuçları alır
- Sonuçları execution_output tablosuna kaydeder
- Execution durumunu günceller
- Node dependency'lerini günceller
- Monitoring ve metrics sağlar

#### Engine Bağlantısı:
```python
class OutputHandler(MonitorableComponent):
    def __init__(self, config: OutputHandlerConfig, orchestrator: DatabaseOrchestrator, exec_engine):
        self.exec_engine = exec_engine  # Execution engine referansı
        # ... diğer initialization
```

#### Engine'den Veri Alma:
```python
def _process_execution_results(self) -> bool:
    """Process execution results from engine."""
    try:
        if not self.exec_engine:
            self.logger.error("No exec_engine reference for output handler!")
            raise Exception("No exec_engine reference for output handler!")
        
        # Engine'den sonuçları al
        results = self.exec_engine.get_execution_results(max_items=self.config.batch_size)
        
        if not results:
            return True  # No results to process
        
        # Sonuçları işle
        for result in results:
            self._process_single_result(result)
        
        return True
        
    except Exception as e:
        self.logger.error(f"Error processing execution results: {str(e)}")
        return False
```

## Execution Engine (MockExecutionEngine)

### Genel Özellikler:
- Input queue ile InputHandler'dan task alır
- Output queue ile OutputHandler'a sonuç gönderir
- Script execution'ı simüle eder
- Configurable delay ve success rate
- Thread-safe queue operations

### Queue Sistemi:
```python
class MockExecutionEngine:
    def __init__(self, processing_delay: float = 2.0, success_rate: float = 0.95, max_queue_size: int = 1000):
        # Handler'larla iletişim için queue'lar
        self.input_queue = queue.Queue(maxsize=max_queue_size)   # InputHandler'dan gelen task'lar
        self.output_queue = queue.Queue(maxsize=max_queue_size)  # OutputHandler'a giden sonuçlar
```

### InputHandler ile Bağlantı:
```python
def put_items_bulk(self, tasks: List[Dict[str, Any]]) -> bool:
    """
    InputHandler'dan gelen task'ları input queue'ya ekler.
    
    Args:
        tasks: InputHandler'dan gelen task listesi
        
    Returns:
        bool: Başarı durumu
    """
    try:
        for task in tasks:
            self.input_queue.put_nowait(task)
        
        self.logger.info(f"Added {len(tasks)} tasks to input queue")
        return True
        
    except queue.Full:
        self.logger.error("Input queue is full, cannot add more tasks")
        return False
    except Exception as e:
        self.logger.error(f"Error adding tasks to input queue: {str(e)}")
        return False
```

### OutputHandler ile Bağlantı:
```python
def get_execution_results(self, max_items: int = 50) -> List[Dict[str, Any]]:
    """
    OutputHandler'a sonuçları gönderir.
    
    Args:
        max_items: Maksimum sonuç sayısı
        
    Returns:
        List[Dict]: İşlenmiş sonuç listesi
    """
    results = []
    
    try:
        for _ in range(max_items):
            try:
                result = self.output_queue.get_nowait()
                results.append(result)
            except queue.Empty:
                break
        
        if results:
            self.logger.debug(f"Retrieved {len(results)} execution results")
        
        return results
        
    except Exception as e:
        self.logger.error(f"Error retrieving execution results: {str(e)}")
        return []
```

## Veri Akışı

### 1. Task Processing Flow:
```
InputHandler → Engine Input Queue → Processing Loop → Engine Output Queue → OutputHandler
```

### 2. Detaylı Adımlar:

#### Adım 1: InputHandler Task Hazırlama
```python
def _create_task_payload(self, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Task payload'ını hazırla ve context'i işle."""
    try:
        # Task context'ini işle (referans çözümleme)
        processed_context = self.orchestrator.process_task_context(task)
        
        # Payload oluştur
        payload = {
            'execution_id': task['execution_id'],
            'workflow_id': task['workflow_id'],
            'node_id': task['node_id'],
            'correlation_id': task.get('correlation_id'),
            'node_name': task['node_name'],
            'script_name': task.get('script_name'),
            'script_path': task.get('script_path'),
            'context': processed_context,  # Çözülmüş referanslar
            'priority': task.get('priority', 0),
            'max_retries': 3,
            'timeout_seconds': 300
        }
        
        return payload
        
    except Exception as e:
        self.logger.error(f"Error creating task payload: {str(e)}")
        return None
```

#### Adım 2: Engine Task İşleme
```python
def _process_task(self, task: Dict[str, Any]):
    """Tek bir task'ı işle ve sonuç üret."""
    try:
        self.logger.info(f"Processing task: {task.get('node_name', 'unknown')}")
        
        # Simüle edilmiş processing delay
        time.sleep(self.processing_delay)
        
        # Mock sonuç üret
        result = self._generate_mock_result(task)
        
        # Sonucu output queue'ya ekle
        self.output_queue.put_nowait(result)
        
    except Exception as e:
        self.logger.error(f"Error processing task: {str(e)}")
        # Hata sonucu üret
        error_result = self._generate_error_result(task, str(e))
        self.output_queue.put_nowait(error_result)
```

#### Adım 3: OutputHandler Sonuç İşleme
```python
def _process_single_result(self, result: Dict[str, Any]) -> bool:
    """Tek bir execution sonucunu işle."""
    try:
        # Execution output kaydet
        execution_output_data = {
            'execution_id': result['execution_id'],
            'workflow_id': result['workflow_id'],
            'node_id': result['node_id'],
            'correlation_id': result.get('correlation_id'),
            'status': result['status'],
            'result_data': result['result_data'],
            'started_at': result['started_at'],
            'ended_at': result['ended_at']
        }
        
        # Veritabanına kaydet
        self.orchestrator.execution_output_orchestrator.create(execution_output_data)
        
        # Node dependency'lerini güncelle
        self._update_node_dependencies(result)
        
        return True
        
    except Exception as e:
        self.logger.error(f"Error processing result: {str(e)}")
        return False
```

## Queue Yönetimi

### Input Queue (InputHandler → Engine):
- **Amaç**: InputHandler'dan gelen task'ları engine'e iletmek
- **Boyut**: Configurable (default: 1000)
- **Thread Safety**: Thread-safe queue operations
- **Error Handling**: Queue full durumunda hata yönetimi

### Output Queue (Engine → OutputHandler):
- **Amaç**: Engine'den işlenmiş sonuçları OutputHandler'a iletmek
- **Boyut**: Configurable (default: 1000)
- **Thread Safety**: Thread-safe queue operations
- **Error Handling**: Queue empty durumunda graceful handling

## Monitoring ve Metrics

### InputHandler Metrics:
```python
self.metrics = {
    'successful_tasks': 0,    # Başarılı task sayısı
    'failed_tasks': 0,        # Başarısız task sayısı
    'tasks_sent_to_engine': 0 # Engine'e gönderilen task sayısı
}
```

### OutputHandler Metrics:
```python
self.metrics = {
    'results_processed': 0,   # İşlenen sonuç sayısı
    'results_saved': 0,       # Kaydedilen sonuç sayısı
    'dependency_updates': 0   # Güncellenen dependency sayısı
}
```

### Engine Metrics:
```python
self.stats = {
    'tasks_processed': 0,     # İşlenen task sayısı
    'tasks_successful': 0,    # Başarılı task sayısı
    'tasks_failed': 0,        # Başarısız task sayısı
    'queue_errors': 0         # Queue hata sayısı
}
```

## Error Handling

### InputHandler Hataları:
- **Engine Bağlantı Hatası**: Engine referansı yoksa hata
- **Queue Full**: Input queue doluysa task gönderilemez
- **Context Processing**: Referans çözümleme hatası

### Engine Hataları:
- **Processing Error**: Task işleme sırasında hata
- **Queue Operations**: Queue put/get operasyon hataları
- **Thread Safety**: Thread-safe operasyon hataları

### OutputHandler Hataları:
- **Engine Bağlantı Hatası**: Engine referansı yoksa hata
- **Database Error**: Sonuç kaydetme hatası
- **Dependency Update**: Dependency güncelleme hatası

## Configuration

### InputHandler Config:
```python
@dataclass
class InputHandlerConfig:
    batch_size: int = 50                    # Batch boyutu
    worker_threads: int = 4                 # Worker thread sayısı
    min_polling_interval: float = 0.1       # Min polling interval
    max_polling_interval: float = 5.0       # Max polling interval
    current_polling_interval: float = 1.0   # Mevcut polling interval
```

### OutputHandler Config:
```python
@dataclass
class OutputHandlerConfig:
    batch_size: int = 50                    # Batch boyutu
    worker_threads: int = 4                 # Worker thread sayısı
    min_polling_interval: float = 0.1       # Min polling interval
    max_polling_interval: float = 5.0       # Max polling interval
    current_polling_interval: float = 1.0   # Mevcut polling interval
```

### Engine Config:
```python
def __init__(self, 
             processing_delay: float = 2.0,    # Processing delay (saniye)
             success_rate: float = 0.95,       # Success rate (0.0-1.0)
             max_queue_size: int = 1000):      # Max queue boyutu
```

## Threading Model

### InputHandler Threading:
- **Main Thread**: Polling ve task hazırlama
- **Worker Threads**: Task processing ve engine communication
- **Thread Pool**: Configurable worker thread sayısı

### OutputHandler Threading:
- **Main Thread**: Polling ve result processing
- **Worker Threads**: Database operations ve dependency updates
- **Thread Pool**: Configurable worker thread sayısı

### Engine Threading:
- **Processing Thread**: Task processing loop
- **Queue Operations**: Thread-safe queue operations
- **Daemon Thread**: Background processing

## Performance Optimization

### Queue Management:
- **Bulk Operations**: put_items_bulk() ile batch processing
- **Non-blocking**: put_nowait() ve get_nowait() kullanımı
- **Timeout Handling**: Queue operations için timeout

### Batch Processing:
- **InputHandler**: Batch olarak task'ları engine'e gönder
- **OutputHandler**: Batch olarak sonuçları işle
- **Configurable Batch Size**: Performance tuning için

### Polling Optimization:
- **Adaptive Polling**: Queue durumuna göre polling interval ayarla
- **Empty Cycle Detection**: Boş cycle'ları tespit et ve interval artır
- **Backpressure**: Queue full durumunda polling durdur

## Troubleshooting

### Yaygın Sorunlar:

1. **Engine Bağlantı Hatası**:
   - Engine referansı doğru mu kontrol et
   - Engine başlatıldı mı kontrol et
   - Handler'lar engine'den önce başlatılmış mı kontrol et

2. **Queue Full Hatası**:
   - Queue boyutunu artır
   - Processing delay'i azalt
   - Worker thread sayısını artır

3. **Task Processing Hatası**:
   - Context processing hatası kontrol et
   - Referans çözümleme hatası kontrol et
   - Script path ve parametreleri kontrol et

### Debug Komutları:
```bash
# Handler durumları
curl -X GET "http://127.0.0.1:8000/api/bfa/monitoring/components"

# Engine metrics
curl -X GET "http://127.0.0.1:8000/api/bfa/monitoring/metrics/component/execution_engine"

# Handler metrics
curl -X GET "http://127.0.0.1:8000/api/bfa/monitoring/metrics/component/input_handler"
curl -X GET "http://127.0.0.1:8000/api/bfa/monitoring/metrics/component/output_handler"
```

## Sonuç

MiniFlow handler'lar ve execution engine arasındaki bağlantı sistemi:

- **Güçlü Queue Sistemi**: Thread-safe queue operations
- **Efficient Processing**: Batch processing ve bulk operations
- **Robust Error Handling**: Comprehensive error management
- **Monitoring**: Real-time metrics ve monitoring
- **Configurable**: Performance tuning için configurable parameters
- **Scalable**: Thread pool ve adaptive polling ile scalable

Bu sistem, production-ready bir iş akışı execution platformu sağlar.

