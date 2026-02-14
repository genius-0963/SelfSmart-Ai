"""
Metrics collection for SmartShelf AI using Prometheus
"""

import time
import threading
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
import psutil
import os

from .logger import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """Centralized metrics collection system"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self._setup_metrics()
        self._start_system_metrics_collection()
        
    def _setup_metrics(self):
        """Initialize Prometheus metrics"""
        
        # Request metrics
        self.request_count = Counter(
            'smartshelf_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'smartshelf_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Chat metrics
        self.chat_messages_total = Counter(
            'smartshelf_chat_messages_total',
            'Total number of chat messages',
            ['role', 'session_id'],
            registry=self.registry
        )
        
        self.chat_response_duration = Histogram(
            'smartshelf_chat_response_duration_seconds',
            'Chat response duration in seconds',
            ['model_used'],
            registry=self.registry
        )
        
        # Product metrics
        self.product_searches_total = Counter(
            'smartshelf_product_searches_total',
            'Total number of product searches',
            ['source', 'query_type'],
            registry=self.registry
        )
        
        self.product_clicks_total = Counter(
            'smartshelf_product_clicks_total',
            'Total number of product clicks',
            ['source', 'category'],
            registry=self.registry
        )
        
        # User metrics
        self.user_registrations_total = Counter(
            'smartshelf_user_registrations_total',
            'Total number of user registrations',
            registry=self.registry
        )
        
        self.active_users = Gauge(
            'smartshelf_active_users',
            'Number of active users',
            registry=self.registry
        )
        
        # System metrics
        self.system_cpu_usage = Gauge(
            'smartshelf_system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            'smartshelf_system_memory_usage_percent',
            'System memory usage percentage',
            registry=self.registry
        )
        
        self.system_disk_usage = Gauge(
            'smartshelf_system_disk_usage_percent',
            'System disk usage percentage',
            registry=self.registry
        )
        
        # Application metrics
        self.app_info = Info(
            'smartshelf_app_info',
            'Application information',
            registry=self.registry
        )
        
        self.app_info.info({
            'version': os.getenv('APP_VERSION', '1.0.0'),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'build_date': os.getenv('BUILD_DATE', 'unknown')
        })
        
        # Error metrics
        self.error_count = Counter(
            'smartshelf_errors_total',
            'Total number of errors',
            ['error_type', 'component'],
            registry=self.registry
        )
        
        # Database metrics
        self.db_connections_active = Gauge(
            'smartshelf_db_connections_active',
            'Number of active database connections',
            registry=self.registry
        )
        
        self.db_query_duration = Histogram(
            'smartshelf_db_query_duration_seconds',
            'Database query duration in seconds',
            ['operation'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits_total = Counter(
            'smartshelf_cache_hits_total',
            'Total number of cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses_total = Counter(
            'smartshelf_cache_misses_total',
            'Total number of cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        # Custom metrics storage
        self.custom_metrics = defaultdict(float)
        self.custom_labels = defaultdict(dict)
        
    def _start_system_metrics_collection(self):
        """Start background thread for system metrics collection"""
        def collect_system_metrics():
            while True:
                try:
                    # CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    self.system_cpu_usage.set(cpu_percent)
                    
                    # Memory usage
                    memory = psutil.virtual_memory()
                    self.system_memory_usage.set(memory.percent)
                    
                    # Disk usage
                    disk = psutil.disk_usage('/')
                    disk_percent = (disk.used / disk.total) * 100
                    self.system_disk_usage.set(disk_percent)
                    
                except Exception as e:
                    logger.error(f"Error collecting system metrics: {e}")
                
                time.sleep(30)  # Collect every 30 seconds
        
        thread = threading.Thread(target=collect_system_metrics, daemon=True)
        thread.start()
    
    def increment_request_count(self, method: str, endpoint: str, status_code: int):
        """Increment request count metric"""
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
    
    def record_request_duration(self, method: str, endpoint: str, duration: float):
        """Record request duration metric"""
        self.request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def increment_chat_messages(self, role: str, session_id: str):
        """Increment chat messages metric"""
        self.chat_messages_total.labels(
            role=role,
            session_id=session_id
        ).inc()
    
    def record_chat_response_duration(self, model_used: str, duration: float):
        """Record chat response duration metric"""
        self.chat_response_duration.labels(
            model_used=model_used
        ).observe(duration)
    
    def increment_product_searches(self, source: str, query_type: str):
        """Increment product searches metric"""
        self.product_searches_total.labels(
            source=source,
            query_type=query_type
        ).inc()
    
    def increment_product_clicks(self, source: str, category: str):
        """Increment product clicks metric"""
        self.product_clicks_total.labels(
            source=source,
            category=category
        ).inc()
    
    def increment_user_registrations(self):
        """Increment user registrations metric"""
        self.user_registrations_total.inc()
    
    def set_active_users(self, count: int):
        """Set active users metric"""
        self.active_users.set(count)
    
    def increment_errors(self, error_type: str, component: str):
        """Increment error count metric"""
        self.error_count.labels(
            error_type=error_type,
            component=component
        ).inc()
    
    def set_db_connections(self, count: int):
        """Set database connections metric"""
        self.db_connections_active.set(count)
    
    def record_db_query_duration(self, operation: str, duration: float):
        """Record database query duration metric"""
        self.db_query_duration.labels(
            operation=operation
        ).observe(duration)
    
    def increment_cache_hits(self, cache_type: str):
        """Increment cache hits metric"""
        self.cache_hits_total.labels(
            cache_type=cache_type
        ).inc()
    
    def increment_cache_misses(self, cache_type: str):
        """Increment cache misses metric"""
        self.cache_misses_total.labels(
            cache_type=cache_type
        ).inc()
    
    def set_custom_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a custom metric"""
        self.custom_metrics[name] = value
        if labels:
            self.custom_labels[name] = labels
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics"""
        return {
            'custom_metrics': dict(self.custom_metrics),
            'custom_labels': dict(self.custom_labels),
            'system_info': {
                'cpu_usage': self.system_cpu_usage._value.get(),
                'memory_usage': self.system_memory_usage._value.get(),
                'disk_usage': self.system_disk_usage._value.get(),
            }
        }
    
    def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        return generate_latest(self.registry).decode('utf-8')


# Global metrics instance
metrics = MetricsCollector()


class MetricsMiddleware:
    """FastAPI middleware for automatic metrics collection"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Create response wrapper to capture status
        response_sent = False
        
        async def send_wrapper(message):
            nonlocal response_sent
            if message["type"] == "http.response.start" and not response_sent:
                response_sent = True
                
                # Record metrics
                duration = time.time() - start_time
                method = scope["method"]
                path = scope["path"]
                status = message["status"]
                
                metrics.increment_request_count(method, path, status)
                metrics.record_request_duration(method, path, duration)
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


def track_performance(operation: str, labels: Dict[str, str] = None):
    """Decorator to track function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record metric
                metric_name = f"smartshelf_{operation}_duration_seconds"
                metrics.set_custom_metric(metric_name, duration, labels)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # Record error metric
                metrics.increment_errors(
                    error_type=type(e).__name__,
                    component=operation
                )
                
                # Record duration even for errors
                metric_name = f"smartshelf_{operation}_duration_seconds"
                metrics.set_custom_metric(metric_name, duration, labels)
                
                raise
        
        return wrapper
    return decorator


class PerformanceTracker:
    """Context manager for tracking performance"""
    
    def __init__(self, operation: str, labels: Dict[str, str] = None):
        self.operation = operation
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        # Record metric
        metric_name = f"smartshelf_{self.operation}_duration_seconds"
        metrics.set_custom_metric(metric_name, duration, self.labels)
        
        if exc_type:
            metrics.increment_errors(
                error_type=exc_type.__name__,
                component=self.operation
            )
