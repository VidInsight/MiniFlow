# Monitoring Usage Examples

## Basic System Monitoring

### 1. Starting System Monitoring

```python
from miniflow.core.monitoring import SystemMonitor, MonitoringConfig

# Basic monitoring setup
config = MonitoringConfig(
    monitoring_interval=10.0,  # Check every 10 seconds
    memory_warning_threshold=70.0,
    memory_critical_threshold=85.0,
    cpu_warning_threshold=70.0,
    cpu_critical_threshold=85.0
)

# Create and start monitor
monitor = SystemMonitor(config)
await monitor.start()

# Monitor will run continuously in background
print(f"Monitoring started with {monitor.get_component_count()} components")
```

### 2. Getting System Metrics

```python
from miniflow.core.monitoring import get_system_monitor_instance

# Get global monitor instance
monitor = get_system_monitor_instance()

# Get current system metrics
metrics = monitor.get_system_metrics()
print(f"CPU Usage: {metrics['system_cpu_percent']}%")
print(f"Memory Usage: {metrics['system_memory_percent']}%")
print(f"Disk Usage: {metrics['disk_usage_percent']}%")
print(f"Active Threads: {metrics['active_threads']}")

# Check monitoring uptime
uptime = monitor.get_system_uptime()
print(f"Monitoring running for: {uptime:.2f} seconds")
```

### 3. Basic Alert Handling

```python
from miniflow.core.monitoring import AlertLevel, AlertType

monitor = get_system_monitor_instance()

# Get recent alerts
recent_alerts = monitor.alert_manager.get_recent_alerts(10)
for alert in recent_alerts:
    print(f"[{alert.level.value}] {alert.message}")
    print(f"  Component: {alert.component}")
    print(f"  Time: {alert.timestamp}")
    print(f"  Details: {alert.metadata}")

# Get alert summary
summary = monitor.alert_manager.get_alert_summary()
print(f"Total alerts: {len(monitor.alert_manager.alerts)}")
print(f"Critical: {summary.get('CRITICAL', 0)}")
print(f"Warnings: {summary.get('WARNING', 0)}")
```

## Advanced Monitoring Usage

### 4. Custom Component Monitoring

```python
from miniflow.core.monitoring import MonitorableComponent, ComponentMetrics


class DatabaseComponent(MonitorableComponent):
    def __init__(self, name: str, db_connection):
        super().__init__(name)
        self.db = db_connection
        self.connection_pool_size = 10

    def health_check(self):
        try:
            # Check database connectivity
            self.db.ping()

            # Check connection pool
            active_connections = self.db.get_active_connections()
            pool_usage = (active_connections / self.connection_pool_size) * 100

            # Assess health based on metrics
            if pool_usage > 90:
                return {
                    "status": "CRITICAL",
                    "message": "Database connection pool nearly exhausted",
                    "details": {"pool_usage": pool_usage}
                }
            elif pool_usage > 70:
                return {
                    "status": "WARNING",
                    "message": "High database connection pool usage",
                    "details": {"pool_usage": pool_usage}
                }
            else:
                return {
                    "status": "HEALTHY",
                    "message": "Database operating normally",
                    "details": {"pool_usage": pool_usage}
                }

        except Exception as e:
            return {
                "status": "CRITICAL",
                "message": f"Database health check failed: {str(e)}",
                "details": {"error": str(e)}
            }


# Register and use custom component
db_component = DatabaseComponent("primary_database", db_connection)
monitor.register_component(db_component)


# Monitor database operations
def process_database_query(query):
    start_time = time.time()
    try:
        result = db.execute(query)
        duration = time.time() - start_time

        # Record successful operation
        db_component.record_request(duration, success=True)
        return result

    except Exception as e:
        duration = time.time() - start_time

        # Record failed operation
        db_component.record_request(duration, success=False)
        raise
```

### 5. Real-time Metrics Dashboard

```python
import asyncio
from miniflow.core.monitoring import get_system_monitor_instance


class MonitoringDashboard:
    def __init__(self):
        self.monitor = get_system_monitor_instance()
        self.running = False

    async def start_dashboard(self):
        self.running = True
        while self.running:
            await self.update_display()
            await asyncio.sleep(5)  # Update every 5 seconds

    async def update_display(self):
        # Clear screen (simple version)
        print("\033[2J\033[H")  # ANSI clear screen

        # Display system metrics
        metrics = self.monitor.get_system_metrics()
        print("=== MiniFlow System Monitor ===")
        print(f"Timestamp: {metrics.get('timestamp', 'N/A')}")
        print(f"CPU Usage: {metrics.get('system_cpu_percent', 0):.1f}%")
        print(f"Memory Usage: {metrics.get('system_memory_percent', 0):.1f}%")
        print(f"Disk Usage: {metrics.get('disk_usage_percent', 0):.1f}%")
        print(f"Active Threads: {metrics.get('active_threads', 0)}")
        print(f"Total Processes: {metrics.get('total_processes', 0)}")

        # Display component health
        components = self.monitor.get_all_components_metrics()
        print("\n=== Component Health ===")
        for name, component_metrics in components.items():
            status = component_metrics.get('component_health', 'UNKNOWN')
            print(f"{name}: {status}")

        # Display recent alerts
        alerts = self.monitor.alert_manager.get_recent_alerts(5)
        print("\n=== Recent Alerts ===")
        if alerts:
            for alert in alerts[-5:]:  # Last 5 alerts
                print(f"[{alert.level.value}] {alert.message[:50]}...")
        else:
            print("No recent alerts")

        # Display monitoring status
        uptime = self.monitor.get_system_uptime()
        print(f"\nMonitoring Uptime: {uptime:.2f}s")


# Start dashboard
dashboard = MonitoringDashboard()
await dashboard.start_dashboard()
```

## Production Monitoring Scenarios

### 6. High-Load System Monitoring

```python
from miniflow.core.monitoring import MonitoringConfig, SystemMonitor

# Production-grade configuration
production_config = MonitoringConfig(
    monitoring_interval=5.0,  # More frequent checks

    # Tighter thresholds for production
    memory_warning_threshold=60.0,
    memory_critical_threshold=75.0,
    cpu_warning_threshold=60.0,
    cpu_critical_threshold=80.0,
    disk_warning_threshold=70.0,
    disk_critical_threshold=85.0,

    # Extended alert history
    max_alerts_history=500,
    enable_alerts=True
)


class ProductionMonitoringService:
    def __init__(self):
        self.monitor = SystemMonitor(production_config)
        self.performance_history = []

    async def start_production_monitoring(self):
        # Start monitoring with enhanced error handling
        try:
            await self.monitor.start()
        except Exception as e:
            # Log to external monitoring service
            await self.notify_operations_team(
                f"Critical: Monitoring system failed to start: {e}"
            )
            raise

    async def collect_performance_data(self):
        """Collect and store performance data for analysis"""
        while True:
            try:
                metrics = self.monitor.get_system_metrics()
                timestamp = datetime.utcnow()

                # Store performance data
                perf_data = {
                    "timestamp": timestamp,
                    "cpu_usage": metrics.get('system_cpu_percent', 0),
                    "memory_usage": metrics.get('system_memory_percent', 0),
                    "disk_usage": metrics.get('disk_usage_percent', 0),
                    "active_connections": self.get_active_connections(),
                    "request_rate": self.get_current_request_rate()
                }

                self.performance_history.append(perf_data)

                # Keep only last 24 hours of data
                cutoff_time = timestamp - timedelta(hours=24)
                self.performance_history = [
                    data for data in self.performance_history
                    if data["timestamp"] > cutoff_time
                ]

                # Check for performance trends
                await self.analyze_performance_trends()

            except Exception as e:
                print(f"Error collecting performance data: {e}")

            await asyncio.sleep(60)  # Collect every minute

    async def analyze_performance_trends(self):
        """Analyze performance trends and predict issues"""
        if len(self.performance_history) < 10:
            return

        # Get recent data
        recent_data = self.performance_history[-10:]

        # Calculate trends
        cpu_trend = self.calculate_trend([d['cpu_usage'] for d in recent_data])
        memory_trend = self.calculate_trend([d['memory_usage'] for d in recent_data])

        # Predict potential issues
        if cpu_trend > 5:  # CPU increasing by 5% per measurement
            await self.create_predictive_alert(
                "CPU usage trending upward",
                {"trend": cpu_trend, "current": recent_data[-1]['cpu_usage']}
            )

        if memory_trend > 3:  # Memory increasing by 3% per measurement
            await self.create_predictive_alert(
                "Memory usage trending upward",
                {"trend": memory_trend, "current": recent_data[-1]['memory_usage']}
            )
```

### 7. Microservices Monitoring

```python
from miniflow.core.monitoring import MonitorableComponent


class MicroserviceMonitor:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.component = MonitorableComponent(service_name)
        self.monitor = get_system_monitor_instance()
        self.monitor.register_component(self.component)

        # Service-specific metrics
        self.request_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "min_response_time": float('inf'),
            "max_response_time": 0.0
        }

    def record_api_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """Record API request metrics"""
        self.request_metrics["total_requests"] += 1

        # Track success/failure
        if 200 <= status_code < 400:
            self.request_metrics["successful_requests"] += 1
            success = True
        else:
            self.request_metrics["failed_requests"] += 1
            success = False

        # Update response time metrics
        self.request_metrics["min_response_time"] = min(
            self.request_metrics["min_response_time"], duration
        )
        self.request_metrics["max_response_time"] = max(
            self.request_metrics["max_response_time"], duration
        )

        # Calculate rolling average
        total_requests = self.request_metrics["total_requests"]
        current_avg = self.request_metrics["avg_response_time"]
        self.request_metrics["avg_response_time"] = (
                (current_avg * (total_requests - 1) + duration) / total_requests
        )

        # Record in component
        self.component.record_request(duration, success)

        # Create alerts for issues
        if not success and status_code >= 500:
            self.create_error_alert(endpoint, method, status_code, duration)

        if duration > 5.0:  # Slow request threshold
            self.create_performance_alert(endpoint, method, duration)

    def create_error_alert(self, endpoint: str, method: str, status_code: int, duration: float):
        """Create alert for service errors"""
        alert = Alert(
            level=AlertLevel.WARNING if status_code < 500 else AlertLevel.CRITICAL,
            type=AlertType.COMPONENT,
            message=f"Service error in {self.service_name}",
            component=self.service_name,
            metadata={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time": duration,
                "error_rate": self.get_error_rate()
            }
        )
        self.monitor.alert_manager.process_alert(alert)

    def get_error_rate(self) -> float:
        """Calculate current error rate"""
        total = self.request_metrics["total_requests"]
        if total == 0:
            return 0.0
        return (self.request_metrics["failed_requests"] / total) * 100


# Usage in FastAPI application
from fastapi import FastAPI, Request
import time

app = FastAPI()
service_monitor = MicroserviceMonitor("user-service")


@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    service_monitor.record_api_request(
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
        duration=duration
    )

    return response
```

## Operations Integration

### 8. Monitoring Operations Usage

```python
from miniflow.app.routes.bfa.operations.monitoring_operations import MonitoringOperations


class SystemHealthService:
    def __init__(self):
        self.monitoring_ops = MonitoringOperations()

    async def get_comprehensive_health_report(self):
        """Generate comprehensive system health report"""
        try:
            # Get system metrics
            system_metrics = self.monitoring_ops.get_system_metrics()

            # Get component health
            components_metrics = self.monitoring_ops.get_all_components_metrics()

            # Get alert summary
            alert_summary = self.monitoring_ops.get_alert_summary()

            # Get monitoring status
            monitoring_status = self.monitoring_ops.get_monitoring_status()

            # Analyze overall health
            overall_health = self.analyze_overall_health(
                system_metrics, components_metrics, alert_summary
            )

            return {
                "overall_health": overall_health,
                "system_metrics": system_metrics,
                "components": components_metrics,
                "alerts": alert_summary,
                "monitoring_status": monitoring_status,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            # Fallback health check
            return {
                "overall_health": "UNKNOWN",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def analyze_overall_health(self, system_metrics, components_metrics, alert_summary):
        """Analyze overall system health"""
        # Check system metrics
        cpu_usage = system_metrics.get('system_cpu_percent', 0)
        memory_usage = system_metrics.get('system_memory_percent', 0)
        disk_usage = system_metrics.get('disk_usage_percent', 0)

        # System health assessment
        if cpu_usage > 85 or memory_usage > 85 or disk_usage > 90:
            return "CRITICAL"

        # Check component health
        critical_components = sum(
            1 for comp in components_metrics.values()
            if comp.get('component_health') == 'CRITICAL'
        )

        if critical_components > 0:
            return "CRITICAL"

        # Check alerts
        critical_alerts = alert_summary.get('critical_count', 0)
        if critical_alerts > 0:
            return "WARNING"

        warning_components = sum(
            1 for comp in components_metrics.values()
            if comp.get('component_health') == 'WARNING'
        )

        if warning_components > 0 or cpu_usage > 70 or memory_usage > 70:
            return "WARNING"

        return "HEALTHY"

    async def update_monitoring_configuration(self, updates: dict):
        """Update monitoring configuration"""
        try:
            # Validate updates
            self.validate_config_updates(updates)

            # Apply updates
            updated_config = self.monitoring_ops.update_monitoring_config(updates)

            # Log configuration change
            print(f"Monitoring configuration updated: {updates}")

            return {
                "success": True,
                "updated_config": updated_config,
                "message": "Configuration updated successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update configuration"
            }
```

### 9. Alert Management Operations
```python
class AlertManagementService:
    def __init__(self):
        self.monitoring_ops = MonitoringOperations()
    
    async def setup_alert_rules(self):
        """Setup custom alert rules"""
        alert_rules = [
            {
                "name": "High CPU Usage",
                "condition": "cpu_usage > 80",
                "level": "WARNING",
                "cooldown": 300  # 5 minutes
            },
            {
                "name": "Critical CPU Usage", 
                "condition": "cpu_usage > 90",
                "level": "CRITICAL",
                "cooldown": 60   # 1 minute
            },
            {
                "name": "High Error Rate",
                "condition": "error_rate > 5",
                "level": "WARNING",
                "cooldown": 180  # 3 minutes
            }
        ]
        
        for rule in alert_rules:
            await self.register_alert_rule(rule)
    
    async def process_alert_workflow(self, alert):
        """Process alert through workflow"""
        # 1. Validate alert
        if not self.is_valid_alert(alert):
            return
        
        # 2. Check if alert should be suppressed
        if self.should_suppress_alert(alert):
            return
        
        # 3. Enrich alert with additional context
        enriched_alert = await self.enrich_alert(alert)
        
        # 4. Route alert to appropriate handlers
        await self.route_alert(enriched_alert)
        
        # 5. Update alert metrics
        self.update_alert_metrics(enriched_alert)
    
    async def enrich_alert(self, alert):
        """Enrich alert with additional context"""
        # Add system context
        system_metrics = self.monitoring_ops.get_system_metrics()
        
        # Add component context
        if alert.component:
            component_metrics = self.monitoring_ops.get_component_metrics(alert.component)
            alert.metadata['component_metrics'] = component_metrics
        
        # Add historical context
        similar_alerts = self.monitoring_ops.get_alerts_by_component(alert.component)
        alert.metadata['recent_similar_alerts'] = len(similar_alerts)
        
        # Add system load context
        alert.metadata['system_load'] = {
            'cpu': system_metrics.get('system_cpu_percent'),
            'memory': system_metrics.get('system_memory_percent'),
            'timestamp': system_metrics.get('timestamp')
        }
        
        return alert
    
    async def route_alert(self, alert):
        """Route alert to appropriate handlers"""
        if alert.level == AlertLevel.CRITICAL:
            # Immediate notification for critical alerts
            await self.send_immediate_notification(alert)
            await self.create_incident_ticket(alert)
        
        elif alert.level == AlertLevel.WARNING:
            # Batch notification for warnings
            await self.add_to_warning_batch(alert)
        
        # Always log alert
        await self.log_alert(alert)
    
    async def generate_alert_report(self, time_period: str = "24h"):
        """Generate alert analysis report"""
        # Get alerts for time period
        all_alerts = self.monitoring_ops.get_all_alerts()
        
        # Filter by time period
        cutoff_time = self.calculate_cutoff_time(time_period)
        period_alerts = [
            alert for alert in all_alerts
            if datetime.fromisoformat(alert['alert_timestamp']) > cutoff_time
        ]
        
        # Analyze alerts
        analysis = {
            "time_period": time_period,
            "total_alerts": len(period_alerts),
            "alerts_by_level": self.group_alerts_by_level(period_alerts),
            "alerts_by_component": self.group_alerts_by_component(period_alerts),
            "top_alert_sources": self.get_top_alert_sources(period_alerts),
            "alert_frequency": self.calculate_alert_frequency(period_alerts),
            "resolution_stats": self.calculate_resolution_stats(period_alerts)
        }
        
        return analysis
```

## Testing and Development

### 10. Mock Monitoring for Testing

```python
import pytest
from unittest.mock import Mock, patch
from miniflow.core.monitoring import SystemMonitor, MonitoringConfig


class TestMonitoringIntegration:
    @pytest.fixture
    def mock_system_monitor(self):
        """Mock system monitor for testing"""
        monitor = Mock(spec=SystemMonitor)

        # Mock system metrics
        monitor.get_system_metrics.return_value = {
            "timestamp": "2023-01-01T12:00:00",
            "system_cpu_percent": 45.0,
            "system_memory_percent": 60.0,
            "disk_usage_percent": 30.0,
            "active_threads": 10,
            "total_processes": 25
        }

        # Mock component metrics
        monitor.get_all_components_metrics.return_value = {
            "database": {
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

    def test_health_check_service(self, mock_system_monitor):
        """Test health check service with mocked monitoring"""
        with patch('miniflow.core.monitoring.get_system_monitor_instance',
                   return_value=mock_system_monitor):
            health_service = SystemHealthService()
            health_report = health_service.get_comprehensive_health_report()

            assert health_report["overall_health"] == "HEALTHY"
            assert health_report["system_metrics"]["system_cpu_percent"] == 45.0
            mock_system_monitor.get_system_metrics.assert_called_once()
```

### 11. Development Monitoring Setup
```python
def setup_development_monitoring():
    """Setup monitoring for development environment"""
    # Relaxed thresholds for development
    dev_config = MonitoringConfig(
        monitoring_interval=30.0,  # Less frequent checks
        memory_warning_threshold=80.0,
        memory_critical_threshold=90.0,
        cpu_warning_threshold=80.0,
        cpu_critical_threshold=90.0,
        max_alerts_history=50,     # Smaller history
        enable_alerts=True
    )
    
    # Create monitor
    monitor = SystemMonitor(dev_config)
    
    # Add development-specific components
    dev_component = MonitorableComponent("development_tools")
    monitor.register_component(dev_component)
    
    return monitor

# Usage in development
if __name__ == "__main__":
    import asyncio
    
    # Setup development monitoring
    dev_monitor = setup_development_monitoring()
    
    # Start monitoring
    asyncio.run(dev_monitor.start())
```

These examples demonstrate the comprehensive monitoring capabilities of MiniFlow, from basic system monitoring to complex production scenarios with custom components, alert management, and operations integration.
