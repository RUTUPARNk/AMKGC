import os
import logging
from typing import List, Optional
from .ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)

class OllamaEmbedder:
    """Ollama embedder for generating text embeddings"""
    
    def __init__(self, model: str = None, base_url: str = None) -> None:
        """
        Initialize Ollama embedder
        
        Args:
            model: Model name for embeddings (default: llama3)
            base_url: Ollama API base URL (default: http://localhost:11434)
        """
        self.provider = OllamaProvider(model=model, base_url=base_url)
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for text using Ollama
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        try:
            # The OllamaProvider.embed method is async, but we need a sync version
            # For now, we'll use requests directly to avoid async complexity
            import requests
            
            response = requests.post(
                f"{self.provider.base_url}/api/embeddings",
                json={
                    "model": self.provider.model,
                    "input": text
                },
                timeout=300  # 5 minute timeout
            )
            
            response.raise_for_status()
            
            response_data = response.json()
            embedding = response_data.get("embedding", [])
            
            if not embedding:
                raise Exception("Empty embedding returned from Ollama")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Ollama embedding failed: {e}")
            raise
