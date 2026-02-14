"""
SmartShelf AI - Metrics Service
Real-time performance monitoring and analytics
"""

import time
import psutil
import asyncio
from typing import Dict, Any, List
from collections import defaultdict, deque
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MetricsService:
    """Comprehensive metrics collection and monitoring"""
    
    def __init__(self):
        self.request_counts = defaultdict(int)
        self.response_times = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.start_time = time.time()
        self.active_connections = 0
        self.user_sessions = defaultdict(dict)
        self.intent_counts = defaultdict(int)
        self.product_searches = defaultdict(int)
        
        # Performance tracking
        self.cpu_usage = deque(maxlen=60)  # Last 60 samples
        self.memory_usage = deque(maxlen=60)
        self.disk_usage = deque(maxlen=60)
        
        # Start background monitoring
        self._monitoring_task = None
    
    def record_request(self, endpoint: str, method: str, response_time: float, 
                      status_code: int, user_id: str = None, intent: str = None):
        """Record request metrics"""
        key = f"{method}:{endpoint}"
        self.request_counts[key] += 1
        self.response_times.append(response_time)
        
        if status_code >= 400:
            self.error_counts[key] += 1
        
        if intent:
            self.intent_counts[intent] += 1
        
        if user_id:
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {
                    'requests': 0,
                    'first_seen': datetime.now(),
                    'last_seen': datetime.now()
                }
            self.user_sessions[user_id]['requests'] += 1
            self.user_sessions[user_id]['last_seen'] = datetime.now()
    
    def record_websocket_connection(self, action: str, session_id: str):
        """Record WebSocket connection metrics"""
        if action == "connect":
            self.active_connections += 1
        elif action == "disconnect":
            self.active_connections = max(0, self.active_connections - 1)
    
    def record_product_search(self, query: str, results_count: int):
        """Record product search metrics"""
        self.product_searches["total_searches"] += 1
        self.product_searches["total_results"] += results_count
        self.product_searches["avg_results"] = (
            self.product_searches["total_results"] / self.product_searches["total_searches"]
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        # Calculate response time percentiles
        if self.response_times:
            sorted_times = sorted(self.response_times)
            avg_response_time = sum(self.response_times) / len(self.response_times)
            p50_response_time = sorted_times[len(sorted_times) // 2]
            p95_response_time = sorted_times[int(len(sorted_times) * 0.95)]
            p99_response_time = sorted_times[int(len(sorted_times) * 0.99)]
        else:
            avg_response_time = p50_response_time = p95_response_time = p99_response_time = 0
        
        # System metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Update tracking
        self.cpu_usage.append(cpu_percent)
        self.memory_usage.append(memory.percent)
        self.disk_usage.append(disk.percent)
        
        # Calculate error rate
        total_requests = sum(self.request_counts.values())
        total_errors = sum(self.error_counts.values())
        error_rate = total_errors / max(total_requests, 1)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": error_rate,
            "active_connections": self.active_connections,
            "unique_users": len(self.user_sessions),
            
            # Response time metrics
            "avg_response_time_ms": avg_response_time * 1000,
            "p50_response_time_ms": p50_response_time * 1000,
            "p95_response_time_ms": p95_response_time * 1000,
            "p99_response_time_ms": p99_response_time * 1000,
            
            # System metrics
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3),
            
            # Request metrics
            "requests_per_endpoint": dict(self.request_counts),
            "errors_per_endpoint": dict(self.error_counts),
            "intent_distribution": dict(self.intent_counts),
            
            # Product search metrics
            "product_searches": dict(self.product_searches),
            
            # Performance trends
            "cpu_trend": list(self.cpu_usage)[-10:],  # Last 10 samples
            "memory_trend": list(self.memory_usage)[-10:],
            "disk_trend": list(self.disk_usage)[-10:]
        }
    
    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics for specific user"""
        if user_id not in self.user_sessions:
            return {"error": "User not found"}
        
        user_data = self.user_sessions[user_id]
        session_duration = (datetime.now() - user_data['first_seen']).total_seconds()
        
        return {
            "user_id": user_id,
            "total_requests": user_data['requests'],
            "session_duration_seconds": session_duration,
            "requests_per_minute": user_data['requests'] / max(session_duration / 60, 1),
            "first_seen": user_data['first_seen'].isoformat(),
            "last_seen": user_data['last_seen'].isoformat()
        }
    
    def get_top_intents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top intents by frequency"""
        sorted_intents = sorted(self.intent_counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {"intent": intent, "count": count, "percentage": (count / sum(self.intent_counts.values())) * 100}
            for intent, count in sorted_intents[:limit]
        ]
    
    def get_endpoint_performance(self) -> Dict[str, Any]:
        """Get performance metrics per endpoint"""
        endpoint_stats = {}
        
        for endpoint_key in self.request_counts:
            method, endpoint = endpoint_key.split(":", 1)
            requests = self.request_counts[endpoint_key]
            errors = self.error_counts.get(endpoint_key, 0)
            
            # Calculate average response time for this endpoint
            endpoint_response_times = [
                rt for rt in self.response_times 
                if rt > 0  # This would need more sophisticated tracking in production
            ]
            
            avg_time = sum(endpoint_response_times) / len(endpoint_response_times) if endpoint_response_times else 0
            
            endpoint_stats[endpoint_key] = {
                "method": method,
                "endpoint": endpoint,
                "requests": requests,
                "errors": errors,
                "error_rate": errors / max(requests, 1),
                "avg_response_time_ms": avg_time * 1000
            }
        
        return endpoint_stats
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)"""
        self.request_counts.clear()
        self.response_times.clear()
        self.error_counts.clear()
        self.intent_counts.clear()
        self.product_searches.clear()
        self.start_time = time.time()
    
    async def start_monitoring(self):
        """Start background system monitoring"""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitor_system())
    
    async def _monitor_system(self):
        """Background system monitoring task"""
        while True:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                self.cpu_usage.append(cpu_percent)
                self.memory_usage.append(memory.percent)
                self.disk_usage.append(disk.percent)
                
                # Clean up old user sessions (inactive for more than 1 hour)
                cutoff_time = datetime.now() - timedelta(hours=1)
                inactive_users = [
                    user_id for user_id, data in self.user_sessions.items()
                    if data['last_seen'] < cutoff_time
                ]
                
                for user_id in inactive_users:
                    del self.user_sessions[user_id]
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(60)
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None

# Global metrics service instance
metrics_service = MetricsService()
