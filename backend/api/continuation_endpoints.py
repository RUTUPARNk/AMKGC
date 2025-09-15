"""
Continuation Service API Endpoints

This module provides FastAPI endpoints for the ContinuationService functionality.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from services.continuation_service import (
    ContinuationService, 
    make_continuation_service_from_env, 
    NodeChain
)

# Pydantic models for request/response
class CheckAndSplitRequest(BaseModel):
    node_id: str
    new_message: str
    token_limit: Optional[int] = None

class CheckAndSplitResponse(BaseModel):
    target_node_id: str
    message: str
    action: str  # "added" or "split"

class GetChainResponse(BaseModel):
    root_node_id: str
    nodes: List[dict]
    message: str
    count: int

class GetActiveNodeResponse(BaseModel):
    node: dict
    message: str

class NodeSummary(BaseModel):
    id: str
    name: str
    node_type: str
    status: str
    created_at: str
    continuation_of: Optional[str] = None

class ContinuationChainSummaryResponse(BaseModel):
    root_node_id: str
    chain: List[NodeSummary]
    message: str
    count: int

# Create router
router = APIRouter(prefix="/continuation", tags=["continuation"])

def get_continuation_service():
    """Dependency to get ContinuationService instance"""
    service = make_continuation_service_from_env()
    try:
        yield service
    finally:
        service.close()

@router.post("/check-and-split", response_model=CheckAndSplitResponse)
async def check_and_split(
    request: CheckAndSplitRequest,
    continuation_service: ContinuationService = Depends(get_continuation_service)
):
    """
    Check if a node needs to be split due to token overflow and create a continuation node if needed.
    """
    try:
        target_node_id = await continuation_service.check_and_split(
            node_id=request.node_id,
            new_message=request.new_message,
            token_limit=request.token_limit
        )
        
        action = "split" if target_node_id != request.node_id else "added"
        
        return CheckAndSplitResponse(
            target_node_id=target_node_id,
            action=action,
            message=f"Message will be {'added to continuation node' if action == 'split' else 'added to original node'}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check and split node: {str(e)}")

@router.get("/chain/{node_id}", response_model=GetChainResponse)
async def get_chain(
    node_id: str,
    continuation_service: ContinuationService = Depends(get_continuation_service)
):
    """
    Get the full continuation chain for a node.
    """
    try:
        chain = await continuation_service.get_chain(node_id)
        
        # Convert nodes to serializable format
        serialized_nodes = []
        for node in chain.nodes:
            serialized_node = {
                "id": node["id"],
                "name": node["name"],
                "context_window": node["context_window"],
                "parent_node": node.get("parent_node"),
                "child_nodes": node["child_nodes"],
                "llm_model_used": node.get("llm_model_used"),
                "node_type": node["node_type"],
                "status": node["status"],
                "created_at": node["created_at"].isoformat() if node["created_at"] else None,
                "updated_at": node["updated_at"].isoformat() if node["updated_at"] else None,
                "continuation_of": node.get("continuation_of"),
                "token_count": node.get("token_count", 0)
            }
            serialized_nodes.append(serialized_node)
        
        return GetChainResponse(
            root_node_id=chain.root_node_id,
            nodes=serialized_nodes,
            message=f"Retrieved continuation chain with {len(serialized_nodes)} nodes",
            count=len(serialized_nodes)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get continuation chain: {str(e)}")

@router.get("/active/{node_id}", response_model=GetActiveNodeResponse)
async def get_active_node(
    node_id: str,
    continuation_service: ContinuationService = Depends(get_continuation_service)
):
    """
    Get the active (latest) node in a continuation chain.
    """
    try:
        node = await continuation_service.get_active_node(node_id)
        
        # Convert node to serializable format
        serialized_node = {
            "id": node["id"],
            "name": node["name"],
            "context_window": node["context_window"],
            "parent_node": node.get("parent_node"),
            "child_nodes": node["child_nodes"],
            "llm_model_used": node.get("llm_model_used"),
            "node_type": node["node_type"],
            "status": node["status"],
            "created_at": node["created_at"].isoformat() if node["created_at"] else None,
            "updated_at": node["updated_at"].isoformat() if node["updated_at"] else None,
            "continuation_of": node.get("continuation_of"),
            "token_count": node.get("token_count", 0)
        }
        
        return GetActiveNodeResponse(
            node=serialized_node,
            message=f"Retrieved active node {node['id']} in continuation chain"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active node: {str(e)}")

@router.get("/chain/{node_id}/summary", response_model=ContinuationChainSummaryResponse)
async def get_chain_summary(
    node_id: str,
    continuation_service: ContinuationService = Depends(get_continuation_service)
):
    """
    Get a summary of the continuation chain for a node.
    """
    try:
        chain = await continuation_service.get_chain(node_id)
        
        # Create summary of nodes
        summaries = []
        for node in chain.nodes:
            summaries.append(NodeSummary(
                id=node["id"],
                name=node["name"],
                node_type=node["node_type"],
                status=node["status"],
                created_at=node["created_at"].isoformat() if node["created_at"] else None,
                continuation_of=node.get("continuation_of")
            ))
        
        return ContinuationChainSummaryResponse(
            root_node_id=chain.root_node_id,
            chain=summaries,
            message=f"Continuation chain summary with {len(summaries)} nodes",
            count=len(summaries)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chain summary: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the continuation service.
    """
    return {"status": "healthy", "service": "continuation_service"}
