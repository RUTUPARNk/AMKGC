from fastapi import APIRouter
from api.endpoints import router as api_router
from api.websocket import router as websocket_router
from api.pipelines import router as pipelines_router
from api.distributed import router as distributed_router
from api.router_queries import router as router_queries_router
from api.merge import router as merge_router
from services.health_service import get_health, get_load_distribution, simulate_failure

# Main API router
router = APIRouter()

# Include all API endpoints
router.include_router(api_router, prefix="/api/v1")
router.include_router(websocket_router, prefix="/api/v1")
router.include_router(pipelines_router, prefix="/api/v1")
router.include_router(distributed_router, prefix="/api/v1")
router.include_router(router_queries_router, prefix="/api/v1")
router.include_router(merge_router, prefix="/api/v1")

# Back-compat simple health
@router.get("/health")
async def health_check():
    """Return service health array"""
    return get_health()

@router.get("/load-distribution")
async def load_distribution():
    """Return load distribution array"""
    return get_load_distribution()

@router.post("/simulate-failure/{service_id}")
async def simulate_failure_route(service_id: str):
    """Simulate service failure and update load distribution."""
    return simulate_failure(service_id, status="unhealthy")

# Root endpoint
@router.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Node LLM System API",
        "version": "1.0.0",
        "description": "A comprehensive node-based LLM system with Ollama integration",
        "endpoints": {
            "health": "/health",
            "load_distribution": "/load-distribution",
            "simulate_failure": "/simulate-failure/{service_id}",
            "api": "/api/v1",
            "docs": "/docs",
            "websocket": "/api/v1/ws",
            "distributed": "/api/v1/distributed",
            "router": "/api/v1/router",
            "merge": "/api/v1/merge"
        }
    } 