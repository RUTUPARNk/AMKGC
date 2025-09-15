import pytest
import unittest.mock as mock
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

from ..services.llm_service import LLMService, rate_limit

class TestLLMService:
    """Test cases for LLMService"""
    
    @pytest.fixture
    def llm_service(self):
        """Create LLMService instance for testing"""
        with patch('redis.from_url'):
            service = LLMService("redis://localhost:6379")
            return service
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        with patch('redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_redis.return_value = mock_client
            yield mock_client
    
    def test_init(self, mock_redis):
        """Test LLMService initialization"""
        service = LLMService("redis://localhost:6379")
        
        assert service.redis_url == "redis://localhost:6379"
        assert service.ollama_model == "llama3"
        assert service.openai_model == "gpt-3.5-turbo"
        assert "llama3" in service.token_thresholds["ollama"]
        assert "gpt-3.5-turbo" in service.token_thresholds["openai"]
    
    @patch('subprocess.run')
    def test_generate_with_ollama_success(self, mock_subprocess, llm_service):
        """Test successful Ollama generation"""
        # Mock subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Generated content"
        mock_subprocess.return_value = mock_result
        
        # Mock Redis cache
        llm_service.redis_client.get.return_value = None
        llm_service.redis_client.setex.return_value = True
        
        result = llm_service._generate_with_ollama("Test prompt")
        
        assert result["content"] == "Generated content"
        assert result["model"] == "llama3"
        assert result["provider"] == "ollama"
        assert "timestamp" in result
    
    @patch('subprocess.run')
    def test_generate_with_ollama_failure(self, mock_subprocess, llm_service):
        """Test Ollama generation failure"""
        # Mock subprocess result with error
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Ollama error"
        mock_subprocess.return_value = mock_result
        
        with pytest.raises(Exception, match="Ollama generation failed"):
            llm_service._generate_with_ollama("Test prompt")
    
    @patch('requests.post')
    def test_generate_with_openai_success(self, mock_post, llm_service):
        """Test successful OpenAI generation"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generated content"}}],
            "usage": {"total_tokens": 100}
        }
        mock_post.return_value = mock_response
        
        # Mock Redis cache
        llm_service.redis_client.get.return_value = None
        llm_service.redis_client.setex.return_value = True
        
        result = llm_service._generate_with_openai("Test prompt")
        
        assert result["content"] == "Generated content"
        assert result["model"] == "gpt-3.5-turbo"
        assert result["provider"] == "openai"
        assert result["tokens_used"] == 100
    
    @patch('requests.post')
    def test_generate_with_openai_rate_limit(self, mock_post, llm_service):
        """Test OpenAI rate limiting"""
        # Mock rate limit response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_post.return_value = mock_response
        
        with patch('time.sleep'):  # Mock sleep to avoid delays
            with pytest.raises(Exception):
                llm_service._generate_with_openai("Test prompt")
    
    def test_generate_with_cache_hit(self, llm_service):
        """Test generation with cache hit"""
        cached_result = {
            "content": "Cached content",
            "model": "llama3",
            "provider": "ollama",
            "timestamp": datetime.now().isoformat()
        }
        
        llm_service.redis_client.get.return_value = json.dumps(cached_result)
        
        result = llm_service.generate("Test prompt", model="ollama")
        
        assert result["content"] == "Cached content"
        # Should not call actual LLM
        llm_service.redis_client.setex.assert_not_called()
    
    def test_generate_with_fallback(self, llm_service):
        """Test generation with OpenAI fallback"""
        # Mock Ollama failure
        with patch.object(llm_service, '_generate_with_ollama') as mock_ollama:
            mock_ollama.side_effect = Exception("Ollama unavailable")
            
            # Mock OpenAI success
            with patch.object(llm_service, '_generate_with_openai') as mock_openai:
                mock_openai.return_value = {
                    "content": "Fallback content",
                    "model": "gpt-3.5-turbo",
                    "provider": "openai",
                    "tokens_used": 50,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Mock Redis cache
                llm_service.redis_client.get.return_value = None
                llm_service.redis_client.setex.return_value = True
                
                result = llm_service.generate("Test prompt", model="ollama")
                
                assert result["content"] == "Fallback content"
                assert result["fallback_used"] is True
    
    def test_check_token_limit(self, llm_service):
        """Test token limit checking"""
        # Test within limit
        short_text = "Short text"
        exceeds, count = llm_service.check_token_limit(short_text, "ollama")
        assert not exceeds
        assert count > 0
        
        # Test exceeding limit
        long_text = "word " * 5000  # Very long text
        exceeds, count = llm_service.check_token_limit(long_text, "ollama")
        assert exceeds
        assert count > 4000
    
    def test_split_context(self, llm_service):
        """Test context splitting"""
        # Test short context (no splitting needed)
        short_context = "Short context"
        chunks = llm_service.split_context(short_context, "ollama")
        assert len(chunks) == 1
        assert chunks[0] == short_context
        
        # Test long context (splitting needed)
        long_context = "word " * 5000
        chunks = llm_service.split_context(long_context, "ollama")
        assert len(chunks) > 1
        assert all(len(chunk) > 0 for chunk in chunks)
    
    def test_detect_conflicts(self, llm_service):
        """Test conflict detection"""
        with patch.object(llm_service, 'generate') as mock_generate:
            mock_generate.return_value = {
                "content": json.dumps({
                    "conflicts": ["Conflict 1", "Conflict 2"],
                    "severity": "high",
                    "priority": 8,
                    "resolution_suggestions": ["Suggestion 1"]
                })
            }
            
            result = llm_service.detect_conflicts(
                "Context 1", "Context 2", "User feedback"
            )
            
            assert "conflicts" in result
            assert "severity" in result
            assert "priority" in result
            assert "suggestions" in result
    
    def test_resolve_conflict(self, llm_service):
        """Test conflict resolution"""
        with patch.object(llm_service, 'generate') as mock_generate:
            mock_generate.return_value = {
                "content": "Resolution content",
                "model": "llama3",
                "provider": "ollama"
            }
            
            result = llm_service.resolve_conflict(
                "Conflict description", "Context", "User feedback"
            )
            
            assert result["content"] == "Resolution content"
    
    def test_get_cache_stats(self, llm_service):
        """Test cache statistics"""
        mock_info = {
            "used_memory_human": "1.5M",
            "connected_clients": 5,
            "total_commands_processed": 1000,
            "keyspace_hits": 800,
            "keyspace_misses": 200
        }
        
        llm_service.redis_client.info.return_value = mock_info
        
        stats = llm_service.get_cache_stats()
        
        assert stats["used_memory"] == "1.5M"
        assert stats["connected_clients"] == 5
        assert stats["total_commands_processed"] == 1000
    
    def test_clear_cache(self, llm_service):
        """Test cache clearing"""
        llm_service.redis_client.keys.return_value = ["llm:key1", "llm:key2"]
        llm_service.redis_client.delete.return_value = 2
        
        result = llm_service.clear_cache()
        
        assert result is True
        llm_service.redis_client.delete.assert_called_once_with("llm:key1", "llm:key2")

class TestRateLimit:
    """Test rate limiting decorator"""
    
    def test_rate_limit_decorator(self):
        """Test rate limiting functionality"""
        call_count = 0
        
        @rate_limit(calls=2, period=1)
        def test_function():
            nonlocal call_count
            call_count += 1
            return call_count
        
        # First two calls should succeed
        assert test_function() == 1
        assert test_function() == 2
        
        # Third call should be rate limited
        with patch('time.sleep') as mock_sleep:
            test_function()
            mock_sleep.assert_called_once() 