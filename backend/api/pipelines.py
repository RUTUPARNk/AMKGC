"""
FastAPI routes for pipeline execution
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
import os
import sys

# Add the parent directory to the path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Try to import PipelineExecutor
try:
    from pipeline.executor import PipelineExecutor
except ImportError as e:
    print(f"Error importing PipelineExecutor: {e}")
    # Create a mock executor for testing
    class PipelineExecutor:
        def __init__(self, config_path: str):
            self.graphs = []
        
        async def run_pipeline(self, pipeline_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
            return {"pipeline": pipeline_id, "output": "Mock output", "trace": {}, "status": "mock"}

# Initialize the pipeline executor
# Using a relative path from the backend directory
executor = PipelineExecutor("pipelines/graph_config.json")

router = APIRouter()

@router.post("/run_pipeline")
async def run_pipeline(
    pipeline: str = Body(..., embed=True),
    input_data: Dict[str, Any] = Body(..., embed=True)
):
    """Execute a pipeline by ID with input data"""
    try:
        result = await executor.run_pipeline(pipeline, input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list_pipelines")
async def list_pipelines():
    """List all available pipelines"""
    try:
        pipeline_ids = [graph.get("id") for graph in executor.graphs if graph.get("id")]
        return {"pipelines": pipeline_ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
