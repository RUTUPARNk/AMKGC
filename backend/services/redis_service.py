import json
import logging
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import redis
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisService:
    """Service for Redis operations including caching, sessions, and rate limiting"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.client = redis.from_url(redis_url, decode_responses=True)
        
        # Default TTL values (in seconds)
        self.default_ttls = {
            'node_context': 3600,      # 1 hour
            'graph_data': 1800,        # 30 minutes
            'search_results': 900,     # 15 minutes
            'user_session': 86400,     # 24 hours
            'rate_limit': 60,          # 1 minute
            'token_usage': 604800,     # 1 week
            'conflict_data': 1800,     # 30 minutes
            'llm_cache': 3600,         # 1 hour
        }
        
        logger.info(f"RedisService initialized with URL: {redis_url}")
    
    def _get_key(self, prefix: str, *args) -> str:
        """Generate Redis key with prefix"""
        return f"{prefix}:{':'.join(str(arg) for arg in args)}"
    
    def set_cache(self, key: str, value: Any, ttl: Optional[int] = None, 
                  prefix: str = "cache") -> bool:
        """Set value in cache with TTL"""
        try:
            full_key = self._get_key(prefix, key)
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            
            if ttl is None:
                ttl = self.default_ttls.get(prefix, 3600)
            
            result = self.client.setex(full_key, ttl, serialized_value)
            logger.debug(f"Cached {full_key} with TTL {ttl}s")
            return result
            
        except Exception as e:
            logger.error(f"Error setting cache {key}: {e}")
            return False
    
    def get_cache(self, key: str, prefix: str = "cache") -> Optional[Any]:
        """Get value from cache"""
        try:
            full_key = self._get_key(prefix, key)
            value = self.client.get(full_key)
            
            if value is None:
                return None
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error(f"Error getting cache {key}: {e}")
            return None
    
    def delete_cache(self, key: str, prefix: str = "cache") -> bool:
        """Delete value from cache"""
        try:
            full_key = self._get_key(prefix, key)
            result = self.client.delete(full_key)
            logger.debug(f"Deleted cache {full_key}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Error deleting cache {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Invalidated {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidating pattern {pattern}: {e}")
            return 0
    
    def set_session(self, session_id: str, user_data: Dict[str, Any], 
                   ttl: Optional[int] = None) -> bool:
        """Set user session data"""
        try:
            if ttl is None:
                ttl = self.default_ttls['user_session']
            
            session_data = {
                'user_data': user_data,
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat()
            }
            
            return self.set_cache(session_id, session_data, ttl, "session")
            
        except Exception as e:
            logger.error(f"Error setting session {session_id}: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user session data"""
        try:
            session_data = self.get_cache(session_id, "session")
            if session_data:
                # Update last activity
                session_data['last_activity'] = datetime.now().isoformat()
                self.set_session(session_id, session_data['user_data'])
            
            return session_data
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete user session"""
        return self.delete_cache(session_id, "session")
    
    def check_rate_limit(self, identifier: str, action: str, 
                        max_requests: int, window: int) -> Dict[str, Any]:
        """Check rate limit for an action"""
        try:
            key = self._get_key("rate_limit", action, identifier)
            current_time = int(time.time())
            
            # Get current requests in window
            requests = self.client.zrangebyscore(key, current_time - window, current_time)
            
            if len(requests) >= max_requests:
                # Rate limit exceeded
                oldest_request = self.client.zrange(key, 0, 0, withscores=True)
                if oldest_request:
                    reset_time = oldest_request[0][1] + window
                    return {
                        'allowed': False,
                        'remaining': 0,
                        'reset_time': reset_time,
                        'retry_after': reset_time - current_time
                    }
            
            # Add current request
            self.client.zadd(key, {str(current_time): current_time})
            self.client.expire(key, window)
            
            remaining = max(0, max_requests - len(requests) - 1)
            
            return {
                'allowed': True,
                'remaining': remaining,
                'reset_time': current_time + window,
                'retry_after': 0
            }
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return {'allowed': True, 'remaining': max_requests, 'reset_time': 0, 'retry_after': 0}
    
    def log_token_usage(self, model: str, tokens_used: int, operation: str, 
                       user_id: Optional[str] = None) -> bool:
        """Log token usage for monitoring"""
        try:
            usage_data = {
                'model': model,
                'tokens_used': tokens_used,
                'operation': operation,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Store in sorted set for time-based queries
            key = self._get_key("token_usage", model)
            score = time.time()
            
            self.client.zadd(key, {json.dumps(usage_data): score})
            
            # Keep only last 1000 entries
            self.client.zremrangebyrank(key, 0, -1001)
            
            # Set TTL
            self.client.expire(key, self.default_ttls['token_usage'])
            
            logger.debug(f"Logged token usage: {model} - {tokens_used} tokens")
            return True
            
        except Exception as e:
            logger.error(f"Error logging token usage: {e}")
            return False
    
    def get_token_usage_stats(self, model: Optional[str] = None, 
                            hours: int = 24) -> Dict[str, Any]:
        """Get token usage statistics"""
        try:
            stats = {
                'total_tokens': 0,
                'total_requests': 0,
                'by_model': {},
                'by_operation': {}
            }
            
            since_time = time.time() - (hours * 3600)
            
            if model:
                keys = [self._get_key("token_usage", model)]
            else:
                keys = self.client.keys("token_usage:*")
            
            for key in keys:
                # Get usage data from the last N hours
                usage_entries = self.client.zrangebyscore(key, since_time, '+inf')
                
                for entry in usage_entries:
                    try:
                        usage_data = json.loads(entry)
                        tokens = usage_data.get('tokens_used', 0)
                        model_name = usage_data.get('model', 'unknown')
                        operation = usage_data.get('operation', 'unknown')
                        
                        stats['total_tokens'] += tokens
                        stats['total_requests'] += 1
                        
                        # By model
                        if model_name not in stats['by_model']:
                            stats['by_model'][model_name] = {'tokens': 0, 'requests': 0}
                        stats['by_model'][model_name]['tokens'] += tokens
                        stats['by_model'][model_name]['requests'] += 1
                        
                        # By operation
                        if operation not in stats['by_operation']:
                            stats['by_operation'][operation] = {'tokens': 0, 'requests': 0}
                        stats['by_operation'][operation]['tokens'] += tokens
                        stats['by_operation'][operation]['requests'] += 1
                        
                    except json.JSONDecodeError:
                        continue
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting token usage stats: {e}")
            return {'error': str(e)}
    
    def set_graph_data(self, graph_id: str, graph_data: Dict[str, Any]) -> bool:
        """Cache graph data"""
        return self.set_cache(graph_id, graph_data, prefix="graph")
    
    def get_graph_data(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """Get cached graph data"""
        return self.get_cache(graph_id, "graph")
    
    def set_search_results(self, query: str, results: List[Dict[str, Any]]) -> bool:
        """Cache search results"""
        return self.set_cache(query, results, prefix="search")
    
    def get_search_results(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results"""
        return self.get_cache(query, "search")
    
    def add_to_list(self, list_name: str, item: Any, max_length: int = 1000) -> bool:
        """Add item to a Redis list with max length"""
        try:
            key = self._get_key("list", list_name)
            serialized_item = json.dumps(item) if not isinstance(item, str) else item
            
            # Add to list
            self.client.lpush(key, serialized_item)
            
            # Trim to max length
            self.client.ltrim(key, 0, max_length - 1)
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding to list {list_name}: {e}")
            return False
    
    def get_list(self, list_name: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get items from a Redis list"""
        try:
            key = self._get_key("list", list_name)
            items = self.client.lrange(key, start, end)
            
            result = []
            for item in items:
                try:
                    result.append(json.loads(item))
                except json.JSONDecodeError:
                    result.append(item)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting list {list_name}: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis statistics"""
        try:
            info = self.client.info()
            
            # Get cache statistics
            cache_keys = self.client.keys("cache:*")
            session_keys = self.client.keys("session:*")
            graph_keys = self.client.keys("graph:*")
            search_keys = self.client.keys("search:*")
            
            stats = {
                'redis_info': {
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'connected_clients': info.get('connected_clients', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                },
                'cache_stats': {
                    'total_cache_keys': len(cache_keys),
                    'total_sessions': len(session_keys),
                    'total_graphs': len(graph_keys),
                    'total_searches': len(search_keys)
                },
                'token_usage': self.get_token_usage_stats()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {'error': str(e)}
    
    def clear_all(self) -> bool:
        """Clear all application data from Redis"""
        try:
            patterns = [
                "cache:*",
                "session:*",
                "graph:*",
                "search:*",
                "rate_limit:*",
                "token_usage:*",
                "list:*"
            ]
            
            total_deleted = 0
            for pattern in patterns:
                deleted = self.invalidate_pattern(pattern)
                total_deleted += deleted
            
            logger.info(f"Cleared {total_deleted} keys from Redis")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing Redis: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            # Test basic operations
            test_key = "health_check_test"
            test_value = {"test": True, "timestamp": datetime.now().isoformat()}
            
            # Set test value
            self.set_cache(test_key, test_value, ttl=10)
            
            # Get test value
            retrieved_value = self.get_cache(test_key)
            
            # Clean up
            self.delete_cache(test_key)
            
            if retrieved_value == test_value:
                return {
                    'status': 'healthy',
                    'message': 'Redis is working correctly',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': 'Redis data integrity check failed',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Redis health check failed: {e}',
                'timestamp': datetime.now().isoformat()
            }
    
    def get_all_cache_entries(self) -> Dict[str, Any]:
        """Get all cache entries"""
        try:
            # Get all cache keys
            keys = self.client.keys("cache:*")
            entries = {}
            
            # Get values for each key
            for key in keys:
                # Remove prefix from key name
                clean_key = key.replace("cache:", "", 1)
                value = self.client.get(key)
                
                # Try to deserialize JSON
                try:
                    entries[clean_key] = json.loads(value)
                except json.JSONDecodeError:
                    entries[clean_key] = value
            
            return entries
            
        except Exception as e:
            logger.error(f"Error getting all cache entries: {e}")
            return {}

def rate_limit_decorator(max_requests: int, window: int, identifier_func=None):
    """Decorator for rate limiting functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get identifier (user_id, IP, etc.)
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                identifier = "default"
            
            # Check rate limit
            redis_service = RedisService()
            rate_limit_result = redis_service.check_rate_limit(
                identifier, func.__name__, max_requests, window
            )
            
            if not rate_limit_result['allowed']:
                raise Exception(f"Rate limit exceeded. Retry after {rate_limit_result['retry_after']} seconds")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator 