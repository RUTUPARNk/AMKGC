"""
Ollama Model Warm-up Service

This service pre-loads Ollama models to reduce cold start latency.
It also maintains model availability through periodic keep-alive pings.
Updated to use adaptive memory-aware loading with priority levels.
"""

import time
import logging
import requests
import os
import sys
import threading
import subprocess
from typing import Dict, Any, List

# Add the parent directory to the path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from config.config import settings
except ImportError:
    # Fallback if running as standalone script
    class Settings:
        OLLAMA_URL = "http://localhost:11434"
        OLLAMA_MODEL = "llama3"
    
    settings = Settings()

logger = logging.getLogger(__name__)

# Try to import psutil for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available. Install with: pip install psutil")

# Configuration for adaptive loading
MEMORY_THRESHOLD = 0.75  # unload if >75% RAM used

# Model priorities (higher number = higher priority)
# This should match the configuration in ollama_warmup_service.py
MODELS = [
    {"name": "llama3:latest", "priority": 2},
    {"name": "qwen3:latest", "priority": 1}
]

# Track last used times for LRU eviction
last_used: Dict[str, float] = {}


class OllamaWarmupService:
    """Service to warm up Ollama models and keep them alive with adaptive memory management"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
        self.is_ready = False
        self.keep_alive_thread = None
        self.keep_alive_running = False
    
    def memory_ok(self) -> bool:
        """Check if memory usage is below threshold"""
        if not PSUTIL_AVAILABLE:
            return True  # If we can't check memory, assume it's OK
        try:
            mem = psutil.virtual_memory()
            return mem.percent < MEMORY_THRESHOLD * 100
        except Exception as e:
            logger.error(f"Error checking memory: {e}")
            return True  # If error, assume OK to avoid blocking
    
    def is_model_loaded(self, model: str) -> bool:
        """Check if a model is currently loaded in Ollama"""
        try:
            result = subprocess.check_output(["ollama", "ps"], stderr=subprocess.STDOUT)
            output = result.decode()
            return model in output
        except Exception as e:
            logger.error(f"Error checking if {model} is loaded: {e}")
            return False
    
    def unload_model(self, model: str) -> bool:
        """Unload a model to free memory"""
        try:
            logger.info(f"Unloading {model} to save memory...")
            subprocess.run(["ollama", "stop", model], check=True, capture_output=True)
            logger.info(f"{model} unloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error unloading {model}: {e}")
            return False
    
    def warmup_model(self) -> bool:
        """Warm up the Ollama model with a dummy request using adaptive memory management"""
        try:
            logger.info(f"Warming up Ollama model: {self.model}")
            
            # Check if we need to unload lower priority models to make room
            current_model_info = next((m for m in MODELS if m["name"] == self.model), None)
            if current_model_info and current_model_info["priority"] == 2:  # High priority
                if not self.memory_ok():
                    # Try to unload a lower priority model first
                    lower_models = [m for m in MODELS if m["priority"] < 2 and self.is_model_loaded(m["name"])]
                    if lower_models:
                        self.unload_model(lower_models[0]["name"])
            
            start_time = time.perf_counter()
            
            # Send a small warmup request
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": "Hello, world!",
                    "stream": False
                },
                timeout=30.0  # Longer timeout for warmup
            )
            
            end_time = time.perf_counter()
            warmup_time = end_time - start_time
            
            if response.status_code == 200:
                logger.info(f"Ollama model {self.model} warmed up successfully in {warmup_time:.2f} seconds")
                self.is_ready = True
                last_used[self.model] = time.time()  # Track usage for LRU
                return True
            else:
                logger.error(f"Ollama warmup failed with status {response.status_code}: {response.text}")
                self.is_ready = False
                return False
                
        except Exception as e:
            logger.error(f"Ollama warmup failed with exception: {e}")
            self.is_ready = False
            return False
    
    def check_readiness(self) -> bool:
        """Check if Ollama service is ready and models are loaded"""
        try:
            # Check if Ollama API is responsive
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5.0)
            if response.status_code != 200:
                return False
            
            # Check if our model is loaded (equivalent to ollama ps)
            running_models_response = requests.get(f"{self.ollama_url}/api/ps", timeout=5.0)
            if running_models_response.status_code == 200:
                running_models = running_models_response.json().get('models', [])
                for model_info in running_models:
                    if self.model in model_info.get('name', ''):
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Ollama readiness check failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
        return {}
    
    def send_keep_alive_ping(self) -> bool:
        """Send a keep-alive ping to keep the model loaded"""
        try:
            logger.debug(f"Sending keep-alive ping for model: {self.model}")
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": "ping",
                    "stream": False
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                logger.debug(f"Keep-alive ping successful for model: {self.model}")
                last_used[self.model] = time.time()  # Update usage time
                return True
            else:
                logger.warning(f"Keep-alive ping failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Keep-alive ping failed with exception: {e}")
            return False
    
    def start_keep_alive_daemon(self):
        """Start background thread to send periodic keep-alive pings"""
        if self.keep_alive_thread and self.keep_alive_thread.is_alive():
            logger.info("Keep-alive daemon is already running")
            return
        
        self.keep_alive_running = True
        self.keep_alive_thread = threading.Thread(target=self._keep_alive_worker, daemon=True)
        self.keep_alive_thread.start()
        logger.info("Keep-alive daemon started")
    
    def stop_keep_alive_daemon(self):
        """Stop the background keep-alive thread"""
        self.keep_alive_running = False
        if self.keep_alive_thread:
            self.keep_alive_thread.join(timeout=5)
        logger.info("Keep-alive daemon stopped")
    
    def _keep_alive_worker(self):
        """Background worker that sends periodic keep-alive pings with adaptive memory management"""
        # Wait a bit after initial warmup before starting pings
        time.sleep(30)
        
        while self.keep_alive_running:
            try:
                # Check memory and unload if needed
                if not self.memory_ok():
                    logger.warning("Memory usage high, considering model unload...")
                    # Find lowest priority, least recently used model to unload
                    loaded_models = [m for m in MODELS if self.is_model_loaded(m["name"])]
                    if loaded_models:
                        # Sort by priority first, then by last used time (LRU)
                        unload_candidate = sorted(
                            loaded_models, 
                            key=lambda x: (x["priority"], last_used.get(x["name"], 0))
                        )[0]
                        
                        # Only unload if it's not a high priority model
                        if unload_candidate["priority"] < 2 and self.is_model_loaded(unload_candidate["name"]):
                            self.unload_model(unload_candidate["name"])
                
                # Check if model is still loaded
                if not self.check_readiness():
                    logger.warning(f"Model {self.model} not found in running models, re-warming up...")
                    self.warmup_model()
                else:
                    # Send keep-alive ping
                    self.send_keep_alive_ping()
                
                # Wait 1 minute before next ping (more frequent for better responsiveness)
                for _ in range(60):  # 60 seconds
                    if not self.keep_alive_running:
                        break
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Error in keep-alive worker: {e}")
                time.sleep(30)  # Wait before retrying


# Global instance
ollama_warmup_service = OllamaWarmupService()
