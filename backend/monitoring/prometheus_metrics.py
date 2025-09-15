import time
import logging
from prometheus_client import (
    Counter, Histogram, Gauge, Summary, 
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, multiprocess
)
from functools import wraps
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Create registry for metrics
registry = CollectorRegistry()

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

# LLM metrics
LLM_REQUESTS = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['provider', 'model', 'operation'],
    registry=registry
)

LLM_TOKENS_USED = Counter(
    'llm_tokens_used_total',
    'Total tokens used by LLM',
    ['provider', 'model', 'operation'],
    registry=registry
)

LLM_REQUEST_DURATION = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['provider', 'model'],
    registry=registry
)

LLM_ERRORS = Counter(
    'llm_errors_total',
    'Total LLM errors',
    ['provider', 'model', 'error_type'],
    registry=registry
)

# Node metrics
NODE_OPERATIONS = Counter(
    'node_operations_total',
    'Total node operations',
    ['operation', 'node_type'],
    registry=registry
)

NODE_COUNT = Gauge(
    'node_count_total',
    'Total number of nodes',
    ['node_type', 'status'],
    registry=registry
)

# Conflict metrics
CONFLICT_OPERATIONS = Counter(
    'conflict_operations_total',
    'Total conflict operations',
    ['operation', 'severity'],
    registry=registry
)

CONFLICT_COUNT = Gauge(
    'conflict_count_total',
    'Total number of conflicts',
    ['severity', 'status'],
    registry=registry
)

# Cache metrics
CACHE_OPERATIONS = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'cache_type'],
    registry=registry
)

CACHE_HIT_RATIO = Gauge(
    'cache_hit_ratio',
    'Cache hit ratio',
    ['cache_type'],
    registry=registry
)

# Database metrics
DB_OPERATIONS = Counter(
    'database_operations_total',
    'Total database operations',
    ['operation', 'table'],
    registry=registry
)

DB_QUERY_DURATION = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    registry=registry
)

# Authentication metrics
AUTH_OPERATIONS = Counter(
    'auth_operations_total',
    'Total authentication operations',
    ['operation', 'status'],
    registry=registry
)

AUTH_FAILURES = Counter(
    'auth_failures_total',
    'Total authentication failures',
    ['operation', 'reason'],
    registry=registry
)

# Rate limiting metrics
RATE_LIMIT_HITS = Counter(
    'rate_limit_hits_total',
    'Total rate limit hits',
    ['action', 'identifier'],
    registry=registry
)

# WebSocket metrics
WEBSOCKET_CONNECTIONS = Gauge(
    'websocket_connections_total',
    'Total WebSocket connections',
    registry=registry
)

WEBSOCKET_MESSAGES = Counter(
    'websocket_messages_total',
    'Total WebSocket messages',
    ['message_type'],
    registry=registry
)

# System metrics
SYSTEM_MEMORY_USAGE = Gauge(
    'system_memory_bytes',
    'System memory usage in bytes',
    registry=registry
)

SYSTEM_CPU_USAGE = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage',
    registry=registry
)

# Custom metrics
ACTIVE_USERS = Gauge(
    'active_users_total',
    'Total active users',
    registry=registry
)

TOKEN_USAGE_BY_USER = Counter(
    'token_usage_by_user_total',
    'Token usage by user',
    ['user_id', 'model'],
    registry=registry
)

class MetricsCollector:
    """Collector for custom metrics"""
    
    def __init__(self):
        self.start_time = time.time()
    
    def update_node_metrics(self, nodes: list):
        """Update node-related metrics"""
        # Count nodes by type and status
        node_counts = {}
        for node in nodes:
            node_type = node.get('node_type', 'unknown')
            status = node.get('status', 'unknown')
            key = (node_type, status)
            node_counts[key] = node_counts.get(key, 0) + 1
        
        # Update gauges
        for (node_type, status), count in node_counts.items():
            NODE_COUNT.labels(node_type=node_type, status=status).set(count)
    
    def update_conflict_metrics(self, conflicts: list):
        """Update conflict-related metrics"""
        # Count conflicts by severity and status
        conflict_counts = {}
        for conflict in conflicts:
            severity = conflict.get('severity', 'unknown')
            status = conflict.get('status', 'unknown')
            key = (severity, status)
            conflict_counts[key] = conflict_counts.get(key, 0) + 1
        
        # Update gauges
        for (severity, status), count in conflict_counts.items():
            CONFLICT_COUNT.labels(severity=severity, status=status).set(count)
    
    def update_cache_metrics(self, cache_stats: Dict[str, Any]):
        """Update cache-related metrics"""
        if 'redis_info' in cache_stats:
            redis_info = cache_stats['redis_info']
            
            # Update cache hit ratio
            hits = redis_info.get('keyspace_hits', 0)
            misses = redis_info.get('keyspace_misses', 0)
            total = hits + misses
            
            if total > 0:
                hit_ratio = hits / total
                CACHE_HIT_RATIO.labels(cache_type='redis').set(hit_ratio)
    
    def update_system_metrics(self):
        """Update system metrics"""
        try:
            import psutil
            
            # Memory usage
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY_USAGE.set(memory.used)
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_CPU_USAGE.set(cpu_percent)
            
        except ImportError:
            logger.warning("psutil not available, skipping system metrics")
    
    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - self.start_time

# Global metrics collector
metrics_collector = MetricsCollector()

def track_request_metrics(method: str, endpoint: str, status: int, duration: float):
    """Track HTTP request metrics"""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

def track_llm_metrics(provider: str, model: str, operation: str, tokens: int, duration: float, success: bool = True):
    """Track LLM metrics"""
    if success:
        LLM_REQUESTS.labels(provider=provider, model=model, operation=operation).inc()
        LLM_TOKENS_USED.labels(provider=provider, model=model, operation=operation).inc(tokens)
        LLM_REQUEST_DURATION.labels(provider=provider, model=model).observe(duration)
    else:
        LLM_ERRORS.labels(provider=provider, model=model, error_type='request_failed').inc()

def track_node_operation(operation: str, node_type: str):
    """Track node operation metrics"""
    NODE_OPERATIONS.labels(operation=operation, node_type=node_type).inc()

def track_conflict_operation(operation: str, severity: str):
    """Track conflict operation metrics"""
    CONFLICT_OPERATIONS.labels(operation=operation, severity=severity).inc()

def track_cache_operation(operation: str, cache_type: str, hit: bool = True):
    """Track cache operation metrics"""
    CACHE_OPERATIONS.labels(operation=operation, cache_type=cache_type).inc()

def track_db_operation(operation: str, table: str, duration: float):
    """Track database operation metrics"""
    DB_OPERATIONS.labels(operation=operation, table=table).inc()
    DB_QUERY_DURATION.labels(operation=operation, table=table).observe(duration)

def track_auth_operation(operation: str, status: str):
    """Track authentication operation metrics"""
    AUTH_OPERATIONS.labels(operation=operation, status=status).inc()

def track_auth_failure(operation: str, reason: str):
    """Track authentication failure metrics"""
    AUTH_FAILURES.labels(operation=operation, reason=reason).inc()

def track_rate_limit_hit(action: str, identifier: str):
    """Track rate limit hit metrics"""
    RATE_LIMIT_HITS.labels(action=action, identifier=identifier).inc()

def track_websocket_connection(connected: bool):
    """Track WebSocket connection metrics"""
    if connected:
        WEBSOCKET_CONNECTIONS.inc()
    else:
        WEBSOCKET_CONNECTIONS.dec()

def track_websocket_message(message_type: str):
    """Track WebSocket message metrics"""
    WEBSOCKET_MESSAGES.labels(message_type=message_type).inc()

def track_token_usage(user_id: str, model: str, tokens: int):
    """Track token usage by user"""
    TOKEN_USAGE_BY_USER.labels(user_id=user_id, model=model).inc(tokens)

def update_active_users(count: int):
    """Update active users count"""
    ACTIVE_USERS.set(count)

# Decorators for easy metric tracking
def track_request_time(method: str, endpoint: str):
    """Decorator to track request time and count"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                status = 200
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                track_request_metrics(method, endpoint, status, duration)
        return wrapper
    return decorator

def track_llm_time(provider: str, model: str, operation: str):
    """Decorator to track LLM request time and tokens"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                tokens = result.get('tokens_used', 0)
                track_llm_metrics(provider, model, operation, tokens, duration, True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                track_llm_metrics(provider, model, operation, 0, duration, False)
                raise
        return wrapper
    return decorator

def track_db_time(operation: str, table: str):
    """Decorator to track database operation time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                track_db_operation(operation, table, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                track_db_operation(operation, table, duration)
                raise
        return wrapper
    return decorator

# Metrics endpoint
def get_metrics():
    """Get Prometheus metrics"""
    return generate_latest(registry), CONTENT_TYPE_LATEST

# Health check metrics
def get_health_metrics() -> Dict[str, Any]:
    """Get health check metrics"""
    return {
        'uptime_seconds': metrics_collector.get_uptime(),
        'active_connections': WEBSOCKET_CONNECTIONS._value.get(),
        'total_requests': REQUEST_COUNT._metrics.get(),
        'total_llm_requests': LLM_REQUESTS._metrics.get(),
        'total_conflicts': CONFLICT_COUNT._metrics.get(),
        'cache_hit_ratio': CACHE_HIT_RATIO._metrics.get(),
    } 