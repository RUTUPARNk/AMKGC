import subprocess
import requests
import json
import os
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from functools import wraps
import redis
from collections import defaultdict

logger = logging.getLogger(__name__)

def rate_limit(max_calls: int, time_window: int):
    """Rate limiting decorator for LLM calls"""
    def decorator(func):
        call_history = defaultdict(list)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            func_name = func.__name__
            
            # Clean old calls outside the time window
            call_history[func_name] = [
                call_time for call_time in call_history[func_name]
                if current_time - call_time < time_window
            ]
            
            # Check if rate limit exceeded
            if len(call_history[func_name]) >= max_calls:
                raise Exception(f"Rate limit exceeded: {max_calls} calls per {time_window} seconds")
            
            # Add current call
            call_history[func_name].append(current_time)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

class OllamaService:
    def __init__(self, model_name: str = "llama3", openai_api_key: Optional[str] = None, 
                 redis_url: str = "redis://localhost:6379"):
        self.model_name = model_name
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.redis_url = redis_url
        self.fallback_enabled = bool(self.openai_api_key)
        
        # Dynamic token thresholds
        self.token_thresholds = {
            'low': 1024,
            'medium': 2048,
            'high': 4096,
            'critical': 8192
        }
        
        # Rate limiting configuration
        self.rate_limits = {
            'ollama': {'max_calls': 10, 'time_window': 60},  # 10 calls per minute
            'openai': {'max_calls': 5, 'time_window': 60}    # 5 calls per minute
        }
        
        # Initialize Redis connection
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def _get_cache_key(self, prefix: str, identifier: str) -> str:
        """Generate cache key with TTL"""
        return f"ollama:{prefix}:{identifier}"
    
    def _cache_get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache"""
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None
    
    def _cache_set(self, key: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Set data in cache with TTL"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.setex(key, ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def _log_token_usage(self, prompt_length: int, response_length: int, model: str):
        """Log token usage for monitoring"""
        total_tokens = prompt_length + response_length
        threshold_exceeded = None
        
        for threshold_name, threshold_value in self.token_thresholds.items():
            if total_tokens > threshold_value:
                threshold_exceeded = threshold_name
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'prompt_tokens': prompt_length,
            'response_tokens': response_length,
            'total_tokens': total_tokens,
            'threshold_exceeded': threshold_exceeded
        }
        
        if threshold_exceeded:
            logger.warning(f"Token limit exceeded: {log_data}")
        else:
            logger.info(f"Token usage: {log_data}")
    
    @rate_limit(max_calls=10, time_window=60)
    def generate(self, prompt: str, max_tokens: Optional[int] = None, 
                use_cache: bool = True) -> Dict[str, Any]:
        """
        Generate response using Ollama with fallback to OpenAI
        """
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key("generate", str(hash(prompt)))
            cached_result = self._cache_get(cache_key)
            if cached_result:
                logger.info("Using cached result for generation")
                return cached_result
        
        try:
            result = self._generate_with_ollama(prompt, max_tokens)
            
            # Cache the result
            if use_cache:
                cache_key = self._get_cache_key("generate", str(hash(prompt)))
                self._cache_set(cache_key, result, ttl=1800)  # 30 minutes TTL
            
            return result
            
        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}")
            if self.fallback_enabled:
                try:
                    result = self._generate_with_openai(prompt, max_tokens)
                    
                    # Cache the fallback result
                    if use_cache:
                        cache_key = self._get_cache_key("generate", str(hash(prompt)))
                        self._cache_set(cache_key, result, ttl=1800)
                    
                    return result
                except Exception as fallback_error:
                    logger.error(f"OpenAI fallback also failed: {fallback_error}")
                    raise Exception("Both Ollama and OpenAI failed")
            else:
                raise Exception("Ollama unavailable and no OpenAI fallback configured")
    
    def _generate_with_ollama(self, prompt: str, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate response using local Ollama with enhanced error handling
        """
        try:
            # Check if Ollama is available
            try:
                subprocess.run(["ollama", "--version"], capture_output=True, check=True, timeout=5)
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
                raise Exception("Ollama not available")
            
            # Use Ollama CLI with timeout
            cmd = ["ollama", "run", self.model_name, prompt]
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                logger.error(f"Ollama command failed: {error_msg}")
                raise Exception(f"Ollama command failed: {error_msg}")
            
            response_text = result.stdout.strip()
            
            # Log token usage
            self._log_token_usage(len(prompt.split()), len(response_text.split()), f"ollama:{self.model_name}")
            
            return {
                "text": response_text,
                "model": f"ollama:{self.model_name}",
                "execution_time": execution_time,
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": len(response_text.split()),
                    "total_tokens": len(prompt.split()) + len(response_text.split())
                }
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Ollama request timed out")
            raise Exception("Ollama request timed out")
        except FileNotFoundError:
            logger.error("Ollama not found")
            raise Exception("Ollama not found. Please install Ollama: https://ollama.com/download")
        except Exception as e:
            logger.error(f"Unexpected Ollama error: {e}")
            raise
    
    @rate_limit(max_calls=5, time_window=60)
    def _generate_with_openai(self, prompt: str, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate response using OpenAI API as fallback with enhanced error handling
        """
        if not self.openai_api_key:
            raise Exception("OpenAI API key not configured")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens or 2048,
                    "temperature": 0.7
                },
                timeout=60
            )
            
            execution_time = time.time() - start_time
            
            if response.status_code == 429:
                logger.warning("OpenAI rate limit exceeded")
                raise Exception("OpenAI rate limit exceeded")
            elif response.status_code != 200:
                error_msg = f"OpenAI API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            response_text = data["choices"][0]["message"]["content"]
            
            # Log token usage
            usage = data.get("usage", {})
            self._log_token_usage(
                usage.get("prompt_tokens", len(prompt.split())),
                usage.get("completion_tokens", len(response_text.split())),
                "openai:gpt-3.5-turbo"
            )
            
            return {
                "text": response_text,
                "model": "openai:gpt-3.5-turbo",
                "execution_time": execution_time,
                "usage": usage
            }
            
        except requests.exceptions.Timeout:
            logger.error("OpenAI request timed out")
            raise Exception("OpenAI request timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API request failed: {e}")
            raise Exception(f"OpenAI API request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected OpenAI error: {e}")
            raise
    
    def generate_schema(self, table_name: str, description: str) -> Dict[str, Any]:
        """
        Generate database schema for a table with caching
        """
        cache_key = self._get_cache_key("schema", f"{table_name}:{hash(description)}")
        cached_result = self._cache_get(cache_key)
        if cached_result:
            logger.info("Using cached schema")
            return cached_result
        
        prompt = f"""
        Generate a database schema for a table named '{table_name}' with the following description:
        {description}
        
        Return the schema as a JSON object with the following structure:
        {{
            "type": "schema",
            "table": "{table_name}",
            "columns": [
                {{"name": "column_name", "type": "data_type", "constraints": ["constraint1", "constraint2"]}}
            ],
            "indexes": [
                {{"name": "index_name", "columns": ["column1", "column2"], "type": "index_type"}}
            ],
            "relationships": [
                {{"type": "foreign_key", "column": "column_name", "references": "table.column"}}
            ]
        }}
        """
        
        response = self.generate(prompt, use_cache=False)
        try:
            schema = json.loads(response["text"])
            # Cache schema for 1 hour
            self._cache_set(cache_key, schema, ttl=3600)
            return schema
        except json.JSONDecodeError:
            schema = {
                "type": "schema",
                "table": table_name,
                "content": response["text"],
                "raw_response": True
            }
            self._cache_set(cache_key, schema, ttl=3600)
            return schema
    
    def generate_policy(self, policy_name: str, description: str) -> Dict[str, Any]:
        """
        Generate policy rules with caching
        """
        cache_key = self._get_cache_key("policy", f"{policy_name}:{hash(description)}")
        cached_result = self._cache_get(cache_key)
        if cached_result:
            logger.info("Using cached policy")
            return cached_result
        
        prompt = f"""
        Generate policy rules for '{policy_name}' with the following description:
        {description}
        
        Return the policy as a JSON object with the following structure:
        {{
            "type": "policy",
            "name": "{policy_name}",
            "rules": [
                {{"rule": "rule_description", "enforcement": "enforcement_level"}}
            ],
            "permissions": [
                {{"action": "action_name", "resource": "resource_name", "conditions": ["condition1", "condition2"]}}
            ]
        }}
        """
        
        response = self.generate(prompt, use_cache=False)
        try:
            policy = json.loads(response["text"])
            # Cache policy for 1 hour
            self._cache_set(cache_key, policy, ttl=3600)
            return policy
        except json.JSONDecodeError:
            policy = {
                "type": "policy",
                "name": policy_name,
                "content": response["text"],
                "raw_response": True
            }
            self._cache_set(cache_key, policy, ttl=3600)
            return policy
    
    def detect_conflicts(self, node1_context: str, node2_context: str) -> Dict[str, Any]:
        """
        Detect conflicts between two node contexts with priority assessment
        """
        prompt = f"""
        Analyze these two node contexts and detect any conflicts:
        
        Node 1 Context:
        {node1_context}
        
        Node 2 Context:
        {node2_context}
        
        Return the analysis as a JSON object:
        {{
            "has_conflicts": true/false,
            "conflict_type": "schema/policy/data",
            "priority": "critical/high/medium/low",
            "conflicts": [
                {{
                    "description": "conflict_description",
                    "severity": "critical/high/medium/low",
                    "suggestion": "resolution_suggestion",
                    "affected_fields": ["field1", "field2"]
                }}
            ]
        }}
        """
        
        response = self.generate(prompt, use_cache=False)
        try:
            return json.loads(response["text"])
        except json.JSONDecodeError:
            return {
                "has_conflicts": True,
                "conflict_type": "unknown",
                "priority": "medium",
                "conflicts": [{"description": "Unable to parse conflict analysis", "severity": "medium"}]
            }
    
    def resolve_conflict(self, conflict_description: str, node1_context: str, 
                        node2_context: str, user_feedback: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate resolution for a conflict with user feedback integration
        """
        feedback_context = f"\nUser Feedback: {user_feedback}" if user_feedback else ""
        
        prompt = f"""
        Resolve the following conflict:
        
        Conflict: {conflict_description}
        
        Node 1 Context:
        {node1_context}
        
        Node 2 Context:
        {node2_context}{feedback_context}
        
        Provide a resolution that combines or corrects the conflicting information.
        Return as JSON:
        {{
            "resolved_context": "resolved_content",
            "changes_made": ["change1", "change2"],
            "explanation": "explanation_of_resolution",
            "confidence_score": 0.0-1.0,
            "requires_user_review": true/false
        }}
        """
        
        response = self.generate(prompt, use_cache=False)
        try:
            return json.loads(response["text"])
        except json.JSONDecodeError:
            return {
                "resolved_context": response["text"],
                "changes_made": ["Manual resolution required"],
                "explanation": "Unable to parse automatic resolution",
                "confidence_score": 0.0,
                "requires_user_review": True
            }
    
    def check_token_limit(self, context: str, threshold: str = "medium") -> bool:
        """
        Check if context exceeds token limit with dynamic thresholds
        """
        threshold_value = self.token_thresholds.get(threshold, self.token_thresholds["medium"])
        return len(context) > threshold_value
    
    def get_token_count(self, text: str) -> int:
        """Get approximate token count for text"""
        return len(text.split())
    
    def split_context(self, context: str, threshold: str = "medium") -> List[str]:
        """
        Split large context into smaller chunks with dynamic thresholds
        """
        threshold_value = self.token_thresholds.get(threshold, self.token_thresholds["medium"])
        
        if len(context) <= threshold_value:
            return [context]
        
        chunks = []
        current_chunk = ""
        
        # Split by paragraphs first
        paragraphs = context.split('\n\n')
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > threshold_value:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # If still too large, split by sentences
        if len(chunks) == 1 and len(chunks[0]) > threshold_value:
            sentences = chunks[0].split('. ')
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) > threshold_value:
                    if current_chunk:
                        chunks.append(current_chunk.strip() + ".")
                    current_chunk = sentence
                else:
                    current_chunk += ". " + sentence if current_chunk else sentence
            
            if current_chunk:
                chunks.append(current_chunk.strip())
        
        return chunks
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        if not self.redis_client:
            return {"error": "Redis not available"}
        
        try:
            info = self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}
    
    def clear_cache(self, pattern: str = "ollama:*") -> bool:
        """Clear cache entries matching pattern"""
        if not self.redis_client:
            return False
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False 