"""
FastAPI endpoints for Merge Agent operations
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from pydantic import BaseModel
import logging

from distributed.merge import merge_agent, MergePreview, ApplyResult

logger = logging.getLogger(__name__)

# Pydantic models for request/response
class MergePreviewResponse(BaseModel):
    merge_id: str = None
    text_diff: str = ""
    json_patch: list = []
    diff_summary: str = ""
    impact: dict = {}
    conflict: bool = False
    conflict_node_id: str = None
    error: str = None

class ApplyMergeRequest(BaseModel):
    approver: str

class ApplyMergeResponse(BaseModel):
    success: bool = False
    commit_id: str = None
    error: str = None

# Create router
router = APIRouter()

@router.get("/merge/{child_id}", response_model=MergePreviewResponse)
async def compute_merge(child_id: str):
    """Compute merge preview for a child node"""
    try:
        preview = await merge_agent.compute_merge(child_id)
        return MergePreviewResponse(**preview.to_dict())
    except Exception as e:
        logger.error(f"Error computing merge for {child_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/merge/{child_id}/approve", response_model=ApplyMergeResponse)
async def apply_merge(child_id: str, request: ApplyMergeRequest):
    """Apply an approved merge to update the parent node"""
    try:
        result = await merge_agent.apply_merge(child_id, request.approver)
        return ApplyMergeResponse(**result.to_dict())
    except Exception as e:
        logger.error(f"Error applying merge for {child_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
