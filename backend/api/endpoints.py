from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import logging

from config.config import get_db, settings, get_rate_limit_config
from services.auth_service import AuthService
from services.llm_service import LLMService
from services.llm_ollama import list_ollama_models
from services.conflict_service import ConflictService
from services.redis_service import RedisService
from models.node import Node
from services.health_service import get_health, get_load_distribution, simulate_failure
from api.vector_endpoints import router as vector_router
from api.version_endpoints import router as version_router
from api.clarification_endpoints import router as clarification_router
from api.continuation_endpoints import router as continuation_router

# Configure logging
logger = logging.getLogger(__name__)

# Initialize services
auth_service = AuthService(settings.REDIS_URL)
llm_service = LLMService(settings.REDIS_URL)
conflict_service = ConflictService(settings.REDIS_URL)
redis_service = RedisService(settings.REDIS_URL)

# Security
security = HTTPBearer()

# Create router
router = APIRouter()

# WebSocket connections
active_connections: List[WebSocket] = []

async def broadcast_message(message: Dict[str, Any]):
    """Broadcast message to all connected WebSocket clients"""
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error broadcasting to WebSocket: {e}")
            disconnected.append(connection)
    
    # Remove disconnected clients
    for connection in disconnected:
        active_connections.remove(connection)

# Dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        user_data = auth_service.verify_token(token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Check if token is blacklisted
        if auth_service.is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        return user_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

async def check_rate_limit(user: Dict[str, Any] = Depends(get_current_user)):
    """Check rate limit for API calls"""
    user_id = user.get('user_id', 'anonymous')
    rate_config = get_rate_limit_config('api')
    
    rate_result = redis_service.check_rate_limit(
        user_id, 'api', rate_config['max_requests'], rate_config['window']
    )
    
    if not rate_result['allowed']:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry after {rate_result['retry_after']} seconds"
        )

# Authentication endpoints
@router.post("/auth/register", response_model=Dict[str, Any])
async def register_user(
    username: str,
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        result = auth_service.register_user(username, email, password)
        return {"message": "User registered successfully", "user_id": result['user_id']}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/auth/login", response_model=Dict[str, Any])
async def login_user(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    """Login user and return JWT token"""
    try:
        result = auth_service.login_user(username, password)
        return {
            "access_token": result['access_token'],
            "refresh_token": result['refresh_token'],
            "token_type": "bearer",
            "user": result['user']
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/auth/refresh", response_model=Dict[str, Any])
async def refresh_token(
    refresh_token: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Refresh JWT token"""
    try:
        new_token = auth_service.refresh_token(refresh_token)
        return {"access_token": new_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/auth/logout")
async def logout_user(
    user: Dict[str, Any] = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Logout user and blacklist token"""
    try:
        auth_service.logout_user(credentials.credentials)
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Node management endpoints
@router.post("/nodes", response_model=Dict[str, Any])
async def create_node(
    name: str,
    node_type: str,
    context_window: str = "",
    parent_node_id: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new node"""
    try:
        # Create node logic here (simplified)
        node_data = {
            "name": name,
            "node_type": node_type,
            "context_window": context_window,
            "parent_node_id": parent_node_id,
            "created_by": user['user_id']
        }
        
        # Broadcast to WebSocket clients
        await broadcast_message({
            "type": "node_created",
            "data": node_data
        })
        
        return {"message": "Node created successfully", "node": node_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/nodes", response_model=List[Dict[str, Any]])
async def get_nodes(
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all nodes"""
    try:
        # Get nodes logic here (simplified)
        nodes = []  # Replace with actual database query
        return nodes
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/nodes/{node_id}", response_model=Dict[str, Any])
async def get_node(
    node_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific node"""
    try:
        # Get node logic here (simplified)
        node = {}  # Replace with actual database query
        return node
    except Exception as e:
        raise HTTPException(status_code=404, detail="Node not found")

@router.put("/nodes/{node_id}", response_model=Dict[str, Any])
async def update_node(
    node_id: str,
    name: Optional[str] = None,
    context_window: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a node"""
    try:
        # Update node logic here (simplified)
        node_data = {"id": node_id, "name": name, "context_window": context_window}
        
        # Broadcast to WebSocket clients
        await broadcast_message({
            "type": "node_updated",
            "data": node_data
        })
        
        return {"message": "Node updated successfully", "node": node_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/nodes/{node_id}")
async def delete_node(
    node_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a node"""
    try:
        # Delete node logic here (simplified)
        
        # Broadcast to WebSocket clients
        await broadcast_message({
            "type": "node_deleted",
            "data": {"node_id": node_id}
        })
        
        return {"message": "Node deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/nodes/graph", response_model=Dict[str, Any])
async def get_node_graph(
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get node graph data"""
    try:
        # Get graph data logic here (simplified)
        graph_data = {"nodes": [], "edges": []}
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/nodes/search/{query}", response_model=List[Dict[str, Any]])
async def search_nodes(
    query: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search nodes"""
    try:
        # Search logic here (simplified)
        results = []
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# LLM integration endpoints
@router.post("/llm/generate", response_model=Dict[str, Any])
async def generate_content(
    prompt: str,
    model: str = "ollama",
    user: Dict[str, Any] = Depends(get_current_user),
    rate_limit: None = Depends(check_rate_limit)
):
    """Generate content using LLM"""
    try:
        result = llm_service.generate(prompt, model)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/llm/schema", response_model=Dict[str, Any])
async def generate_schema(
    table_name: str,
    description: str = "",
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Generate database schema"""
    try:
        result = llm_service.generate_schema(table_name, description)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/llm/policy", response_model=Dict[str, Any])
async def generate_policy(
    policy_type: str,
    context: str = "",
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Generate policy rules"""
    try:
        result = llm_service.generate_policy(policy_type, context)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/ollama/models", response_model=Dict[str, Any])
async def get_ollama_models(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get list of available Ollama models"""
    try:
        models = await list_ollama_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/nodes/{node_id}/generate", response_model=Dict[str, Any])
async def generate_node_context(
    node_id: str,
    prompt: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate context for a specific node"""
    try:
        result = llm_service.generate(prompt)
        
        # Broadcast to WebSocket clients
        await broadcast_message({
            "type": "node_context_generated",
            "data": {"node_id": node_id, "context": result['content']}
        })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Conflict management endpoints
@router.post("/nodes/conflicts/detect", response_model=Dict[str, Any])
async def detect_conflicts(
    node1_id: str,
    node2_id: str,
    user_feedback: str = "",
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detect conflicts between two nodes"""
    try:
        result = conflict_service.detect_conflicts(db, node1_id, node2_id, user_feedback)
        
        # Broadcast to WebSocket clients
        await broadcast_message({
            "type": "conflict_detected",
            "data": result
        })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/nodes/conflicts/resolve", response_model=Dict[str, Any])
async def create_conflict_resolution(
    conflict_id: str,
    resolution_context: str,
    user_feedback: str = "",
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a conflict resolution node"""
    try:
        result = conflict_service.resolve_conflict(
            db, conflict_id, resolution_context, user_feedback
        )
        
        # Broadcast to WebSocket clients
        await broadcast_message({
            "type": "conflict_resolved",
            "data": result
        })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/conflicts/{conflict_id}/resolve", response_model=Dict[str, Any])
async def resolve_conflict(
    conflict_id: str,
    resolution_context: str,
    user_feedback: str = "",
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resolve a specific conflict"""
    try:
        result = conflict_service.resolve_conflict(
            db, conflict_id, resolution_context, user_feedback
        )
        
        # Broadcast to WebSocket clients
        await broadcast_message({
            "type": "conflict_resolved",
            "data": result
        })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/conflicts", response_model=List[Dict[str, Any]])
async def get_conflicts(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all conflicts"""
    try:
        conflicts = conflict_service.get_all_conflicts()
        return conflicts
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Token management endpoints
@router.post("/nodes/{node_id}/split", response_model=Dict[str, Any])
async def split_large_context(
    node_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Split large context into smaller chunks"""
    try:
        # Get node context
        node = {}  # Replace with actual database query
        
        # Split context
        chunks = llm_service.split_context(node.get('context_window', ''))
        
        # Broadcast to WebSocket clients
        await broadcast_message({
            "type": "context_split",
            "data": {"node_id": node_id, "chunks": len(chunks)}
        })
        
        return {"chunks": chunks, "total_chunks": len(chunks)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Cache management endpoints
@router.get("/cache", response_model=Dict[str, Any])
async def get_all_cache_entries(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all cache entries"""
    try:
        entries = redis_service.get_all_cache_entries()
        return {"cache": [{"id": k, "value": v} for k, v in entries.items()]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/cache/{key}", response_model=Dict[str, Any])
async def delete_cache_entry(
    key: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a specific cache entry"""
    try:
        result = redis_service.delete_cache(key)
        if result:
            return {"success": True, "message": f"Cache entry '{key}' deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Cache entry '{key}' not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Monitoring endpoints
@router.get("/monitoring/cache-stats", response_model=Dict[str, Any])
async def get_cache_stats(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get cache statistics"""
    try:
        stats = redis_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/monitoring/rate-limits/{action}/{identifier}", response_model=Dict[str, Any])
async def get_rate_limit_info(
    action: str,
    identifier: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get rate limit information"""
    try:
        rate_config = get_rate_limit_config(action)
        rate_result = redis_service.check_rate_limit(
            identifier, action, rate_config['max_requests'], rate_config['window']
        )
        return rate_result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Health and load distribution endpoints
@router.get("/health", response_model=List[Dict[str, Any]])
async def api_health():
    """Return array of service health: [{ id, name, status, latency, lastUpdated }]"""
    return get_health()

@router.get("/load-distribution", response_model=List[Dict[str, Any]])
async def api_load_distribution():
    """Return current load distribution: [{ service, percentageLoad }]"""
    return get_load_distribution()

@router.post("/simulate-failure/{service_id}", response_model=List[Dict[str, Any]])
async def api_simulate_failure(service_id: str):
    """Simulate failure for a service and recompute load."""
    # toggle unhealthy; client can also send query param later for custom
    return simulate_failure(service_id, status="unhealthy")

# Include the vector router
router.include_router(vector_router)

# Include the version router
router.include_router(version_router)

# Include the clarification router
router.include_router(clarification_router)

# Include the continuation router
router.include_router(continuation_router)