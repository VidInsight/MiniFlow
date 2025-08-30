# Logger Design Principles

## Ne Nerede ve Neden

### Neden Asenkron Logger?

#### Problem
Geleneksel synchronous logging yaklaşımları, production ortamlarında ciddi performans sorunlarına yol açar:

```python
# ❌ Problematic Synchronous Approach
def process_user_request():
    logger.info("Processing request")     # BLOCKS here
    # File I/O: 5-10ms delay
    # Network I/O: 50-100ms delay
    # Main thread waits...
    
    business_logic()                      # Delayed execution
    
    logger.info("Request completed")      # BLOCKS again
```

**Sorunlar**:
- **Latency**: Her log 5-100ms delay
- **Throughput**: Request/second dramatik düşüş
- **Resource Waste**: Thread'ler I/O'da bekliyor
- **User Experience**: Yavaş response time'lar

#### Çözüm: Async Logger Architecture
```python
# ✅ MiniFlow Async Approach
def process_user_request():
    logger.info("Processing request")     # Non-blocking (< 1ms)
    # Log immediately queued
    # Main thread continues
    
    business_logic()                      # Immediate execution
    
    logger.info("Request completed")      # Non-blocking (< 1ms)

# Background: Async log processing
async def background_log_processor():
    # Handles all I/O asynchronously
    # Batching for efficiency
    # Error handling and retry logic
```

### Ne Nerede: Component Responsibility

#### 1. AsyncLogger (miniflow/core/logger/logger.py)
**Nerede**: Ana logging interface
**Ne**: Application code ile logging system arasındaki bridge
**Neden Burada**:
```python
# Single Responsibility: Logging Interface
class AsyncLogger:
    def info(self, message, **kwargs):
        # ✅ Sync interface for ease of use
        # ✅ Async processing for performance
        # ✅ Context management for tracing
        
    def _process_async(self, record):
        # ✅ Background processing
        # ✅ Error isolation
        # ✅ Performance optimization
```

**Design Rationale**:
- **Developer Experience**: Sync interface familiar to developers
- **Performance**: Async processing doesn't block
- **Reliability**: Error isolation prevents app crashes
- **Compatibility**: Works with existing codebases

#### 2. LoggerRegistry (miniflow/core/logger/registry.py)
**Nerede**: Logger lifecycle management
**Ne**: Factory, cache, configuration manager
**Neden Burada**:
```python
# Centralized Management Pattern
class LoggerRegistry:
    def get_or_create_logger(self, name):
        # ✅ Prevents duplicate loggers
        # ✅ Enforces configuration consistency
        # ✅ Memory efficiency through caching
        # ✅ Lifecycle management
```

**Why Singleton Pattern**:
- **Consistency**: Single source of truth for all loggers
- **Memory Efficiency**: Shared logger instances
- **Configuration**: Central config management
- **Monitoring**: Global logger health tracking

#### 3. Handler System (miniflow/core/logger/handlers/)
**Nerede**: Output destination management
**Ne**: File, console, network output handlers
**Neden Ayrı Modüller**:
```python
# Separation of Concerns: Each handler knows its domain
class ConsoleHandler:
    # ✅ STDOUT/STDERR specifics
    # ✅ Color formatting
    # ✅ Terminal capabilities
    
class RotatingFileHandler:
    # ✅ File system operations
    # ✅ Rotation logic
    # ✅ Disk space management
    
class NetworkHandler:
    # ✅ Network protocols
    # ✅ Retry mechanisms
    # ✅ Buffer management
```

**Benefits**:
- **Modularity**: Independent development and testing
- **Extensibility**: Easy to add new handler types
- **Configuration**: Per-handler specific settings
- **Performance**: Optimized for each output type

### Neden Bu Tasarım Kararları?

#### 1. Context Propagation: ContextVar vs Thread-Local
**Karar**: `asyncio.ContextVar` kullanımı
**Neden Thread-Local Değil**:
```python
# ❌ Thread-Local Problems in Async
import threading
thread_local = threading.local()

async def handler1():
    thread_local.correlation_id = "123"
    await handler2()  # Different task context!

async def handler2():
    # ❌ correlation_id lost! Same thread, different task
    print(thread_local.correlation_id)  # AttributeError
```

**✅ ContextVar Solution**:
```python
# ✅ Async Context Aware
from contextvars import ContextVar
correlation_id_var: ContextVar[str] = ContextVar('correlation_id')

async def handler1():
    correlation_id_var.set("123")
    await handler2()  # Context preserved!

async def handler2():
    # ✅ correlation_id available across async boundaries
    print(correlation_id_var.get())  # "123"
```

#### 2. Sync Interface + Async Processing
**Karar**: Hybrid approach
**Neden Pure Async Değil**:
```python
# ❌ Pure Async Problems
async def business_logic():
    await logger.info("message")  # Awkward
    # Forces async propagation everywhere
    # Breaking change for existing code
    
# ❌ Sync everywhere in async function
def sync_helper():
    await logger.info("message")  # SyntaxError!
```

**✅ Hybrid Solution**:
```python
# ✅ Best of both worlds
def business_logic():
    logger.info("message")  # Natural, familiar
    # Works in sync and async contexts
    # No breaking changes
    # Performance benefits of async processing
```

#### 3. Error Handling: Multi-Level Strategy
**Neden Çoklu Seviye**:
```python
# Level 1: Handler Error Isolation
class FileHandler:
    def emit_sync(self, record):
        try:
            self._write_to_file(record)
        except PermissionError:
            # ✅ Handler-specific recovery
            self._fallback_to_temp_file(record)
        except DiskFullError:
            # ✅ Graceful degradation
            self._disable_handler()

# Level 2: Logger Error Recovery  
class AsyncLogger:
    def _send_to_handlers(self, record):
        for handler in self.handlers:
            try:
                handler.emit_sync(record)
            except Exception:
                # ✅ Continue with other handlers
                self._log_handler_error(handler, record)

# Level 3: System-Wide Fallback
class LoggerRegistry:
    def handle_critical_error(self, error, context):
        # ✅ Last resort logging
        # ✅ System administrator notification
        # ✅ Emergency shutdown if needed
```

### Performance Design Decisions

#### 1. Batching Strategy
**Neden Gerekli**:
```python
# ❌ Individual Processing (High Overhead)
def process_single_log(record):
    format_record(record)      # 0.1ms
    write_to_file(record)      # 5ms I/O
    sync_to_disk(record)       # 10ms I/O
    # Total: 15.1ms per log

# With 1000 logs/second: 15,100ms = 15 seconds delay!
```

**✅ Batch Processing**:
```python
def process_log_batch(records):
    formatted = [format_record(r) for r in records]  # 10ms for 100 records
    write_batch_to_file(formatted)                   # 8ms I/O
    sync_to_disk()                                   # 10ms I/O
    # Total: 28ms for 100 records = 0.28ms per log

# With 1000 logs/second: 280ms total = 72x improvement!
```

#### 2. Memory Management
**Problem**: Unbounded memory growth
**Solution**: Circular buffers and backpressure
```python
# ✅ Bounded Memory Design
class AsyncLogger:
    def __init__(self):
        self._queue = asyncio.Queue(maxsize=10000)  # Bounded
        self._batch_buffer = CircularBuffer(1000)   # Fixed size
        
    def info(self, message, **kwargs):
        try:
            self._queue.put_nowait(record)
        except asyncio.QueueFull:
            # ✅ Backpressure: Drop oldest or apply rate limiting
            self._handle_queue_full(record)
```

### Configuration Design

#### Neden Modüler Configuration?
**Problem**: Monolithic config zorluğu
```python
# ❌ Monolithic Configuration Problems
LOGGING_CONFIG = {
    "version": 1,
    "loggers": {
        "root": {...},
        "app": {...},
        "db": {...},
        "auth": {...},
        # 50+ logger configurations...
    }
}
# Hard to maintain, validate, and update
```

**✅ Modular Approach**:
```python
# Each module owns its configuration
class UserService:
    def __init__(self):
        config = ModuleLoggerConfig(
            module_name="user_service",
            level="INFO",
            tags={"user", "authentication"},
            custom_fields={
                "service_version": "1.2.3",
                "team": "auth-team"
            }
        )
        self.logger = get_logger("user_service", config)
```

**Benefits**:
- **Ownership**: Each team configures their loggers
- **Validation**: Type-safe configuration
- **Runtime Updates**: Change config without restart
- **Testing**: Easy to mock and test configurations

### Security and Privacy

#### 1. Sensitive Data Filtering
**Neden Gerekli**:
```python
# ❌ Accidental Sensitive Data Logging
user_data = {
    "email": "user@example.com",
    "password": "secret123",          # ❌ Sensitive!
    "credit_card": "1234-5678-9012"  # ❌ Sensitive!
}
logger.info("User data", extra={"user": user_data})
# Logs contain sensitive information!
```

**✅ Automatic Filtering**:
```python
# Built-in sensitive data detection
class LogRecord:
    def sanitize_data(self, data):
        # ✅ Automatic detection and masking
        sensitive_patterns = ["password", "token", "credit_card", "ssn"]
        return mask_sensitive_fields(data, sensitive_patterns)

# Result in logs:
# {"user": {"email": "user@example.com", "password": "***", "credit_card": "****-****-9012"}}
```

#### 2. Audit Trail
**Requirement**: Compliance and debugging
```python
# ✅ Immutable Audit Logs
class AuditLogger:
    def log_user_action(self, user_id, action, resource):
        # Tamper-evident logging
        record = {
            "timestamp": utc_now(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "checksum": calculate_checksum(...)  # Integrity check
        }
        self.audit_handler.emit(record)
```

### Integration Design

#### Neden Operations Layer?
**Problem**: Business logic ve teknik logging karışımı
```python
# ❌ Mixed Concerns
def create_user(user_data):
    # Business logic mixed with technical logging
    logger.debug("Starting user creation")
    validate_user_data(user_data)
    logger.debug("Validation completed")
    user = save_to_database(user_data)
    logger.info(f"User {user.id} created")
    send_welcome_email(user)
    logger.debug("Welcome email sent")
    return user
```

**✅ Separation through Operations**:
```python
# Business Operations Layer
class UserOperations:
    def create_user(self, user_data):
        self.logger.info("User creation started", extra={"email": user_data.email})
        
        try:
            user = self.user_service.create_user(user_data)
            self.logger.info("User created successfully", extra={"user_id": user.id})
            return user
        except ValidationError as e:
            self.logger.warning("User creation failed - validation", extra={"errors": e.errors})
            raise
        except Exception as e:
            self.logger.error("User creation failed - system error", exc_info=True)
            raise

# Pure Business Logic
class UserService:
    def create_user(self, user_data):
        # ✅ Focus on business logic only
        validate_user_data(user_data)
        user = save_to_database(user_data)
        send_welcome_email(user)
        return user
```

### Monitoring and Observability

#### Built-in Metrics
**Neden Gerekli**: Production logger'ın kendisi monitör edilmeli
```python
# ✅ Self-Monitoring Logger
class AsyncLogger:
    def __init__(self):
        self.metrics = {
            "logs_processed": 0,
            "logs_dropped": 0,
            "avg_processing_time": 0,
            "handler_errors": defaultdict(int),
            "queue_size": 0
        }
    
    def get_health_status(self):
        return {
            "status": "healthy" if self.metrics["logs_dropped"] < 100 else "degraded",
            "metrics": self.metrics,
            "handlers_status": [h.get_status() for h in self.handlers]
        }
```

### Future-Proofing

#### Extensibility Points
**Design for Change**:
```python
# ✅ Plugin Architecture
class LoggerRegistry:
    def register_formatter(self, name, formatter_class):
        # Custom formatters
        
    def register_handler(self, name, handler_class):
        # Custom handlers
        
    def register_filter(self, name, filter_class):
        # Custom filters
        
    def register_strategy(self, name, strategy_class):
        # Custom logging strategies
```

**Hook System**:
```python
# ✅ Pre/Post Processing Hooks
class AsyncLogger:
    def add_pre_log_hook(self, hook_func):
        # Modify records before processing
        
    def add_post_log_hook(self, hook_func):
        # Actions after logging (notifications, etc.)
```

## Conclusion

MiniFlow Logger tasarımı, modern production sistemlerin gereksinimlerini karşılamak için dikkatli bir şekilde planlanmış architecture principles'a dayanır:

1. **Performance First**: Async design ile non-blocking operations
2. **Developer Experience**: Familiar sync interface
3. **Production Ready**: Comprehensive error handling and monitoring
4. **Scalable**: Modular design ve efficient resource usage
5. **Maintainable**: Clear separation of concerns
6. **Extensible**: Plugin architecture ve hook system
7. **Secure**: Built-in sensitive data protection
8. **Observable**: Rich metrics ve health monitoring

Bu prensipler, sistemi hem development hem production ortamlarında güvenilir ve performanslı hale getirir.
