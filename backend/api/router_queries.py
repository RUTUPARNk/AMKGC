"""
FastAPI routes for Router Agent queries
"""

from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Any, Optional
import asyncio
import logging

# Local imports
from distributed.router import router_agent

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/plan_execution")
async def plan_execution(
    query: str = Body(..., embed=True),
    k: int = Body(5, embed=True),
    max_tokens: int = Body(4096, embed=True),
    provider: Optional[str] = Body(None, embed=True)
):
    """Create an execution plan based on a query using top-k retrieval and token budgeting"""
    try:
        plan_result = await router_agent.plan_execution(query, k, max_tokens)
        # Note: In a more advanced implementation, we would pass the provider to the router agent
        # For now, the provider is handled at the VectorService level
        return plan_result
    except Exception as e:
        logger.error(f"Error planning execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute_plan")
async def execute_plan(
    plan_id: str = Body(..., embed=True),
    pipeline_id: Optional[str] = Body(None, embed=True)
):
    """Execute a previously created plan"""
    try:
        execution_result = await router_agent.execute_plan(plan_id, pipeline_id)
        return execution_result
    except Exception as e:
        logger.error(f"Error executing plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/node_dependencies/{node_id}")
async def get_node_dependencies(node_id: str):
    """Get dependencies for a specific node"""
    try:
        dependencies = router_agent.get_node_dependencies(node_id)
        return {"node_id": node_id, "dependencies": dependencies}
    except Exception as e:
        logger.error(f"Error getting node dependencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/node_subgraph/{node_id}")
async def get_node_subgraph(node_id: str, depth: int = 2):
    """Get a subgraph centered around a specific node"""
    try:
        subgraph = router_agent.get_node_subgraph(node_id, depth)
        return subgraph
    except Exception as e:
        logger.error(f"Error getting node subgraph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update_relevance")
async def update_node_relevance(
    node_id: str = Body(..., embed=True),
    relevance_score: float = Body(..., embed=True)
):
    """Update node relevance score"""
    try:
        success = router_agent.update_node_relevance(node_id, relevance_score)
        return {"node_id": node_id, "success": success}
    except Exception as e:
        logger.error(f"Error updating node relevance: {e}")
        raise HTTPException(status_code=500, detail=str(e))
