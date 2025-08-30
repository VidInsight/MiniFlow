"""
MiniFlow Execution Engine Konfigürasyonu
Execution engine ayarları ve performans parametreleri
"""

ENGINE_CONFIG = {
    "max_concurrent_tasks": 10,
    "task_timeout_seconds": 300,  # 5 dakika
    "retry_attempts": 3,
    "retry_delay_seconds": 1.0,
    "enable_task_queue": True,
    "queue_max_size": 1000,
    "worker_pool_size": 4,
    "enable_metrics": True,
    "metrics_interval_seconds": 30.0,
    "execution_mode": "async",  # async, sync, hybrid
    "enable_profiling": False,
    "profiling_output_dir": "logs/profiling"
}
