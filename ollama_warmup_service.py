#!/usr/bin/env python3
"""
Ollama Adaptive Warm-up and Keep-Alive Service

This service pre-loads Ollama models and keeps them alive by sending periodic pings.
It adapts to available memory by unloading lower-priority models when needed.
"""

import subprocess
import time
import requests
import sys
import os
import logging
from typing import List, Dict

# Try to import psutil for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil not available. Install with: pip install psutil")

# Configuration
OLLAMA_API = "http://localhost:11434/api/generate"
MEMORY_THRESHOLD = 0.75  # unload if >75% RAM used

# Model priorities (higher number = higher priority)
MODELS = [
    {"name": "llama3:latest", "priority": 2},
    {"name": "qwen3:latest", "priority": 1}
]

KEEPALIVE_INTERVAL = 60  # seconds

# Track last used times for LRU eviction
last_used: Dict[str, float] = {}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("warmup.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def memory_ok() -> bool:
    """Check if memory usage is below threshold"""
    if not PSUTIL_AVAILABLE:
        return True  # If we can't check memory, assume it's OK
    try:
        mem = psutil.virtual_memory()
        return mem.percent < MEMORY_THRESHOLD * 100
    except Exception as e:
        logger.error(f"❌ Error checking memory: {e}")
        return True  # If error, assume OK to avoid blocking


def is_model_loaded(model: str) -> bool:
    """Check if a model is currently loaded in Ollama"""
    try:
        result = subprocess.check_output(["ollama", "ps"], stderr=subprocess.STDOUT)
        output = result.decode()
        return model in output
    except Exception as e:
        logger.error(f"❌ Error checking if {model} is loaded: {e}")
        return False


def unload_model(model: str) -> bool:
    """Unload a model to free memory"""
    try:
        logger.info(f"⚠️ Unloading {model} to save memory...")
        subprocess.run(["ollama", "stop", model], check=True, capture_output=True)
        logger.info(f"✅ {model} unloaded successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error unloading {model}: {e}")
        return False


def load_model(model: str) -> bool:
    """Load a model into memory with a ping request"""
    logger.info(f"🔄 Loading {model} into memory...")
    try:
        response = requests.post(OLLAMA_API, json={
            "model": model,
            "prompt": "ping",
            "stream": False
        }, timeout=60)
        
        if response.status_code == 200:
            logger.info(f"✅ {model} warmed up successfully")
            last_used[model] = time.time()
            return True
        else:
            logger.error(f"❌ Failed to warm {model}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error warming {model}: {e}")
        return False


def adaptive_keep_alive():
    """Main adaptive keep-alive loop that manages models based on memory usage"""
    logger.info("🚀 Starting adaptive warm-up and keep-alive service...")
    
    # Initial warm-up of high priority models
    high_priority_models = [m for m in MODELS if m["priority"] == 2]
    for model_info in high_priority_models:
        load_model(model_info["name"])
    
    # Adaptive keep-alive loop
    while True:
        try:
            # Sort models by priority (highest first)
            sorted_models = sorted(MODELS, key=lambda x: -x["priority"])
            
            for model_info in sorted_models:
                name = model_info["name"]
                priority = model_info["priority"]
                
                # Check memory and unload if needed
                if not memory_ok():
                    logger.warning("MemoryWarning: Memory usage high, considering model unload...")
                    # Find lowest priority, least recently used model to unload
                    loaded_models = [m for m in MODELS if is_model_loaded(m["name"])]
                    if loaded_models:
                        # Sort by priority first, then by last used time (LRU)
                        unload_candidate = sorted(
                            loaded_models, 
                            key=lambda x: (x["priority"], last_used.get(x["name"], 0))
                        )[0]
                        
                        # Only unload if it's not a high priority model
                        if unload_candidate["priority"] < 2 and is_model_loaded(unload_candidate["name"]):
                            unload_model(unload_candidate["name"])
                
                # Load/warm model if not loaded
                if not is_model_loaded(name):
                    # For high priority models, try to make room if needed
                    if priority == 2 and not memory_ok():
                        # Try to unload a lower priority model first
                        lower_models = [m for m in MODELS if m["priority"] < 2 and is_model_loaded(m["name"])]
                        if lower_models:
                            unload_model(lower_models[0]["name"])
                    
                    load_model(name)
                else:
                    logger.info(f"💡 {name} is alive, sending keep-alive ping...")
                    load_model(name)
            
            logger.info(f"😴 Sleeping for {KEEPALIVE_INTERVAL} seconds...")
            time.sleep(KEEPALIVE_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("🛑 Service interrupted by user")
            break
        except Exception as e:
            logger.error(f"❌ Error in adaptive keep-alive loop: {e}")
            time.sleep(30)  # Wait before retrying

if __name__ == "__main__":
    if not PSUTIL_AVAILABLE:
        logger.warning("psutil not available. Running in basic mode without memory awareness.")
        logger.warning("Install psutil for full adaptive memory management: pip install psutil")
    
    adaptive_keep_alive()
