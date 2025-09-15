"""
Vector Service API Endpoints

This module provides FastAPI endpoints for the VectorService functionality.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from services.vector_services import VectorService, make_vector_service_from_env, RetrievedFragment

# Pydantic models for request/response
class AddFragmentRequest(BaseModel):
    node_id: str
    text: str
    commit_id: Optional[str] = None
    offset: int = 0

class AddFragmentResponse(BaseModel):
    fragment_id: str
    message: str

class AddFragmentsBulkRequest(BaseModel):
    node_id: str
    items: List[tuple[str, Optional[str], int]]  # list of (text, commit_id, offset)

class AddFragmentsBulkResponse(BaseModel):
    fragment_ids: List[str]
    message: str

class SearchRequest(BaseModel):
    node_id: str
    query: str
    top_k: Optional[int] = None
    since_commit: Optional[str] = None

class SearchResponse(BaseModel):
    fragments: List[RetrievedFragment]
    message: str

class SemanticSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    exclude_node_id: Optional[str] = None
    provider: Optional[str] = None  # 'ollama', 'openai', or None (default)

class SemanticSearchResponse(BaseModel):
    fragments: List[RetrievedFragment]
    message: str

class DeleteFragmentsResponse(BaseModel):
    deleted_count: int
    message: str

# Create router
router = APIRouter(prefix="/vector", tags=["vector"])

def get_vector_service():
    """Dependency to get VectorService instance"""
    service = make_vector_service_from_env()
    try:
        yield service
    finally:
        service.close()

@router.post("/fragments", response_model=AddFragmentResponse)
async def add_fragment(
    request: AddFragmentRequest,
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Add a text fragment with its embedding to the vector store.
    """
    try:
        fragment_id = vector_service.add_fragment(
            node_id=request.node_id,
            text=request.text,
            commit_id=request.commit_id,
            offset=request.offset
        )
        return AddFragmentResponse(
            fragment_id=fragment_id,
            message="Fragment added successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add fragment: {str(e)}")

@router.post("/fragments/bulk", response_model=AddFragmentsBulkResponse)
async def add_fragments_bulk(
    request: AddFragmentsBulkRequest,
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Add multiple text fragments with their embeddings to the vector store.
    """
    try:
        fragment_ids = vector_service.add_fragments_bulk(
            node_id=request.node_id,
            items=request.items
        )
        return AddFragmentsBulkResponse(
            fragment_ids=fragment_ids,
            message=f"{len(fragment_ids)} fragments added successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add fragments: {str(e)}")

@router.post("/search", response_model=SearchResponse)
async def search_fragments(
    request: SearchRequest,
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Search for relevant fragments using vector similarity.
    """
    try:
        fragments = vector_service.search(
            node_id=request.node_id,
            query=request.query,
            top_k=request.top_k,
            since_commit=request.since_commit
        )
        return SearchResponse(
            fragments=fragments,
            message=f"Found {len(fragments)} relevant fragments"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/search/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Search across all nodes/commits semantically using vector similarity.
    Returns fragments ranked by similarity score.
    """
    try:
        # Note: For now, the provider is handled at the VectorService level
        # In a more advanced implementation, we might want to dynamically switch providers
        fragments = vector_service.global_search(
            query=request.query,
            top_k=request.top_k,
            exclude_node_id=request.exclude_node_id,
            provider=request.provider
        )
        return SemanticSearchResponse(
            fragments=fragments,
            message=f"Found {len(fragments)} relevant fragments across all nodes"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")

@router.delete("/fragments/node/{node_id}", response_model=DeleteFragmentsResponse)
async def delete_node_fragments(
    node_id: str,
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Delete all fragments for a specific node.
    """
    try:
        deleted_count = vector_service.delete_node_fragments(node_id)
        return DeleteFragmentsResponse(
            deleted_count=deleted_count,
            message=f"Deleted {deleted_count} fragments for node {node_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete fragments: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the vector service.
    """
    return {"status": "healthy", "service": "vector_service"}
