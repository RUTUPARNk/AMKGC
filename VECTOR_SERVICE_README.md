# Vector Service Integration Guide

This document explains how to integrate and use the Vector Service for semantic search in the Node-LLM system.

## Overview

The Vector Service provides semantic search capabilities by storing text fragments with their embeddings in a pgvector database. It supports both OpenAI and local embedding models.

## Components

1. **VectorService** - Main service class for adding fragments and searching
2. **Database Schema** - PostgreSQL tables with pgvector support
3. **Worker** - Asynchronous processing of embedding tasks
4. **API Endpoints** - FastAPI endpoints for vector operations

## Setup

### 1. Database Setup

Apply the migration to create the fragments table:

```sql
-- Run this SQL script to set up the database schema
-- database/migrations/002_add_fragments_table.sql
```

### 2. Install Dependencies

```bash
# Install vector service dependencies
pip install -r backend/requirements-vector.txt

# Or for the worker
pip install -r worker/src/requirements.txt
```

### 3. Environment Variables

Set the following environment variables:

```bash
# Database connection
PG_DSN=postgresql://user:password@localhost:5432/your_database

# Or alternatively
DATABASE_URL=postgresql://user:password@localhost:5432/your_database

# Embedding configuration
EMBEDDING_DIM=1536  # Default for OpenAI text-embedding-3-small
VECTOR_DISTANCE=cosine  # or l2, ip
VECTOR_TOP_K=5
EMBEDDER=openai  # or local

# For OpenAI embeddings
OPENAI_API_KEY=your_openai_api_key
OPENAI_EMBED_MODEL=text-embedding-3-small
```

## Usage

### 1. Adding Fragments

```python
from backend.services.vector_services import make_vector_service_from_env

# Initialize service
vector_service = make_vector_service_from_env()

# Add a single fragment
fragment_id = vector_service.add_fragment(
    node_id="node-123",
    text="This is a text fragment to be embedded",
    commit_id="commit-456",
    offset=0
)

# Add multiple fragments
fragment_ids = vector_service.add_fragments_bulk(
    node_id="node-123",
    items=[
        ("First fragment text", "commit-456", 0),
        ("Second fragment text", "commit-456", 1),
        ("Third fragment text", "commit-456", 2)
    ]
)
```

### 2. Searching Fragments

```python
# Search for relevant fragments
fragments = vector_service.search(
    node_id="node-123",
    query="Find information about authentication",
    top_k=5,
    since_commit="commit-456"  # Optional
)

for fragment in fragments:
    print(f"Score: {fragment['score']:.3f}")
    print(f"Text: {fragment['text']}")
```

### 3. Using the API

The Vector Service is exposed through the following API endpoints:

- `POST /vector/fragments` - Add a single fragment
- `POST /vector/fragments/bulk` - Add multiple fragments
- `POST /vector/search` - Search for fragments
- `DELETE /vector/fragments/node/{node_id}` - Delete all fragments for a node
- `GET /vector/health` - Health check

Example API usage:

```bash
# Add a fragment
curl -X POST http://localhost:8000/vector/fragments \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "node-123",
    "text": "This is a text fragment",
    "commit_id": "commit-456"
  }'

# Search fragments
curl -X POST http://localhost:8000/vector/search \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "node-123",
    "query": "Find information about authentication",
    "top_k": 5
  }'
```

### 4. Asynchronous Processing

For high-throughput scenarios, use the worker to process embeddings asynchronously:

```python
import json
import redis

# Connect to Redis
redis_client = redis.Redis.from_url("redis://localhost:6379/0")

# Queue a fragment embedding task
message = {
    "type": "fragment_embedding",
    "node_id": "node-123",
    "text": "This is a text fragment to be embedded",
    "commit_id": "commit-456",
    "offset": 0
}

redis_client.lpush("vector_queue", json.dumps(message))
```

Start the worker:

```bash
cd worker/src
python vector_worker.py
```

## Integration with Router Agent

The Router Agent can use the Vector Service to retrieve semantically relevant fragments:

```python
# In your Router Agent implementation
from backend.services.vector_services import make_vector_service_from_env

class RouterAgent:
    def __init__(self):
        self.vector_service = make_vector_service_from_env()
    
    def get_relevant_context(self, node_id: str, query: str, top_k: int = 5):
        """Retrieve semantically relevant fragments for a node."""
        fragments = self.vector_service.search(
            node_id=node_id,
            query=query,
            top_k=top_k
        )
        
        # Format fragments for LLM context
        context = "\n\n".join([
            f"[Fragment {i+1} (Score: {fragment['score']:.3f})] {fragment['text']}"
            for i, fragment in enumerate(fragments)
        ])
        
        return context
```

## Performance Considerations

1. **Indexing**: The schema includes HNSW indexes for efficient similarity search
2. **Batch Processing**: Use `add_fragments_bulk` for better performance when adding multiple fragments
3. **Asynchronous Processing**: Use the worker for high-throughput embedding generation
4. **Caching**: Consider caching frequently accessed fragments

## Troubleshooting

1. **Database Connection Issues**: Verify PG_DSN or DATABASE_URL environment variables
2. **Embedding Dimension Mismatch**: Ensure EMBEDDING_DIM matches your embedding model
3. **Missing Dependencies**: Install required packages from requirements-vector.txt
4. **Permission Issues**: Ensure database user has proper permissions on the fragments table

## Future Enhancements

1. **Multi-tenancy**: Add tenant_id to support multiple users/organizations
2. **Metadata Filtering**: Add support for filtering by metadata fields
3. **Hybrid Search**: Combine vector similarity with keyword search
4. **Re-ranking**: Add re-ranking models for improved relevance
