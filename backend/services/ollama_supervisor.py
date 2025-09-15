"""
Ollama Supervisor Service

This service monitors the Ollama process and API, automatically recovers from failures,
and logs incidents with timestamps and restart reasons.
"""

import subprocess
import time
import requests
import logging
import sys
import os
import threading
from typing import Dict, List, Optional
from datetime import datetime

# Add the parent directory to the path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Try to import psutil for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil not available. Install with: pip install psutil")

# Import supervisor configuration
try:
    from config.supervisor_config import SupervisorConfig
    CONFIG_AVAILABLE = True
except ImportError:
    # Fallback configuration
    class SupervisorConfig:
        CHECK_INTERVAL = 30
        MEMORY_THRESHOLD = 75.0
        WEBHOOK_URL = ""
        ALERTS_ENABLED = False
        MODELS = [
            {"name": "llama3:latest", "priority": 2},
            {"name": "qwen3:latest", "priority": 1}
        ]
    CONFIG_AVAILABLE = False

class OllamaSupervisorService:
    """Service to monitor and supervise Ollama process with automatic recovery"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", check_interval: int = None):
        self.ollama_url = ollama_url
        self.check_interval = check_interval or SupervisorConfig.CHECK_INTERVAL
        self.supervisor_running = False
        self.supervisor_thread: Optional[threading.Thread] = None
        
        # Alerting configuration (can be extended for email, Slack, Discord, etc.)
        self.webhook_url: Optional[str] = SupervisorConfig.WEBHOOK_URL or None
        self.alert_enabled = SupervisorConfig.ALERTS_ENABLED
        
        # Models configuration
        self.models = SupervisorConfig.MODELS
        
        # Set up supervisor logger
        self.logger = logging.getLogger("ollama_supervisor")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler for supervisor logs
        if not self.logger.handlers:  # Avoid duplicate handlers
            handler = logging.FileHandler("ollama_supervisor.log")
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
            # Also add console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        self.logger.info("Ollama Supervisor Service initialized")
        
    def enable_webhook_alerts(self, webhook_url: str):
        """Enable webhook alerts for incidents"""
        self.webhook_url = webhook_url
        self.alert_enabled = True
        self.logger.info(f"Webhook alerts enabled for URL: {webhook_url}")
        
    def send_webhook_alert(self, incident_type: str, reason: str):
        """Send webhook alert for incident"""
        if not self.alert_enabled or not self.webhook_url:
            return
        
        try:
            payload = {
                "text": f"🚨 Ollama Incident Alert\n\nType: {incident_type}\nReason: {reason}\nTime: {datetime.utcnow().isoformat()}\n\nOllama Supervisor Service"
            }
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                self.logger.info(f"✅ Webhook alert sent successfully for {incident_type}")
            else:
                self.logger.error(f"❌ Failed to send webhook alert: {response.status_code} {response.text}")
        except Exception as e:
            self.logger.error(f"❌ Error sending webhook alert: {e}")
        
        # Models configuration (should match ollama_warmup.py)
        self.models = [
            {"name": "llama3:latest", "priority": 2},
            {"name": "qwen3:latest", "priority": 1}
        ]
        
        self.logger.info("Ollama Supervisor Service initialized")
    
    def is_ollama_running(self) -> bool:
        """Check if Ollama process is running"""
        try:
            # Use tasklist on Windows to check for ollama process
            result = subprocess.run(["tasklist"], capture_output=True, text=True, shell=True)
            return "ollama.exe" in result.stdout.lower()
        except Exception as e:
            self.logger.error(f"Error checking Ollama process: {e}")
            return False
    
    def start_ollama(self) -> bool:
        """Start Ollama service"""
        try:
            self.logger.warning("⚠️ Ollama not running. Starting...")
            # Start Ollama in the background
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(5)  # Wait for server to start
            self.logger.info("✅ Ollama started successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to start Ollama: {e}")
            return False
    
    def stop_ollama(self) -> bool:
        """Stop Ollama service"""
        try:
            self.logger.info("🛑 Stopping Ollama service...")
            # Use taskkill on Windows to stop ollama process
            subprocess.run(["taskkill", "/f", "/im", "ollama.exe"], 
                          capture_output=True, text=True, shell=True)
            time.sleep(2)  # Wait for process to terminate
            self.logger.info("✅ Ollama stopped successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error stopping Ollama: {e}")
            return False
    
    def api_alive(self) -> bool:
        """Check if Ollama API is responding"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"❌ Ollama API not responding: {e}")
            return False
    
    def unload_model(self, model: str) -> bool:
        """Unload a model to free memory"""
        try:
            self.logger.info(f"⚠️ Unloading {model} to save memory...")
            subprocess.run(["ollama", "stop", model], check=True, capture_output=True)
            self.logger.info(f"✅ {model} unloaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error unloading {model}: {e}")
            return False
    
    def load_model(self, model: str) -> bool:
        """Load a model into memory with a ping request"""
        self.logger.info(f"🔄 Loading {model} into memory...")
        try:
            response = requests.post(f"{self.ollama_url}/api/generate", json={
                "model": model, 
                "prompt": "ping", 
                "stream": False
            }, timeout=30)
            
            if response.status_code == 200:
                self.logger.info(f"✅ {model} loaded successfully")
                return True
            else:
                self.logger.error(f"❌ Failed to load {model}: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Error loading {model}: {e}")
            return False
    
    def memory_ok(self) -> bool:
        """Check if memory usage is acceptable"""
        if not PSUTIL_AVAILABLE:
            return True  # If we can't check memory, assume it's OK
        try:
            mem = psutil.virtual_memory()
            # Use configured threshold
            return mem.percent < SupervisorConfig.MEMORY_THRESHOLD
        except Exception as e:
            self.logger.error(f"Error checking memory: {e}")
            return True  # If error, assume OK to avoid blocking
    
    def _supervisor_worker(self):
        """Background worker that monitors Ollama and recovers from failures"""
        self.logger.info("🚀 Ollama Supervisor started")
        
        while self.supervisor_running:
            try:
                # Check 1: Is Ollama process running?
                if not self.is_ollama_running():
                    self.logger.error("❌ Ollama process not running. Restarting...")
                    self.log_incident("process_down", "Ollama process not running")
                    self.start_ollama()
                    # Reload models after restart
                    self._reload_models()
                    continue
                
                # Check 2: Is API responding?
                if not self.api_alive():
                    self.logger.error("❌ Ollama API not responding. Restarting service...")
                    self.log_incident("api_unresponsive", "Ollama API not responding")
                    self.stop_ollama()
                    time.sleep(3)  # Wait for clean shutdown
                    self.start_ollama()
                    # Reload models after restart
                    self._reload_models()
                    continue
                
                # Check 3: Adaptive model management
                self._adaptive_model_management()
                
                # Wait before next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"❌ Error in supervisor loop: {e}")
                time.sleep(self.check_interval)
    
    def _reload_models(self):
        """Reload models after Ollama restart"""
        self.logger.info("🔄 Reloading models after Ollama restart...")
        # Sort models by priority (highest first)
        sorted_models = sorted(self.models, key=lambda x: -x["priority"])
        
        for model_info in sorted_models:
            model_name = model_info["name"]
            self.load_model(model_name)
    
    def _adaptive_model_management(self):
        """Manage models based on memory usage"""
        # Check memory and unload if needed
        if not self.memory_ok():
            self.logger.warning("MemoryWarning: Memory usage high, considering model unload...")
            
            # Try to unload lowest priority model
            sorted_models = sorted(self.models, key=lambda x: x["priority"])
            for model_info in sorted_models:
                if self.unload_model(model_info["name"]):
                    break  # Unloaded one model, that might be enough
    
    def log_incident(self, incident_type: str, reason: str):
        """Log incident with timestamp and reason"""
        timestamp = datetime.utcnow().isoformat()
        self.logger.info(f" INCIDENT [{incident_type}] at {timestamp}: {reason}")
        
        # Send webhook alert if enabled
        self.send_webhook_alert(incident_type, reason)
    
    def start_supervisor(self):
        """Start the supervisor background thread"""
        if self.supervisor_thread and self.supervisor_thread.is_alive():
            self.logger.info("Supervisor is already running")
            return
        
        self.supervisor_running = True
        self.supervisor_thread = threading.Thread(target=self._supervisor_worker, daemon=True)
        self.supervisor_thread.start()
        self.logger.info("Supervisor daemon started")
    
    def stop_supervisor(self):
        """Stop the supervisor background thread"""
        self.supervisor_running = False
        if self.supervisor_thread:
            self.supervisor_thread.join(timeout=5)
        self.logger.info("Supervisor daemon stopped")


# Global instance
ollama_supervisor_service = OllamaSupervisorService()
