import os
from typing import AsyncGenerator
from . import llm_qwen, llm_ollama
from config.config import settings

# Default provider from settings
DEFAULT_LLM_PROVIDER = settings.LLM_PROVIDER

# Thread-local storage for request-specific provider
import threading
_local = threading.local()

def set_provider(provider: str):
    """Set the provider for the current request"""
    _local.provider = provider

def get_provider() -> str:
    """Get the provider for the current request, or default provider"""
    return getattr(_local, 'provider', DEFAULT_LLM_PROVIDER)

async def stream_response(model: str, prompt: str) -> AsyncGenerator[str, None]:
    """Unified interface for streaming responses from different LLM providers"""
    provider = get_provider()
    
    if provider == "qwen":
        async for token in llm_qwen.stream_qwen_response(prompt):
            yield token
    elif provider == "ollama":
        async for token in llm_ollama.stream_ollama_response(model, prompt):
            yield token
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
