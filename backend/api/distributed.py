"""
FastAPI routes for distributed pipeline execution
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
import os
import sys
import json

# Add the parent directory to the path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Try to import DistributedCoordinator
try:
    from distributed.coordinator import DistributedCoordinator
    DISTRIBUTED_AVAILABLE = True
except ImportError as e:
    print(f"Error importing DistributedCoordinator: {e}")
    DISTRIBUTED_AVAILABLE = False
    
    # Create a mock coordinator for testing
    class DistributedCoordinator:
        def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
            pass
        
        async def submit_pipeline_task(self, pipeline_id: str, input_data: Dict[str, Any], 
                                     execution_plan: List[List[str]]) -> str:
            return "mock-task-id"
        
        async def run_distributed_pipeline(self, pipeline_id: str, input_data: Dict[str, Any], 
                                         execution_plan: List[List[str]]) -> Dict[str, Any]:
            return {
                "task_id": "mock-task-id",
                "pipeline_id": pipeline_id,
                "results": {},
                "final_output": "Mock output",
                "status": "completed"
            }
        
        def get_active_agents(self) -> List[Dict[str, Any]]:
            return []
        
        def run_watchdog(self) -> Dict[str, Any]:
            return {
                "health_check": {"active_agents": [], "failed_agents": []},
                "requeued_tasks": {}
            }

# Initialize the distributed coordinator
coordinator = DistributedCoordinator() if DISTRIBUTED_AVAILABLE else DistributedCoordinator()

router = APIRouter()

@router.post("/distributed/run_pipeline")
async def run_distributed_pipeline(
    pipeline_id: str = Body(..., embed=True),
    input_data: Dict[str, Any] = Body(..., embed=True),
    execution_plan: List[List[str]] = Body(..., embed=True)
):
    """Execute a pipeline in distributed mode"""
    try:
        result = await coordinator.run_distributed_pipeline(pipeline_id, input_data, execution_plan)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/distributed/submit_task")
async def submit_distributed_task(
    pipeline_id: str = Body(..., embed=True),
    input_data: Dict[str, Any] = Body(..., embed=True),
    execution_plan: List[List[str]] = Body(..., embed=True)
):
    """Submit a pipeline task for distributed execution"""
    try:
        task_id = await coordinator.submit_pipeline_task(pipeline_id, input_data, execution_plan)
        return {"task_id": task_id, "status": "submitted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/distributed/agents")
async def get_active_agents():
    """Get list of active agents"""
    try:
        agents = coordinator.get_active_agents()
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/distributed/watchdog")
async def run_watchdog():
    """Run watchdog to check for failed agents and requeue tasks"""
    try:
        results = coordinator.run_watchdog()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/distributed/task/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a distributed task"""
    try:
        # Get task monitoring data from Redis
        task_monitor_json = coordinator.redis_client.hget(coordinator.task_monitoring, task_id)
        if not task_monitor_json:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task_monitor = json.loads(task_monitor_json)
        return task_monitor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
