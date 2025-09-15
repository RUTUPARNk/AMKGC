"""
Clarification Service API Endpoints

This module provides FastAPI endpoints for the ClarificationService functionality.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from services.clarification_service import (
    ClarificationService, 
    make_clarification_service_from_env, 
    HallucinationIssue, 
    HallucinationRecord
)

# Pydantic models for request/response
class AnalyzeResponseRequest(BaseModel):
    node_id: str
    response_text: str

class AnalyzeResponseResponse(BaseModel):
    issues: List[dict]  # Simplified representation of HallucinationIssue
    message: str
    count: int

class GetHallucinationsResponse(BaseModel):
    hallucinations: List[dict]  # Simplified representation of HallucinationRecord
    message: str
    count: int

class CreateClarificationNodeRequest(BaseModel):
    parent_node_id: str
    snippet: str

class CreateClarificationNodeResponse(BaseModel):
    child_id: str
    message: str

class ResolveHallucinationRequest(BaseModel):
    resolution_notes: Optional[str] = None

class ResolveHallucinationResponse(BaseModel):
    success: bool
    message: str

class HallucinationSummaryResponse(BaseModel):
    node_id: str
    total_hallucinations: int
    unresolved_hallucinations: int
    types_breakdown: dict

# Create router
router = APIRouter(prefix="/clarification", tags=["clarification"])

def get_clarification_service():
    """Dependency to get ClarificationService instance"""
    service = make_clarification_service_from_env()
    try:
        yield service
    finally:
        service.close()

@router.post("/analyze", response_model=AnalyzeResponseResponse)
async def analyze_response(
    request: AnalyzeResponseRequest,
    clarification_service: ClarificationService = Depends(get_clarification_service)
):
    """
    Analyze an LLM response for potential hallucinations or knowledge gaps.
    """
    try:
        issues = await clarification_service.analyze_response(
            node_id=request.node_id,
            response_text=request.response_text
        )
        
        # Convert issues to serializable format
        serialized_issues = [
            {
                "type": issue.type.value,
                "snippet": issue.snippet,
                "confidence": issue.confidence,
                "explanation": issue.explanation
            }
            for issue in issues
        ]
        
        return AnalyzeResponseResponse(
            issues=serialized_issues,
            message=f"Analyzed response, found {len(issues)} potential issues",
            count=len(issues)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze response: {str(e)}")

@router.get("/node/{node_id}", response_model=GetHallucinationsResponse)
async def get_hallucinations(
    node_id: str,
    unresolved_only: bool = True,
    clarification_service: ClarificationService = Depends(get_clarification_service)
):
    """
    Retrieve hallucination records for a specific node.
    """
    try:
        records = await clarification_service.get_hallucinations(node_id, unresolved_only)
        
        # Convert records to serializable format
        serialized_records = [
            {
                "id": record.id,
                "node_id": record.node_id,
                "type": record.type.value,
                "snippet": record.snippet,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "resolved": record.resolved,
                "resolution_notes": record.resolution_notes
            }
            for record in records
        ]
        
        return GetHallucinationsResponse(
            hallucinations=serialized_records,
            message=f"Retrieved {len(records)} hallucination records for node {node_id}",
            count=len(records)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve hallucinations: {str(e)}")

@router.post("/node/{node_id}/child", response_model=CreateClarificationNodeResponse)
async def create_clarification_node(
    node_id: str,
    request: CreateClarificationNodeRequest,
    clarification_service: ClarificationService = Depends(get_clarification_service)
):
    """
    Auto-create a child node flagged for clarification.
    """
    try:
        child_id = await clarification_service.create_clarification_node(
            parent_node_id=request.parent_node_id,
            snippet=request.snippet
        )
        
        return CreateClarificationNodeResponse(
            child_id=child_id,
            message=f"Created clarification node {child_id} for parent {request.parent_node_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create clarification node: {str(e)}")

@router.post("/hallucination/{hallucination_id}/resolve", response_model=ResolveHallucinationResponse)
async def resolve_hallucination(
    hallucination_id: str,
    request: ResolveHallucinationRequest,
    clarification_service: ClarificationService = Depends(get_clarification_service)
):
    """
    Mark a hallucination as resolved.
    """
    try:
        success = await clarification_service.resolve_hallucination(
            hallucination_id=hallucination_id,
            resolution_notes=request.resolution_notes
        )
        
        if success:
            return ResolveHallucinationResponse(
                success=True,
                message=f"Resolved hallucination {hallucination_id}"
            )
        else:
            raise HTTPException(status_code=404, detail=f"Hallucination {hallucination_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve hallucination: {str(e)}")

@router.get("/node/{node_id}/summary", response_model=HallucinationSummaryResponse)
async def get_hallucination_summary(
    node_id: str,
    clarification_service: ClarificationService = Depends(get_clarification_service)
):
    """
    Get a summary of hallucinations for a node.
    """
    try:
        # Get all hallucinations for the node
        records = await clarification_service.get_hallucinations(node_id, unresolved_only=False)
        
        # Calculate summary statistics
        total_count = len(records)
        unresolved_count = len([r for r in records if not r.resolved])
        
        # Break down by type
        types_breakdown = {}
        for record in records:
            type_name = record.type.value
            if type_name in types_breakdown:
                types_breakdown[type_name] += 1
            else:
                types_breakdown[type_name] = 1
        
        return HallucinationSummaryResponse(
            node_id=node_id,
            total_hallucinations=total_count,
            unresolved_hallucinations=unresolved_count,
            types_breakdown=types_breakdown
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve hallucination summary: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the clarification service.
    """
    return {"status": "healthy", "service": "clarification_service"}
