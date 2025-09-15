"""
Version Service API Endpoints

This module provides FastAPI endpoints for the VersionService functionality.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from services.version_service import VersionService, make_version_service_from_env, Version, DiffResult

# Pydantic models for request/response
class CreateSnapshotRequest(BaseModel):
    node_id: str
    author: str
    reason: str
    content_snapshot: Optional[dict] = None
    diff_summary: Optional[str] = None
    diff_patch: Optional[List[dict]] = None
    parent_commit_id: Optional[str] = None

class CreateSnapshotResponse(BaseModel):
    commit_id: str
    message: str

class GetVersionsResponse(BaseModel):
    versions: List[Version]
    message: str

class GetVersionResponse(BaseModel):
    version: Version
    message: str

class GetDiffRequest(BaseModel):
    commit_a: str
    commit_b: str

class GetDiffResponse(BaseModel):
    diff: DiffResult
    message: str

class RollbackRequest(BaseModel):
    node_id: str
    commit_id: str

class RollbackResponse(BaseModel):
    success: bool
    message: str

class VersionHistoryResponse(BaseModel):
    node_id: str
    versions: List[dict]  # Simplified version info for frontend
    current_commit_id: Optional[str]

# Create router
router = APIRouter(prefix="/versions", tags=["versions"])

def get_version_service():
    """Dependency to get VersionService instance"""
    service = make_version_service_from_env()
    try:
        yield service
    finally:
        service.close()

@router.post("/snapshots", response_model=CreateSnapshotResponse)
async def create_snapshot(
    request: CreateSnapshotRequest,
    version_service: VersionService = Depends(get_version_service)
):
    """
    Create a snapshot of a node's current state.
    """
    try:
        commit_id = version_service.create_snapshot(
            node_id=request.node_id,
            author=request.author,
            reason=request.reason,
            content_snapshot=request.content_snapshot,
            diff_summary=request.diff_summary,
            diff_patch=request.diff_patch,
            parent_commit_id=request.parent_commit_id
        )
        return CreateSnapshotResponse(
            commit_id=commit_id,
            message="Snapshot created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create snapshot: {str(e)}")

@router.get("/nodes/{node_id}", response_model=GetVersionsResponse)
async def get_versions(
    node_id: str,
    version_service: VersionService = Depends(get_version_service)
):
    """
    Retrieve all versions for a specific node.
    """
    try:
        versions = version_service.get_versions(node_id)
        return GetVersionsResponse(
            versions=versions,
            message=f"Retrieved {len(versions)} versions for node {node_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve versions: {str(e)}")

@router.get("/{commit_id}", response_model=GetVersionResponse)
async def get_version(
    commit_id: str,
    version_service: VersionService = Depends(get_version_service)
):
    """
    Retrieve a specific version by commit ID.
    """
    try:
        version = version_service.get_version(commit_id)
        if not version:
            raise HTTPException(status_code=404, detail=f"Version {commit_id} not found")
        
        return GetVersionResponse(
            version=version,
            message=f"Retrieved version {commit_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve version: {str(e)}")

@router.post("/diff", response_model=GetDiffResponse)
async def get_diff(
    request: GetDiffRequest,
    version_service: VersionService = Depends(get_version_service)
):
    """
    Generate a diff between two versions.
    """
    try:
        diff = version_service.get_diff(request.commit_a, request.commit_b)
        return GetDiffResponse(
            diff=diff,
            message=f"Generated diff between {request.commit_a} and {request.commit_b}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate diff: {str(e)}")

@router.post("/rollback", response_model=RollbackResponse)
async def rollback(
    request: RollbackRequest,
    version_service: VersionService = Depends(get_version_service)
):
    """
    Rollback a node to a specific version.
    """
    try:
        success = version_service.rollback(request.node_id, request.commit_id)
        return RollbackResponse(
            success=success,
            message=f"Rolled back node {request.node_id} to commit {request.commit_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rollback: {str(e)}")

@router.get("/nodes/{node_id}/history", response_model=VersionHistoryResponse)
async def get_version_history(
    node_id: str,
    version_service: VersionService = Depends(get_version_service)
):
    """
    Get simplified version history for a node (for frontend display).
    """
    try:
        # Get the current node info
        # This would require access to the nodes table or a node service
        # For now, we'll just get the versions
        versions = version_service.get_versions(node_id)
        
        # Simplify version info for frontend
        simplified_versions = [
            {
                "commit_id": v.commit_id,
                "author": v.author,
                "reason": v.reason,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "diff_summary": v.diff_summary
            }
            for v in versions
        ]
        
        # Get current commit ID from node (simplified)
        current_commit_id = versions[0].commit_id if versions else None
        
        return VersionHistoryResponse(
            node_id=node_id,
            versions=simplified_versions,
            current_commit_id=current_commit_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve version history: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the version service.
    """
    return {"status": "healthy", "service": "version_service"}
