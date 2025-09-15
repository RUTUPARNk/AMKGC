import asyncio
import time
import httpx
import os
import sys
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add the parent directory to the path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from config.config import check_database_connection, check_redis_connection, settings
    from .redis_service import RedisService
    from .ollama_warmup import ollama_warmup_service
except ImportError:
    # Fallback implementations for standalone testing
    def check_database_connection():
        return True
    
    def check_redis_connection():
        return True
    
    class Settings:
        REDIS_URL = "redis://localhost:6379"
        OLLAMA_URL = "http://localhost:11434"
        OLLAMA_MODEL = "llama3"
    
    settings = Settings()
    
    class RedisService:
        def __init__(self, url):
            pass
        
        def set_cache(self, key, value, prefix=""):
            pass
        
        def get_cache(self, key, prefix=""):
            return None
    
    _redis = RedisService(settings.REDIS_URL)
    
    # Mock ollama_warmup_service for standalone testing
    class MockOllamaWarmupService:
        def check_readiness(self):
            return True
    
    ollama_warmup_service = MockOllamaWarmupService()

# In-memory cache for quick reads (also mirrored to Redis)
_health_state: Dict[str, Dict[str, Any]] = {}
_load_distribution: List[Dict[str, Any]] = []

# Default services to monitor
DEFAULT_SERVICES: List[Dict[str, Any]] = [
    {"id": "database", "name": "Database", "status": "unknown"},
    {"id": "redis", "name": "Redis", "status": "unknown"},
    {"id": "llm", "name": "LLM Service", "status": "unknown"},
    {"id": "auth", "name": "Auth Service", "status": "unknown"},
    {"id": "conflict", "name": "Conflict Service", "status": "unknown"},
    {"id": "ollama", "name": "Ollama Service", "status": "unknown"},
]

REDIS_HEALTH_KEY = "health:services"
REDIS_LOAD_KEY = "health:load_distribution"

_redis = RedisService(settings.REDIS_URL)


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _measure(fn) -> Tuple[bool, float]:
    start = time.perf_counter()
    ok = False
    try:
        ok = bool(fn())
    except Exception:
        ok = False
    latency_ms = (time.perf_counter() - start) * 1000.0
    return ok, latency_ms


def _check_ollama_health() -> bool:
    """Check if Ollama is healthy and model is loaded"""
    try:
        # Use the improved readiness check from ollama_warmup_service
        # This checks both API availability and model presence
        return ollama_warmup_service.check_readiness()
    except Exception:
        return False

def _check_ollama_warmup() -> Tuple[bool, float]:
    """Check if Ollama model is warmed up by sending a small request"""
    try:
        import requests
        start_time = time.perf_counter()
        # Send a small warmup request
        response = requests.post(
            f"{settings.OLLAMA_URL}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": "hi",
                "stream": False
            },
            timeout=10.0
        )
        end_time = time.perf_counter()
        latency = (end_time - start_time) * 1000.0  # Convert to milliseconds
        return response.status_code == 200, latency
    except Exception:
        return False, 0.0


def _check_service(service_id: str) -> Tuple[str, float]:
    if service_id == "database":
        ok, ms = _measure(check_database_connection)
        return ("healthy" if ok else "unhealthy"), ms
    if service_id == "redis":
        ok, ms = _measure(check_redis_connection)
        return ("healthy" if ok else "unhealthy"), ms
    if service_id == "llm":
        # Placeholder: consider adding a real ping to LLM provider
        ok, ms = _measure(lambda: True)
        return ("healthy" if ok else "unhealthy"), ms
    if service_id == "auth":
        ok, ms = _measure(lambda: True)
        return ("healthy" if ok else "unhealthy"), ms
    if service_id == "conflict":
        ok, ms = _measure(lambda: True)
        return ("healthy" if ok else "unhealthy"), ms
    if service_id == "ollama":
        ok = _check_ollama_health()
        warmup_ok, latency = _check_ollama_warmup()
        if ok and warmup_ok:
            return "healthy", latency
        else:
            return "unhealthy", 0.0
    # Unknown service
    return "unknown", 0.0


def _recompute_load_distribution() -> List[Dict[str, Any]]:
    global _load_distribution
    healthy_services = [s for s in _health_state.values() if s.get("status") == "healthy"]
    if not healthy_services:
        _load_distribution = []
        _redis.set_cache(REDIS_LOAD_KEY, _load_distribution, prefix="app")
        return _load_distribution

    share = round(100.0 / len(healthy_services), 2)
    remaining = 100.0 - share * (len(healthy_services) - 1)

    distribution: List[Dict[str, Any]] = []
    for idx, s in enumerate(healthy_services):
        pct = remaining if idx == len(healthy_services) - 1 else share
        distribution.append({"service": s["name"], "percentageLoad": pct})

    _load_distribution = distribution
    _redis.set_cache(REDIS_LOAD_KEY, distribution, prefix="app")
    return distribution


def get_health() -> List[Dict[str, Any]]:
    # Try Redis first
    data = _redis.get_cache(REDIS_HEALTH_KEY, prefix="app")
    if isinstance(data, list) and data:
        # also warm in-memory cache
        for item in data:
            _health_state[item["id"]] = item
        return data

    # If nothing in Redis, bootstrap from defaults
    if not _health_state:
        for s in DEFAULT_SERVICES:
            _health_state[s["id"]] = {
                "id": s["id"],
                "name": s["name"],
                "status": s.get("status", "unknown"),
                "latency": 0.0,
                "lastUpdated": _now_iso(),
            }
    return list(_health_state.values())


def get_load_distribution() -> List[Dict[str, Any]]:
    data = _redis.get_cache(REDIS_LOAD_KEY, prefix="app")
    if isinstance(data, list):
        _load_distribution.clear()
        _load_distribution.extend(data)
        return data
    return _load_distribution


def simulate_failure(service_id: str, status: str = "unhealthy") -> List[Dict[str, Any]]:
    if service_id not in _health_state:
        # if not known, add it
        _health_state[service_id] = {
            "id": service_id,
            "name": service_id.capitalize(),
            "status": status,
            "latency": 0.0,
            "lastUpdated": _now_iso(),
        }
    else:
        _health_state[service_id]["status"] = status
        _health_state[service_id]["lastUpdated"] = _now_iso()

    # Persist and recompute load
    _redis.set_cache(REDIS_HEALTH_KEY, list(_health_state.values()), prefix="app")
    _recompute_load_distribution()
    return list(_health_state.values())


async def _health_loop(interval_seconds: int = 10) -> None:
    # Initialize defaults if needed
    if not _health_state:
        for s in DEFAULT_SERVICES:
            _health_state[s["id"]] = {
                "id": s["id"],
                "name": s["name"],
                "status": "unknown",
                "latency": 0.0,
                "lastUpdated": _now_iso(),
            }

    while True:
        try:
            for service_id, service in list(_health_state.items()):
                status, latency = _check_service(service_id)
                service["status"] = status
                service["latency"] = round(latency, 2)
                service["lastUpdated"] = _now_iso()

            # Persist to Redis
            _redis.set_cache(REDIS_HEALTH_KEY, list(_health_state.values()), prefix="app")
            # Recompute load distribution
            _recompute_load_distribution()
        except Exception:
            # Avoid crashing the loop
            pass

        await asyncio.sleep(interval_seconds)


_health_task: Optional[asyncio.Task] = None


def start_background_health_checks(interval_seconds: int = 10) -> None:
    global _health_task
    if _health_task and not _health_task.done():
        return
    try:
        loop = asyncio.get_event_loop()
        _health_task = loop.create_task(_health_loop(interval_seconds))
    except RuntimeError:
        # Fallback if no running loop yet (e.g., in some server setups)
        asyncio.ensure_future(_health_loop(interval_seconds)) 