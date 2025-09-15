"""
Configuration for Ollama Supervisor Service
"""

import os
from typing import List, Dict

class SupervisorConfig:
    # Supervisor settings
    CHECK_INTERVAL: int = int(os.getenv("SUPERVISOR_CHECK_INTERVAL", 30))  # seconds
    MEMORY_THRESHOLD: float = float(os.getenv("SUPERVISOR_MEMORY_THRESHOLD", 75.0))  # percentage
    
    # Webhook settings
    WEBHOOK_URL: str = os.getenv("SUPERVISOR_WEBHOOK_URL", "")
    ALERTS_ENABLED: bool = os.getenv("SUPERVISOR_ALERTS_ENABLED", "false").lower() == "true"
    
    # Models configuration (should match ollama_warmup.py)
    MODELS: List[Dict[str, any]] = [
        {"name": "llama3:latest", "priority": 2},
        {"name": "qwen3:latest", "priority": 1}
    ]
