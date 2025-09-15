import requests
import os
import logging
from typing import List, Dict, Any, Optional

# Try to import settings, fallback to environment variables if not available
try:
    from .config import settings
except ImportError:
    settings = None

logger = logging.getLogger(__name__)

class OllamaProvider:
    """Ollama provider for LLM chat and embedding functionality"""
    
    def __init__(self, model: str = None, base_url: str = None):
        """
        Initialize Ollama provider
        
        Args:
            model: Model name (default: llama3)
            base_url: Ollama API base URL (default: http://localhost:11434)
        """
        # Get model from parameters, settings, or environment variables
        if model:
            self.model = model
        elif settings and hasattr(settings, 'OLLAMA_MODEL'):
            self.model = settings.OLLAMA_MODEL
        else:
            self.model = os.getenv('OLLAMA_MODEL', 'llama3')
        
        # Get base URL from parameters, settings, or environment variables
        if base_url:
            self.base_url = base_url
        elif settings and hasattr(settings, 'OLLAMA_URL'):
            self.base_url = settings.OLLAMA_URL
        else:
            self.base_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        
        logger.info(f"OllamaProvider initialized with model: {self.model}, base_url: {self.base_url}")
    
    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Generate chat response using Ollama
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            Dict containing the response message
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages
                },
                timeout=300  # 5 minute timeout
            )
            
            response.raise_for_status()
            
            # Return the last message from the response
            response_data = response.json()
            return response_data.get("message", {"role": "assistant", "content": ""})
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama chat request failed: {e}")
            raise Exception(f"Ollama chat request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Ollama chat: {e}")
            raise
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings using Ollama
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "input": text
                },
                timeout=300  # 5 minute timeout
            )
            
            response.raise_for_status()
            
            response_data = response.json()
            return response_data.get("embedding", [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama embedding request failed: {e}")
            raise Exception(f"Ollama embedding request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Ollama embedding: {e}")
            raise
    
    def check_health(self) -> bool:
        """
        Check if Ollama service is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    def list_models(self) -> List[str]:
        """
        List available models
        
        Returns:
            List of available model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            return models
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama library
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=300  # 5 minute timeout for pulling
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to pull Ollama model {model_name}: {e}")
            return False
