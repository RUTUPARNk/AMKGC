"""
Unified Worker

This worker handles multiple types of asynchronous tasks including:
1. Vector embeddings generation
2. Diff generation between node versions
3. Other background processing tasks
"""

import asyncio
import json
import logging
from typing import List, Tuple, Optional, Dict, Any
from redis import Redis
from datetime import datetime
import uuid

# Import services
from backend.services.vector_services import VectorService, make_vector_service_from_env
from backend.services.version_service import VersionService, make_version_service_from_env

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Redis connection for queue
redis_client = Redis.from_url("redis://localhost:6379/0")

# Services
vector_service: Optional[VectorService] = None
version_service: Optional[VersionService] = None

# Queue names
UNIFIED_QUEUE = "unified_worker_queue"
TASK_RESULTS_QUEUE = "task_results_queue"

async def process_fragment_embedding(message: dict):
    """
    Process a single fragment embedding task.
    """
    try:
        task_id = message.get("task_id")
        node_id = message.get("node_id")
        text = message.get("text")
        commit_id = message.get("commit_id")
        offset = message.get("offset", 0)
        
        if not node_id or not text:
            error_msg = f"Invalid message: missing node_id or text"
            logger.error(error_msg)
            _report_task_result(task_id, "error", {"error": error_msg})
            return
        
        # Initialize vector service if needed
        get_vector_service()
        
        # Add fragment to vector store
        fragment_id = vector_service.add_fragment(
            node_id=node_id,
            text=text,
            commit_id=commit_id,
            offset=offset
        )
        
        logger.info(f"Successfully added fragment {fragment_id} for node {node_id}")
        
        # Report success
        _report_task_result(task_id, "completed", {
            "fragment_id": fragment_id,
            "message": f"Successfully added fragment {fragment_id} for node {node_id}"
        })
        
    except Exception as e:
        error_msg = f"Error processing fragment embedding: {e}"
        logger.error(error_msg)
        _report_task_result(task_id, "error", {"error": error_msg})

async def process_bulk_fragments_embedding(message: dict):
    """
    Process bulk fragment embedding task.
    """
    try:
        task_id = message.get("task_id")
        node_id = message.get("node_id")
        items: List[Tuple[str, Optional[str], int]] = message.get("items", [])
        
        if not node_id or not items:
            error_msg = f"Invalid message: missing node_id or items"
            logger.error(error_msg)
            _report_task_result(task_id, "error", {"error": error_msg})
            return
        
        # Initialize vector service if needed
        get_vector_service()
        
        # Add fragments to vector store
        fragment_ids = vector_service.add_fragments_bulk(
            node_id=node_id,
            items=items
        )
        
        logger.info(f"Successfully added {len(fragment_ids)} fragments for node {node_id}")
        
        # Report success
        _report_task_result(task_id, "completed", {
            "fragment_ids": fragment_ids,
            "message": f"Successfully added {len(fragment_ids)} fragments for node {node_id}"
        })
        
    except Exception as e:
        error_msg = f"Error processing bulk fragment embedding: {e}"
        logger.error(error_msg)
        _report_task_result(task_id, "error", {"error": error_msg})

async def process_diff_generation(message: dict):
    """
    Process diff generation task between two node versions.
    """
    try:
        task_id = message.get("task_id")
        commit_a = message.get("commit_a")
        commit_b = message.get("commit_b")
        
        if not commit_a or not commit_b:
            error_msg = f"Invalid message: missing commit_a or commit_b"
            logger.error(error_msg)
            _report_task_result(task_id, "error", {"error": error_msg})
            return
        
        # Initialize version service if needed
        get_version_service()
        
        # Generate diff
        diff_result = version_service.get_diff(commit_a, commit_b)
        
        logger.info(f"Successfully generated diff between {commit_a} and {commit_b}")
        
        # Report success
        _report_task_result(task_id, "completed", {
            "diff": {
                "commit_a": diff_result.commit_a,
                "commit_b": diff_result.commit_b,
                "diff_summary": diff_result.diff_summary,
                "diff_patch": diff_result.diff_patch,
                "changes": diff_result.changes
            },
            "message": f"Successfully generated diff between {commit_a[:8]} and {commit_b[:8]}"
        })
        
    except Exception as e:
        error_msg = f"Error processing diff generation: {e}"
        logger.error(error_msg)
        _report_task_result(task_id, "error", {"error": error_msg})

async def process_version_snapshot(message: dict):
    """
    Process version snapshot creation task.
    """
    try:
        task_id = message.get("task_id")
        node_id = message.get("node_id")
        author = message.get("author")
        reason = message.get("reason")
        content_snapshot = message.get("content_snapshot")
        diff_summary = message.get("diff_summary")
        diff_patch = message.get("diff_patch")
        parent_commit_id = message.get("parent_commit_id")
        
        if not node_id or not author or not reason:
            error_msg = f"Invalid message: missing required fields (node_id, author, reason)"
            logger.error(error_msg)
            _report_task_result(task_id, "error", {"error": error_msg})
            return
        
        # Initialize version service if needed
        get_version_service()
        
        # Create snapshot
        commit_id = version_service.create_snapshot(
            node_id=node_id,
            author=author,
            reason=reason,
            content_snapshot=content_snapshot,
            diff_summary=diff_summary,
            diff_patch=diff_patch,
            parent_commit_id=parent_commit_id
        )
        
        logger.info(f"Successfully created snapshot {commit_id} for node {node_id}")
        
        # Report success
        _report_task_result(task_id, "completed", {
            "commit_id": commit_id,
            "message": f"Successfully created snapshot {commit_id[:8]} for node {node_id}"
        })
        
    except Exception as e:
        error_msg = f"Error processing version snapshot: {e}"
        logger.error(error_msg)
        _report_task_result(task_id, "error", {"error": error_msg})

def get_vector_service():
    """
    Get or create vector service instance.
    """
    global vector_service
    if vector_service is None:
        vector_service = make_vector_service_from_env()
    return vector_service

def get_version_service():
    """
    Get or create version service instance.
    """
    global version_service
    if version_service is None:
        version_service = make_version_service_from_env()
    return version_service

def _report_task_result(task_id: str, status: str, result: Dict[str, Any]):
    """
    Report task result back to the results queue.
    """
    try:
        result_data = {
            "task_id": task_id,
            "status": status,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        redis_client.lpush(TASK_RESULTS_QUEUE, json.dumps(result_data))
        logger.info(f"Reported result for task {task_id} with status {status}")
        
    except Exception as e:
        logger.error(f"Failed to report task result: {e}")

def main():
    """
    Main worker loop.
    """
    global vector_service, version_service
    
    logger.info("Unified worker started")
    
    try:
        while True:
            # Blocking pop from Redis queue
            _, message = redis_client.blpop(UNIFIED_QUEUE, timeout=5)
            
            if message:
                try:
                    # Parse message
                    task = json.loads(message)
                    task_id = task.get("task_id", str(uuid.uuid4()))
                    task_type = task.get("type")
                    
                    logger.info(f"Processing task {task_id} of type {task_type}")
                    
                    # Process based on task type
                    if task_type == "fragment_embedding":
                        asyncio.run(process_fragment_embedding(task))
                    elif task_type == "bulk_fragments_embedding":
                        asyncio.run(process_bulk_fragments_embedding(task))
                    elif task_type == "diff_generation":
                        asyncio.run(process_diff_generation(task))
                    elif task_type == "version_snapshot":
                        asyncio.run(process_version_snapshot(task))
                    else:
                        error_msg = f"Unknown task type: {task_type}"
                        logger.warning(error_msg)
                        _report_task_result(task_id, "error", {"error": error_msg})
                        
                except json.JSONDecodeError as e:
                    error_msg = f"Error decoding message: {e}"
                    logger.error(error_msg)
                    # We don't have a task_id here, so we can't report the result
                except Exception as e:
                    error_msg = f"Error processing message: {e}"
                    logger.error(error_msg)
                    # We don't have a task_id here, so we can't report the result
            
    except KeyboardInterrupt:
        logger.info("Worker interrupted")
    except Exception as e:
        logger.error(f"Worker error: {e}")
    finally:
        # Clean up
        if vector_service:
            vector_service.close()
        if version_service:
            version_service.close()
        
        logger.info("Unified worker stopped")

if __name__ == "__main__":
    main()
