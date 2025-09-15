"""
Vector Worker

This worker handles asynchronous processing of text fragments for vector embeddings.
"""

import asyncio
import json
import logging
from typing import List, Tuple, Optional
from redis import Redis

from backend.services.vector_services import VectorService, make_vector_service_from_env

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Redis connection for queue
redis_client = Redis.from_url("redis://localhost:6379/0")

# Vector service
vector_service: Optional[VectorService] = None

# Queue name
VECTOR_QUEUE = "vector_queue"

async def process_fragment_embedding(message: dict):
    """
    Process a single fragment embedding task.
    """
    try:
        node_id = message.get("node_id")
        text = message.get("text")
        commit_id = message.get("commit_id")
        offset = message.get("offset", 0)
        
        if not node_id or not text:
            logger.error(f"Invalid message: missing node_id or text")
            return
        
        # Add fragment to vector store
        fragment_id = vector_service.add_fragment(
            node_id=node_id,
            text=text,
            commit_id=commit_id,
            offset=offset
        )
        
        logger.info(f"Successfully added fragment {fragment_id} for node {node_id}")
        
        # Notify completion (optional)
        # This could publish to a completion channel or update a status in Redis
        
    except Exception as e:
        logger.error(f"Error processing fragment embedding: {e}")
        # Handle error (retry, dead letter queue, etc.)

async def process_bulk_fragments_embedding(message: dict):
    """
    Process bulk fragment embedding task.
    """
    try:
        node_id = message.get("node_id")
        items: List[Tuple[str, Optional[str], int]] = message.get("items", [])
        
        if not node_id or not items:
            return
        
        # Add fragments to vector store
        fragment_ids = vector_service.add_fragments_bulk(
            node_id=node_id,
            items=items
        )
        
        logger.info(f"Successfully added {len(fragment_ids)} fragments for node {node_id}")
        
    except Exception as e:
        logger.error(f"Error processing bulk fragment embedding: {e}")
        # Handle error (retry, dead letter queue, etc.)

def get_vector_service():
    """
    Get or create vector service instance.
    """
    global vector_service
    if vector_service is None:
        vector_service = make_vector_service_from_env()
    return vector_service

def main():
    """
    Main worker loop.
    """
    global vector_service
    
    # Initialize vector service
    vector_service = get_vector_service()
    
    logger.info("Vector worker started")
    
    try:
        while True:
            # Blocking pop from Redis queue
            _, message = redis_client.blpop(VECTOR_QUEUE, timeout=5)
            
            if message:
                try:
                    # Parse message
                    task = json.loads(message)
                    task_type = task.get("type")
                    
                    # Process based on task type
                    if task_type == "fragment_embedding":
                        asyncio.run(process_fragment_embedding(task))
                    elif task_type == "bulk_fragments_embedding":
                        asyncio.run(process_bulk_fragments_embedding(task))
                    else:
                        logger.warning(f"Unknown task type: {task_type}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding message: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
            
    except KeyboardInterrupt:
        logger.info("Worker interrupted")
    except Exception as e:
        logger.error(f"Worker error: {e}")
    finally:
        # Clean up
        if vector_service:
            vector_service.close()
        
        logger.info("Vector worker stopped")

if __name__ == "__main__":
    main()
