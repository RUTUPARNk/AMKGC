import os
import json
import time
import logging
import subprocess
import requests
from typing import Dict, Any, Optional, List, Tuple, AsyncGenerator
from functools import wraps
import redis
from datetime import datetime, timedelta
import httpx

# Import the new OllamaProvider
from .ollama_provider import OllamaProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def rate_limit(calls: int, period: int):
    """Rate limiting decorator for LLM calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Simple in-memory rate limiting
            # In production, use Redis for distributed rate limiting
            current_time = time.time()
            if not hasattr(wrapper, 'call_times'):
                wrapper.call_times = []
            
            # Remove old calls outside the window
            wrapper.call_times = [t for t in wrapper.call_times if current_time - t < period]
            
            if len(wrapper.call_times) >= calls:
                sleep_time = period - (current_time - wrapper.call_times[0])
                if sleep_time > 0:
                    logger.warning(f"Rate limit exceeded. Sleeping for {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
            
            wrapper.call_times.append(current_time)
            return func(*args, **kwargs)
        return wrapper
    return decorator

class LLMService:
    """Service for interacting with Large Language Models (Ollama and OpenAI)"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Dynamic token thresholds based on model
        self.token_thresholds = {
            'ollama': {
                'llama3': 8192,
                'llama2': 4096,
                'mistral': 8192,
                'default': 4096
            },
            'openai': {
                'gpt-4': 8192,
                'gpt-3.5-turbo': 4096,
                'default': 4096
            }
        }
        
        # Rate limiting configuration
        self.rate_limits = {
            'ollama': {'calls': 10, 'period': 60},  # 10 calls per minute
            'openai': {'calls': 60, 'period': 60}   # 60 calls per minute
        }
        
        # Model configuration
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'llama3')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        
        # Initialize OllamaProvider
        self.ollama_provider = OllamaProvider(model=self.ollama_model)
        
        logger.info(f"LLMService initialized with Ollama model: {self.ollama_model}")
    
    def _get_cache_key(self, operation: str, **kwargs) -> str:
        """Generate cache key for Redis"""
        key_parts = ['llm', operation]
        for k, v in sorted(kwargs.items()):
            key_parts.extend([k, str(v)])
        return ':'.join(key_parts)
    
    def _cache_get(self, key: str) -> Optional[str]:
        """Get value from Redis cache"""
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def _cache_set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """Set value in Redis cache with TTL"""
        try:
            return self.redis_client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def _log_token_usage(self, model: str, tokens_used: int, operation: str):
        """Log token usage for monitoring"""
        try:
            usage_data = {
                'model': model,
                'tokens_used': tokens_used,
                'operation': operation,
                'timestamp': datetime.now().isoformat()
            }
            self.redis_client.lpush('token_usage_log', json.dumps(usage_data))
            self.redis_client.ltrim('token_usage_log', 0, 999)  # Keep last 1000 entries
        except Exception as e:
            logger.error(f"Token usage logging error: {e}")
    
    @rate_limit(calls=10, period=60)
    def generate(self, prompt: str, model: str = 'ollama', **kwargs) -> Dict[str, Any]:
        """
        Generate content using the specified LLM
        
        Args:
            prompt: The input prompt
            model: 'ollama' or 'openai'
            **kwargs: Additional parameters for the LLM
        
        Returns:
            Dict containing the generated content and metadata
        """
        cache_key = self._get_cache_key('generate', prompt=prompt, model=model, **kwargs)
        
        # Check cache first
        cached_result = self._cache_get(cache_key)
        if cached_result:
            logger.info("Returning cached LLM result")
            return json.loads(cached_result)
        
        try:
            if model == 'ollama':
                result = self._generate_with_ollama(prompt, **kwargs)
            else:
                result = self._generate_with_openai(prompt, **kwargs)
            
            # Cache the result
            self._cache_set(cache_key, json.dumps(result), ttl=3600)  # 1 hour TTL
            
            return result
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Fallback to OpenAI if Ollama fails
            if model == 'ollama' and self.openai_api_key:
                logger.info("Falling back to OpenAI")
                try:
                    result = self._generate_with_openai(prompt, **kwargs)
                    result['fallback_used'] = True
                    return result
                except Exception as fallback_error:
                    logger.error(f"OpenAI fallback also failed: {fallback_error}")
            
            raise
    
    def _generate_with_ollama(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate content using Ollama"""
        try:
            # Check if Ollama is available
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                raise Exception("Ollama is not available")
            
            # Generate content
            cmd = ['ollama', 'run', self.ollama_model, prompt]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"Ollama generation failed: {result.stderr}")
            
            content = result.stdout.strip()
            tokens_used = len(content.split())  # Approximate token count
            
            self._log_token_usage('ollama', tokens_used, 'generate')
            
            return {
                'content': content,
                'model': self.ollama_model,
                'tokens_used': tokens_used,
                'provider': 'ollama',
                'timestamp': datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            raise Exception("Ollama request timed out")
        except Exception as e:
            raise Exception(f"Ollama generation error: {e}")
    
    @rate_limit(calls=60, period=60)
    def _generate_with_openai(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate content using OpenAI API"""
        if not self.openai_api_key:
            raise Exception("OpenAI API key not configured")
        
        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': self.openai_model,
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': kwargs.get('max_tokens', 2048),
                'temperature': kwargs.get('temperature', 0.7)
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited by OpenAI. Retry after {retry_after} seconds")
                time.sleep(retry_after)
                return self._generate_with_openai(prompt, **kwargs)
            
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            tokens_used = result['usage']['total_tokens']
            
            self._log_token_usage('openai', tokens_used, 'generate')
            
            return {
                'content': content,
                'model': self.openai_model,
                'tokens_used': tokens_used,
                'provider': 'openai',
                'timestamp': datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenAI API error: {e}")
    
    def generate_schema(self, table_name: str, description: str = "") -> Dict[str, Any]:
        """Generate database schema using LLM"""
        prompt = f"""
        Generate a database schema for table '{table_name}'.
        Description: {description}
        
        Return the schema in JSON format with columns, data types, constraints, and indexes.
        """
        
        cache_key = self._get_cache_key('schema', table=table_name, desc=description)
        cached_result = self._cache_get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        result = self.generate(prompt)
        self._cache_set(cache_key, json.dumps(result), ttl=3600)  # 1 hour TTL
        
        return result
    
    def generate_policy(self, policy_type: str, context: str = "") -> Dict[str, Any]:
        """Generate policy rules using LLM"""
        prompt = f"""
        Generate {policy_type} policy rules.
        Context: {context}
        
        Return the policy in a structured format with rules, conditions, and actions.
        """
        
        cache_key = self._get_cache_key('policy', type=policy_type, context=context)
        cached_result = self._cache_get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        result = self.generate(prompt)
        self._cache_set(cache_key, json.dumps(result), ttl=3600)  # 1 hour TTL
        
        return result
    
    def detect_conflicts(self, node1_context: str, node2_context: str, 
                        user_feedback: str = "") -> Dict[str, Any]:
        """Detect conflicts between two node contexts"""
        prompt = f"""
        Analyze these two node contexts for conflicts:
        
        Node 1 Context:
        {node1_context}
        
        Node 2 Context:
        {node2_context}
        
        User Feedback: {user_feedback}
        
        Identify any conflicts, inconsistencies, or contradictions.
        Return analysis in JSON format with:
        - conflicts: list of detected conflicts
        - severity: critical/high/medium/low
        - priority: 1-10 (10 being highest)
        - resolution_suggestions: list of suggested resolutions
        """
        
        result = self.generate(prompt)
        
        try:
            # Try to parse the response as JSON
            analysis = json.loads(result['content'])
            return {
                'conflicts': analysis.get('conflicts', []),
                'severity': analysis.get('severity', 'medium'),
                'priority': analysis.get('priority', 5),
                'suggestions': analysis.get('resolution_suggestions', []),
                'raw_analysis': result['content']
            }
        except json.JSONDecodeError:
            # If not JSON, return the raw content
            return {
                'conflicts': [result['content']],
                'severity': 'medium',
                'priority': 5,
                'suggestions': [],
                'raw_analysis': result['content']
            }
    
    def resolve_conflict(self, conflict_description: str, context: str = "",
                        user_feedback: str = "") -> Dict[str, Any]:
        """Generate conflict resolution using LLM"""
        prompt = f"""
        Resolve this conflict:
        
        Conflict: {conflict_description}
        Context: {context}
        User Feedback: {user_feedback}
        
        Provide a resolution that addresses the conflict while maintaining consistency.
        Return the resolution in a clear, actionable format.
        """
        
        return self.generate(prompt)
    
    def check_token_limit(self, content: str, model: str = 'ollama') -> Tuple[bool, int]:
        """Check if content exceeds token limit for the model"""
        # Approximate token count (words + punctuation)
        token_count = len(content.split()) + len([c for c in content if c in '.,;:!?'])
        
        if model == 'ollama':
            threshold = self.token_thresholds['ollama'].get(self.ollama_model, 
                                                          self.token_thresholds['ollama']['default'])
        else:
            threshold = self.token_thresholds['openai'].get(self.openai_model,
                                                          self.token_thresholds['openai']['default'])
        
        exceeds_limit = token_count > threshold
        
        if exceeds_limit:
            logger.warning(f"Token limit exceeded: {token_count} > {threshold}")
        
        return exceeds_limit, token_count
    
    def split_context(self, content: str, model: str = 'ollama') -> List[str]:
        """Split large context into smaller chunks"""
        exceeds_limit, token_count = self.check_token_limit(content, model)
        
        if not exceeds_limit:
            return [content]
        
        # Get threshold for the model
        if model == 'ollama':
            threshold = self.token_thresholds['ollama'].get(self.ollama_model,
                                                          self.token_thresholds['ollama']['default'])
        else:
            threshold = self.token_thresholds['openai'].get(self.openai_model,
                                                          self.token_thresholds['openai']['default'])
        
        # Split by paragraphs first, then by sentences
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk + paragraph) < threshold * 0.8:  # 80% of threshold
                current_chunk += paragraph + '\n\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + '\n\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # If still too large, split by sentences
        if len(chunks) == 1 and len(chunks[0]) > threshold:
            sentences = content.split('. ')
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk + sentence) < threshold * 0.8:
                    current_chunk += sentence + '. '
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + '. '
            
            if current_chunk:
                chunks.append(current_chunk.strip())
        
        logger.info(f"Split content into {len(chunks)} chunks")
        return chunks
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            info = self.redis_client.info()
            return {
                'used_memory': info.get('used_memory_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}
    
    def clear_cache(self) -> bool:
        """Clear all LLM cache entries"""
        try:
            keys = self.redis_client.keys('llm:*')
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} LLM cache entries")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_available_ollama_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            # Try API first
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return [model.get("name", "") for model in models if model.get("name")]
        except requests.exceptions.RequestException as e:
            logger.warning(f"API request failed: {e}")
        
        # Fallback to CLI
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                models = []
                for line in lines[1:]:  # Skip header line
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)
                return models
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"CLI fallback failed: {e}")
        
        return []
    
    def validate_ollama_model(self, model_name: str) -> bool:
        """Check if a specific Ollama model is available"""
        available_models = self.get_available_ollama_models()
        return model_name in available_models
    
    def get_first_available_model(self) -> Optional[str]:
        """Get the first available Ollama model name"""
        available_models = self.get_available_ollama_models()
        return available_models[0] if available_models else None
    
    def update_ollama_model(self, model_name: str) -> bool:
        """Update the Ollama model being used"""
        if self.validate_ollama_model(model_name):
            self.ollama_model = model_name
            logger.info(f"Updated Ollama model to: {model_name}")
            return True
        else:
            logger.error(f"Model '{model_name}' not found in available models")
            return False
    
    def check_ollama_status(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    async def chat_with_ollama(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Chat with Ollama using the new OllamaProvider
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            Dict containing the response message
        """
        try:
            return await self.ollama_provider.chat(messages)
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            raise
    
    async def embed_with_ollama(self, text: str) -> List[float]:
        """
        Generate embeddings with Ollama using the new OllamaProvider
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        try:
            return await self.ollama_provider.embed(text)
        except Exception as e:
            logger.error(f"Ollama embedding failed: {e}")
            raise


import os
import httpx
from typing import AsyncGenerator
from . import llm_qwen, llm_ollama

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "qwen")

async def stream_response(prompt: str) -> AsyncGenerator[str, None]:
    if LLM_PROVIDER == "qwen":
        async for token in llm_qwen.stream_qwen_response(prompt):
            yield token
    elif LLM_PROVIDER == "ollama":
        async for token in llm_ollama.stream_ollama_response(prompt):
            yield token
    else:
        raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")