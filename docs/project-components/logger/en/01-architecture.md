# Logger Module Architecture

## Overview
MiniFlow Logger modülü, production-grade asenkron logging sistemi sağlayan kapsamlı bir modüldür. Hem performans hem de güvenilirlik açısından kritik iş yüklerini desteklemek üzere tasarlanmıştır.

## Core Architecture

### 1. Modül Yapısı
```
miniflow/core/logger/
├── __init__.py              # Public API exports
├── logger.py                # AsyncLogger ana sınıfı
├── registry.py              # LoggerRegistry merkezi yönetim
├── levels.py                # LogLevel enum tanımları
├── handlers/                # Log handler'ları
│   ├── console.py          # Console output handler
│   ├── file.py             # File output handler
│   └── rotating_file.py    # Rotating file handler
├── formatters/              # Log formatters
│   ├── json.py             # JSON formatter
│   └── plain.py            # Plain text formatter
├── config.py               # Configuration models
├── context.py              # Correlation ID context
└── utils.py                # Utility functions
```

### 2. Temel Bileşenler

#### AsyncLogger (logger.py)
**Amaç**: Asenkron logging operasyonları için ana interface
**Algoritma Mantığı**:
```python
# Hybrid Async-Sync Pattern
class AsyncLogger:
    def info(self, message, **kwargs):  # Sync interface
        # 1. Sync validation ve preprocessing
        # 2. Async queue'ya log record gönder
        # 3. Background task log'u process eder
        # 4. Caller bloke olmaz
```

**Key Features**:
- **Non-blocking Interface**: Caller thread'i bloke etmez
- **Async Processing**: Background'da log processing
- **Context Propagation**: Correlation ID otomatik propagation
- **Handler Management**: Multiple handler support
- **Level Filtering**: Efficient level-based filtering

#### LoggerRegistry (registry.py)
**Amaç**: Tüm logger instance'larının merkezi yönetimi
**Algoritma Mantığı**:
```python
# Singleton Registry Pattern
class LoggerRegistry:
    _instance = None
    _loggers = {}           # Logger cache
    _configs = {}           # Configuration cache
    _strategy = Strategy    # Logging strategy
    
    def get_or_create_logger(self, name):
        # 1. Cache'den kontrol et
        # 2. Yoksa yeni logger oluştur
        # 3. Config'le yapılandır
        # 4. Cache'e kaydet
        # 5. Return logger
```

**Design Patterns**:
- **Singleton Pattern**: Tek registry instance
- **Factory Pattern**: Logger creation
- **Strategy Pattern**: Different logging strategies
- **Observer Pattern**: Config changes notification

#### Handler System (handlers/)
**Amaç**: Log output destinasyonlarını yönet
**Handler Types**:

1. **ConsoleHandler**: STDOUT/STDERR output
2. **FileHandler**: Static file output  
3. **RotatingFileHandler**: Size-based rotation

**Handler Lifecycle**:
```python
# Handler Processing Pipeline
def emit_sync(self, record):
    # 1. Level filtering
    # 2. Format record
    # 3. Write to destination
    # 4. Handle errors gracefully
    # 5. Performance metrics
```

### 3. Configuration System

#### ModuleLoggerConfig
**Struktur**:
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

**Configuration Strategies**:
- **Centralized**: Tek config için tüm modüller
- **Module-based**: Her modül kendi config'i
- **Hybrid**: Mixed approach
- **Custom**: Özel configuration logic

### 4. Async Architecture

#### Thread Model
```python
# Main Thread (Caller)
logger.info("message")  # Non-blocking call
    ↓
# Background Thread (Processor)  
async def _process_log_record():
    # 1. Format record
    # 2. Send to handlers
    # 3. Handle errors
    # 4. Update metrics
```

**Async Benefits**:
- **Performance**: No I/O blocking on main thread
- **Scalability**: Handle high-volume logging
- **Reliability**: Error isolation
- **Monitoring**: Performance metrics collection

### 5. Context Management

#### Correlation ID System
**Purpose**: Request tracking across distributed components
**Implementation**:
```python
# Context Variables (asyncio.context)
correlation_id_var: ContextVar[str] = ContextVar('correlation_id')

# Automatic Propagation
def set_correlation_id(correlation_id: str):
    correlation_id_var.set(correlation_id)
    
def get_correlation_id() -> str:
    return correlation_id_var.get("unknown")
```

**Flow**:
1. **Request Entry**: Correlation ID set at middleware
2. **Propagation**: Automatic in async context
3. **Logging**: Auto-attached to all log records
4. **Cross-service**: Correlation ID in headers

### 6. Performance Optimizations

#### Batching Strategy
```python
# Log Record Batching
class AsyncLogger:
    def __init__(self):
        self._batch = []
        self._batch_size = 100
        self._batch_timeout = 1.0  # seconds
    
    async def _process_batch(self):
        # Process multiple records together
        # Reduce I/O overhead
        # Improve throughput
```

#### Memory Management
- **Circular Buffers**: Fixed memory footprint
- **Lazy Loading**: Load handlers on demand
- **Weak References**: Prevent memory leaks
- **Garbage Collection**: Explicit cleanup

### 7. Error Handling

#### Multi-level Error Handling
```python
# 1. Handler Level
def emit_sync(self, record):
    try:
        self._write_record(record)
    except Exception as e:
        self._handle_error(e, record)

# 2. Logger Level  
def _send_to_handler(self, handler, record):
    try:
        handler.emit_sync(record)
    except Exception as e:
        self._fallback_logging(e, record)

# 3. Registry Level
def handle_logger_error(self, logger_name, error):
    # System-wide error handling
    # Alert administrators
    # Fallback mechanisms
```

**Error Recovery**:
- **Graceful Degradation**: Continue with available handlers
- **Fallback Logging**: System logger for critical errors
- **Circuit Breaker**: Temporarily disable failing handlers
- **Health Monitoring**: Track handler health status

### 8. Integration Points

#### Application Integration

```python
# Fast API Integration
from miniflow.core.logger import get_logger

logger = get_logger("api_service")


@app.middleware("http")
async def logging_middleware(request, call_next):
# 1. Set correlation ID
# 2. Log request
# 3. Process request
# 4. Log response
# 5. Cleanup context
```

#### Operations Integration
```python
# Operations Layer Integration
class LoggerOperations:
    def __init__(self):
        self.registry = get_logger_registry()
        self.logger = get_logger("operations")
    
    def get_available_loggers(self):
        # Business logic for logger management
        # Discovery, configuration, monitoring
```

## Design Principles

### 1. **Separation of Concerns**
- **Logging Logic**: AsyncLogger
- **Configuration**: LoggerRegistry + Config models
- **Output**: Handler system
- **Formatting**: Formatter system
- **Context**: Context management

### 2. **Extensibility**
- **Plugin Architecture**: Custom handlers/formatters
- **Strategy Pattern**: Different logging strategies
- **Hook System**: Pre/post processing hooks
- **Event System**: Configuration change events

### 3. **Performance First**
- **Async Design**: Non-blocking operations
- **Lazy Loading**: Load on demand
- **Efficient Filtering**: Early level filtering
- **Memory Conscious**: Bounded memory usage

### 4. **Production Ready**
- **Error Resilience**: Multi-level error handling
- **Monitoring**: Built-in metrics and health checks
- **Configuration**: Runtime configuration updates
- **Security**: Sensitive data filtering

### 5. **Developer Experience**
- **Simple API**: Intuitive logging interface
- **Rich Context**: Automatic context propagation
- **Debugging**: Comprehensive debug information
- **Testing**: Mock-friendly design

## Architecture Benefits

### Performance
- **Non-blocking**: Main thread never blocks on I/O
- **Scalable**: Handle thousands of logs/second
- **Efficient**: Minimal memory and CPU overhead
- **Optimized**: Batch processing and caching

### Reliability
- **Fault Tolerant**: Continue operation on handler failures
- **Data Safety**: No log loss on application crashes
- **Monitoring**: Real-time health and performance metrics
- **Recovery**: Automatic error recovery mechanisms

### Maintainability
- **Modular Design**: Clear component boundaries
- **Testable**: Comprehensive unit and integration tests
- **Configurable**: Runtime configuration without restarts
- **Observable**: Rich debugging and monitoring capabilities

### Scalability
- **Distributed**: Correlation ID for distributed tracing
- **High Volume**: Async processing for high throughput
- **Resource Efficient**: Bounded resource usage
- **Cloud Native**: Container and orchestration friendly
