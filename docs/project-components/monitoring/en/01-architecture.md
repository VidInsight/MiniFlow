# Monitoring Module Architecture

## Overview
MiniFlow Monitoring modülü, production-grade sistem izleme ve alerting sistemi sağlayan kapsamlı bir modüldür. Real-time sistem metrikleri, component health tracking, alert management ve performance monitoring functionality'si sunar.

## Core Architecture

### 1. Modül Yapısı
```
miniflow/core/monitoring/
├── __init__.py                  # Public API exports
├── system_monitor.py            # SystemMonitor ana sınıfı
├── alert_manager.py             # Alert ve AlertManager
├── config.py                    # Configuration models
├── components.py                # Component monitoring
├── metrics/                     # Metrics collection
│   ├── system_metrics.py       # OS level metrics
│   ├── process_metrics.py      # Process metrics
│   └── custom_metrics.py       # Application metrics
└── strategies/                  # Monitoring strategies
    ├── centralized.py          # Centralized monitoring
    ├── distributed.py          # Distributed monitoring
    └── hybrid.py               # Hybrid approach
```

### 2. Temel Bileşenler

#### SystemMonitor (system_monitor.py)
**Amaç**: Sistem-wide monitoring koordinasyonu ve merkezi kontrol
**Algoritma Mantığı**:
```python
# Real-time Monitoring Loop
class SystemMonitor:
    async def _monitoring_loop(self):
        while self.running:
            # 1. Collect system metrics
            metrics = await self._collect_system_metrics()
            
            # 2. Check component health
            component_health = await self._check_components()
            
            # 3. Evaluate thresholds
            alerts = self._evaluate_alerts(metrics, component_health)
            
            # 4. Process alerts
            await self._process_alerts(alerts)
            
            # 5. Update performance stats
            self._update_performance_stats()
            
            # 6. Wait for next interval
            await asyncio.sleep(self.config.monitoring_interval)
```

**Key Features**:
- **Real-time Monitoring**: Continuous system observation
- **Alert Generation**: Threshold-based alert creation
- **Component Registry**: Track registered components
- **Performance Tracking**: Historical performance data
- **Health Assessment**: Overall system health status

#### AlertManager (alert_manager.py)
**Amaç**: Alert lifecycle yönetimi ve alert processing
**Alert Data Model**:
```python
@dataclass
class Alert:
    level: AlertLevel          # INFO, WARNING, CRITICAL
    type: AlertType           # SYSTEM, COMPONENT, DEVICE, NETWORK
    message: str              # Human-readable description
    timestamp: str            # ISO format timestamp
    component: str            # Source component
    metadata: Dict[str, Any]  # Additional context data

    def to_dict(self) -> Dict[str, Any]:
        # Serialization for API responses
        return {
            "alert_level": self.level.value,
            "alert_type": self.type.value,
            "alert_message": self.message,
            "alert_timestamp": self.timestamp,
            "alert_component": self.component,
            "alert_metadata": self.metadata
        }
```

**Alert Processing Pipeline**:
```python
class AlertManager:
    def process_alert(self, alert: Alert):
        # 1. Validate alert structure
        self._validate_alert(alert)
        
        # 2. Apply alert filters
        if not self._should_process_alert(alert):
            return
        
        # 3. Check for duplicates/grouping
        existing = self._find_similar_alerts(alert)
        if existing:
            self._update_alert_count(existing)
            return
        
        # 4. Store alert
        self._store_alert(alert)
        
        # 5. Trigger notifications
        self._trigger_notifications(alert)
        
        # 6. Update metrics
        self._update_alert_metrics(alert)
```

#### MonitoringConfig (config.py)
**Amaç**: Monitoring system configuration management
**Configuration Structure**:
```python
@dataclass
class MonitoringConfig:
    # Timing Configuration
    monitoring_interval: float = 10.0          # Seconds between checks
    max_monitoring_interval: float = 30.0      # Maximum allowed interval
    min_monitoring_interval: float = 5.0       # Minimum allowed interval
    
    # System Thresholds
    memory_warning_threshold: float = 70.0     # Memory usage % warning
    memory_critical_threshold: float = 85.0    # Memory usage % critical
    cpu_warning_threshold: float = 70.0        # CPU usage % warning
    cpu_critical_threshold: float = 85.0       # CPU usage % critical
    disk_warning_threshold: float = 80.0       # Disk usage % warning
    disk_critical_threshold: float = 90.0      # Disk usage % critical
    
    # Alert Configuration
    max_alerts_history: int = 100              # Maximum stored alerts
    enable_alerts: bool = True                 # Alert system enable/disable
    
    def validate(self) -> List[str]:
        # Configuration validation logic
        errors = []
        if self.memory_warning_threshold >= self.memory_critical_threshold:
            errors.append("Memory warning threshold must be less than critical")
        # ... additional validations
        return errors
```

### 3. Metrics Collection System

#### System Metrics (metrics/system_metrics.py)
**Real-time OS Metrics Collection**:
```python
class SystemMetricsCollector:
    def collect_metrics(self) -> SystemMetrics:
        return SystemMetrics(
            timestamp=datetime.utcnow().isoformat(),
            
            # CPU Metrics
            cpu_percent=psutil.cpu_percent(interval=1),
            cpu_count=psutil.cpu_count(),
            load_average=os.getloadavg(),
            
            # Memory Metrics
            memory=psutil.virtual_memory(),
            swap=psutil.swap_memory(),
            
            # Disk Metrics
            disk_usage=psutil.disk_usage('/'),
            disk_io=psutil.disk_io_counters(),
            
            # Network Metrics
            network_io=psutil.net_io_counters(),
            
            # Process Metrics
            process_count=len(psutil.pids()),
            thread_count=threading.active_count()
        )
```

#### Component Metrics (components.py)
**Application-level Component Monitoring**:
```python
class MonitorableComponent:
    def __init__(self, name: str):
        self.name = name
        self.metrics = ComponentMetrics()
        self.last_health_check = None
        self.status = ComponentStatus.UNKNOWN
    
    def record_request(self, duration: float, success: bool):
        # Track request metrics
        self.metrics.request_count += 1
        if not success:
            self.metrics.error_count += 1
        self.metrics.avg_response_time = self._calculate_avg(duration)
    
    def health_check(self) -> HealthStatus:
        # Component-specific health logic
        memory_usage = self._get_memory_usage()
        error_rate = self.metrics.error_count / max(self.metrics.request_count, 1)
        
        if error_rate > 0.1:  # 10% error rate
            return HealthStatus.CRITICAL
        elif memory_usage > 80:  # 80% memory usage
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY
```

### 4. Alert System Architecture

#### Alert Levels and Types
```python
class AlertLevel(Enum):
    INFO = "INFO"          # Informational
    WARNING = "WARNING"    # Attention needed
    CRITICAL = "CRITICAL"  # Immediate action required

class AlertType(Enum):
    SYSTEM = "SYSTEM"        # OS-level alerts
    COMPONENT = "COMPONENT"  # Application component alerts
    DEVICE = "DEVICE"        # Hardware device alerts
    NETWORK = "NETWORK"      # Network-related alerts
```

#### Alert Processing Strategies
```python
# Strategy Pattern for Alert Processing
class AlertProcessingStrategy:
    def process_alert(self, alert: Alert) -> None:
        raise NotImplementedError

class ImmediateProcessingStrategy(AlertProcessingStrategy):
    def process_alert(self, alert: Alert):
        # Process alert immediately
        self._send_notification(alert)
        self._log_alert(alert)

class BatchProcessingStrategy(AlertProcessingStrategy):
    def process_alert(self, alert: Alert):
        # Add to batch, process periodically
        self.batch.append(alert)
        if len(self.batch) >= self.batch_size:
            self._process_batch(self.batch)

class ThresholdBasedStrategy(AlertProcessingStrategy):
    def process_alert(self, alert: Alert):
        # Only process if meets severity threshold
        if alert.level.value >= self.min_level.value:
            self._process_high_priority(alert)
```

### 5. Monitoring Strategies

#### Centralized Strategy (strategies/centralized.py)
**Approach**: Single monitoring instance handles all components
```python
class CentralizedMonitoringStrategy:
    def __init__(self, monitor: SystemMonitor):
        self.monitor = monitor
        self.components = {}
    
    def register_component(self, component: MonitorableComponent):
        self.components[component.name] = component
        # Central registration
    
    def collect_all_metrics(self):
        # Single point collection
        system_metrics = self.monitor.collect_system_metrics()
        component_metrics = {
            name: comp.collect_metrics() 
            for name, comp in self.components.items()
        }
        return {
            "system": system_metrics,
            "components": component_metrics
        }
```

**Benefits**:
- Simple configuration and management
- Centralized alerting and reporting
- Efficient resource usage
- Easy debugging and troubleshooting

**Drawbacks**:
- Single point of failure
- Scalability limitations
- Network overhead in distributed systems

#### Distributed Strategy (strategies/distributed.py)
**Approach**: Each component monitors itself
```python
class DistributedMonitoringStrategy:
    def __init__(self):
        self.local_components = {}
        self.remote_endpoints = []
    
    def register_component(self, component: MonitorableComponent):
        # Local component registration
        self.local_components[component.name] = component
        component.start_self_monitoring()
    
    def collect_distributed_metrics(self):
        # Collect from multiple sources
        local_metrics = self._collect_local_metrics()
        remote_metrics = await self._collect_remote_metrics()
        return self._aggregate_metrics(local_metrics, remote_metrics)
```

**Benefits**:
- High scalability
- Fault tolerance
- Reduced network overhead
- Independent component lifecycle

**Drawbacks**:
- Complex configuration
- Distributed state management
- Network partition handling
- Coordination complexity

### 6. Performance and Scalability

#### Async Monitoring Loop
```python
class SystemMonitor:
    async def start_monitoring(self):
        # Start multiple concurrent monitoring tasks
        tasks = [
            asyncio.create_task(self._system_metrics_loop()),
            asyncio.create_task(self._component_health_loop()),
            asyncio.create_task(self._alert_processing_loop()),
            asyncio.create_task(self._performance_tracking_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            await self._handle_monitoring_error(e)
    
    async def _system_metrics_loop(self):
        while self.running:
            try:
                metrics = await self._collect_system_metrics_async()
                await self._process_system_metrics(metrics)
            except Exception as e:
                await self._handle_metrics_error(e)
            
            await asyncio.sleep(self.config.monitoring_interval)
```

#### Memory Efficient Alert Storage
```python
class AlertManager:
    def __init__(self, max_alerts: int = 100):
        # Circular buffer for memory efficiency
        self.alerts = collections.deque(maxlen=max_alerts)
        self.alert_index = {}  # Fast lookup
        self.alert_summary = defaultdict(int)
    
    def store_alert(self, alert: Alert):
        # Memory-bounded storage
        if len(self.alerts) >= self.max_alerts:
            # Remove oldest alert from index
            old_alert = self.alerts[0]
            self._remove_from_index(old_alert)
        
        self.alerts.append(alert)
        self._add_to_index(alert)
        self._update_summary(alert)
```

### 7. Integration Architecture

#### Operations Layer Integration
```python
# Business logic integration
class MonitoringOperations:
    def __init__(self):
        self.system_monitor = self._get_system_monitor()
        self.logger = get_logger("monitoring_operations")
    
    def get_system_health(self) -> Dict[str, Any]:
        # Business logic for system health
        # 1. Collect raw metrics
        # 2. Apply business rules
        # 3. Generate health assessment
        # 4. Return structured response
        
    def update_monitoring_config(self, updates: Dict[str, Any]):
        # Business logic for config updates
        # 1. Validate updates
        # 2. Apply changes
        # 3. Restart monitoring if needed
        # 4. Log configuration changes
```

#### API Layer Integration
```python
# FastAPI integration
@router.get("/health")
async def get_system_health():
    # 1. Get business logic result
    health_data = monitoring_ops.get_system_health()
    
    # 2. Transform for API response
    return APIResponse(
        success=True,
        data=health_data,
        message="System health retrieved"
    )
```

### 8. Error Handling and Recovery

#### Multi-Level Error Handling
```python
class SystemMonitor:
    async def _monitoring_loop(self):
        while self.running:
            try:
                await self._monitor_cycle()
            except CriticalSystemError as e:
                # Level 1: Critical system errors
                await self._handle_critical_error(e)
                await self._emergency_shutdown()
                break
            except MonitoringError as e:
                # Level 2: Monitoring specific errors
                await self._handle_monitoring_error(e)
                await self._attempt_recovery()
            except Exception as e:
                # Level 3: Unexpected errors
                await self._handle_unexpected_error(e)
                await asyncio.sleep(self.config.error_retry_interval)
    
    async def _attempt_recovery(self):
        # Recovery strategies
        # 1. Reset failed components
        # 2. Restart monitoring loops
        # 3. Clear corrupted state
        # 4. Notify administrators
```

#### Circuit Breaker Pattern
```python
class MonitoringCircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call_with_breaker(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
```

## Design Patterns Used

### 1. **Observer Pattern**
- SystemMonitor observes component health changes
- AlertManager notifies subscribers on alert events
- Configuration changes propagate to monitoring loops

### 2. **Strategy Pattern**
- Different monitoring strategies (centralized, distributed, hybrid)
- Alert processing strategies (immediate, batch, threshold-based)
- Metrics collection strategies (pull-based, push-based)

### 3. **Factory Pattern**
- Alert creation based on metric thresholds
- Component monitoring instances based on type
- Metric collector instances based on platform

### 4. **Singleton Pattern**
- SystemMonitor instance (shared across application)
- AlertManager instance (central alert coordination)
- MonitoringConfig instance (global configuration)

### 5. **Circuit Breaker Pattern**
- Monitoring loop protection against cascading failures
- Component health check protection
- External service dependency protection

## Architecture Benefits

### Performance
- **Async Operations**: Non-blocking monitoring loops
- **Efficient Metrics**: Minimal overhead data collection
- **Memory Bounded**: Fixed memory footprint regardless of uptime
- **Batch Processing**: Reduced I/O overhead for alerts

### Reliability
- **Fault Tolerance**: Continue monitoring on component failures
- **Recovery Mechanisms**: Automatic error recovery
- **Health Monitoring**: Monitor the monitoring system itself
- **Circuit Breaker**: Prevent cascading failures

### Scalability
- **Distributed Architecture**: Scale across multiple nodes
- **Component-based**: Independent component monitoring
- **Resource Efficient**: Minimal CPU and memory usage
- **Configurable Intervals**: Adjust monitoring frequency

### Maintainability
- **Modular Design**: Clear component boundaries
- **Strategy Pattern**: Easy to add new monitoring approaches
- **Configuration Driven**: Runtime configuration changes
- **Comprehensive Logging**: Full audit trail of monitoring events

### Observability
- **Self-Monitoring**: Monitor the monitoring system performance
- **Rich Metrics**: Detailed system and application metrics
- **Alert Management**: Comprehensive alert lifecycle
- **Health Assessment**: Overall system health status
