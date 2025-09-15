# Unified Worker Service

This document explains how to use the Unified Worker for asynchronous task processing in the Node-LLM system.

## Overview

The Unified Worker handles multiple types of asynchronous tasks including:

1. Vector embeddings generation
2. Diff generation between node versions
3. Version snapshot creation
4. Other background processing tasks

## Components

1. **Unified Worker** - Main worker process that handles multiple task types
2. **Redis Queues** - Task queues for distributing work
3. **Task Result Reporting** - Mechanism for reporting task results

## Setup

### 1. Install Dependencies

```bash
# Install worker dependencies (already included in worker/src/requirements.txt)
pip install -r worker/src/requirements.txt
```

### 2. Environment Variables

Set the following environment variables:

```bash
# Database connection (for vector and version services)
PG_DSN=postgresql://user:password@localhost:5432/your_database

# Or alternatively
DATABASE_URL=postgresql://user:password@localhost:5432/your_database

# For OpenAI embeddings (optional)
OPENAI_API_KEY=your_openai_api_key

# Redis connection
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Usage

### 1. Starting the Worker

```bash
cd worker/src
python unified_worker.py
```

### 2. Queueing Tasks

Tasks are queued using Redis. Here's how to queue different types of tasks:

#### Vector Embedding Task

```python
import json
import redis

# Connect to Redis
redis_client = redis.Redis.from_url("redis://localhost:6379/0")

# Queue a single fragment embedding task
task = {
    "task_id": "task-123",  # Optional, will be generated if not provided
    "type": "fragment_embedding",
    "node_id": "node-abc123",
    "text": "Text to be embedded",
    "commit_id": "commit-def456",
    "offset": 0
}

redis_client.lpush("unified_worker_queue", json.dumps(task))
```

#### Bulk Vector Embedding Task

```python
# Queue a bulk fragment embedding task
task = {
    "task_id": "task-456",
    "type": "bulk_fragments_embedding",
    "node_id": "node-abc123",
    "items": [
        ("First fragment text", "commit-def456", 0),
        ("Second fragment text", "commit-def456", 1),
        ("Third fragment text", "commit-def456", 2)
    ]
}

redis_client.lpush("unified_worker_queue", json.dumps(task))
```

#### Diff Generation Task

```python
# Queue a diff generation task
task = {
    "task_id": "task-789",
    "type": "diff_generation",
    "commit_a": "commit-abc123",
    "commit_b": "commit-def456"
}

redis_client.lpush("unified_worker_queue", json.dumps(task))
```

#### Version Snapshot Task

```python
# Queue a version snapshot task
task = {
    "task_id": "task-101",
    "type": "version_snapshot",
    "node_id": "node-abc123",
    "author": "merge-agent",
    "reason": "merge",
    "content_snapshot": {
        "id": "node-abc123",
        "name": "Example Node",
        "context_window": "Node content",
        "status": "active"
    },
    "diff_summary": "Updated content with new information",
    "diff_patch": [
        {"op": "replace", "path": "/context_window", "value": "New content"}
    ]
}

redis_client.lpush("unified_worker_queue", json.dumps(task))
```

### 3. Processing Task Results

Task results are reported to the `task_results_queue`. Here's how to process them:

```python
import json
import redis

# Connect to Redis
redis_client = redis.Redis.from_url("redis://localhost:6379/0")

# Process task results
while True:
    # Blocking pop from results queue
    _, result_json = redis_client.brpop("task_results_queue", timeout=5)
    
    if result_json:
        result = json.loads(result_json)
        task_id = result["task_id"]
        status = result["status"]
        task_result = result["result"]
        
        if status == "completed":
            print(f"Task {task_id} completed successfully: {task_result}")
        elif status == "error":
            print(f"Task {task_id} failed: {task_result['error']}")
```

## Integration with Services

### Integration with Vector Service

The Vector Service can offload embedding generation to the worker:

```python
# In your VectorService implementation
import json
import redis
import uuid

class VectorService:
    def __init__(self):
        self.redis_client = redis.Redis.from_url("redis://localhost:6379/0")
    
    def add_fragment_async(self, node_id: str, text: str, commit_id: str = None, offset: int = 0):
        """Add a fragment asynchronously using the worker."""
        task = {
            "task_id": str(uuid.uuid4()),
            "type": "fragment_embedding",
            "node_id": node_id,
            "text": text,
            "commit_id": commit_id,
            "offset": offset
        }
        
        self.redis_client.lpush("unified_worker_queue", json.dumps(task))
        return task["task_id"]
```

### Integration with Version Service

The Version Service can offload diff generation and snapshot creation to the worker:

```python
# In your VersionService implementation
import json
import redis
import uuid

class VersionService:
    def __init__(self):
        self.redis_client = redis.Redis.from_url("redis://localhost:6379/0")
    
    def get_diff_async(self, commit_a: str, commit_b: str):
        """Generate a diff asynchronously using the worker."""
        task = {
            "task_id": str(uuid.uuid4()),
            "type": "diff_generation",
            "commit_a": commit_a,
            "commit_b": commit_b
        }
        
        self.redis_client.lpush("unified_worker_queue", json.dumps(task))
        return task["task_id"]
    
    def create_snapshot_async(self, node_id: str, author: str, reason: str, 
                             content_snapshot: dict = None, diff_summary: str = None,
                             diff_patch: list = None, parent_commit_id: str = None):
        """Create a snapshot asynchronously using the worker."""
        task = {
            "task_id": str(uuid.uuid4()),
            "type": "version_snapshot",
            "node_id": node_id,
            "author": author,
            "reason": reason,
            "content_snapshot": content_snapshot,
            "diff_summary": diff_summary,
            "diff_patch": diff_patch,
            "parent_commit_id": parent_commit_id
        }
        
        self.redis_client.lpush("unified_worker_queue", json.dumps(task))
        return task["task_id"]
```

### Integration with Merge Agent

The Merge Agent can use the worker for offloading heavy operations:

```python
# In your Merge Agent implementation
class MergeAgent:
    def __init__(self):
        self.redis_client = redis.Redis.from_url("redis://localhost:6379/0")
    
    def apply_merge_with_snapshot(self, parent_id: str, child_content: str, approver: str):
        """Apply a merge and create a snapshot asynchronously."""
        # Create a snapshot asynchronously
        task = {
            "task_id": str(uuid.uuid4()),
            "type": "version_snapshot",
            "node_id": parent_id,
            "author": approver,
            "reason": "merge",
            "content_snapshot": child_content,
            "diff_summary": "Applied changes from child node"
        }
        
        self.redis_client.lpush("unified_worker_queue", json.dumps(task))
        return task["task_id"]
```

## Performance Considerations

1. **Task Prioritization**: Consider implementing priority queues for different task types
2. **Error Handling**: Implement retry mechanisms for failed tasks
3. **Monitoring**: Monitor worker performance and queue depths
4. **Scaling**: Run multiple worker instances for better throughput

## Troubleshooting

1. **Worker Not Starting**: Verify Redis connection and dependencies
2. **Tasks Not Processing**: Check if the worker is running and Redis queues are configured correctly
3. **Database Connection Issues**: Verify PG_DSN or DATABASE_URL environment variables
4. **Missing Dependencies**: Install required packages from requirements.txt

## Future Enhancements

1. **Task Prioritization**: Add priority levels to tasks
2. **Retry Mechanism**: Implement automatic retry for failed tasks
3. **Dead Letter Queue**: Add a queue for repeatedly failing tasks
4. **Monitoring Dashboard**: Create a dashboard for worker and queue monitoring
