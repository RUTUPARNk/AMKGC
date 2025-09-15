# Continuation Nodes Service

This document explains how to use the Continuation Nodes feature for handling token overflow in large node contexts.

## Overview

The Continuation Nodes feature ensures nodes don't grow unbounded when chat history or embeddings exceed token limits. It automatically creates Continuation Nodes to store overflow and allows the Router Agent to stitch together context from a parent node and its continuation chain.

## Components

1. **Database Schema** - PostgreSQL schema changes for continuation nodes
2. **ContinuationService** - Main service class for managing continuation nodes
3. **API Endpoints** - FastAPI endpoints for continuation operations

## Setup

### 1. Database Setup

Apply the migration to add continuation nodes support:

```sql
-- Run this SQL script to set up the database schema
-- database/migrations/005_add_continuation_nodes.sql
```

### 2. Install Dependencies

```bash
# The Continuation Service uses existing dependencies
# No additional installation needed beyond main requirements
```

### 3. Environment Variables

Set the following environment variables:

```bash
# Database connection
PG_DSN=postgresql://user:password@localhost:5432/your_database

# Or alternatively
DATABASE_URL=postgresql://user:password@localhost:5432/your_database

# Token limit before splitting
CONTINUATION_TOKEN_LIMIT=2000000

# Minimum tokens to keep in parent node
CONTINUATION_MIN_TOKENS=100000
```

## Usage

### 1. Checking and Splitting Nodes

```python
from backend.services.continuation_service import make_continuation_service_from_env

# Initialize service
continuation_service = make_continuation_service_from_env()

# Check if a node needs to be split and create continuation if needed
# Returns the node ID where the message should be added
target_node_id = await continuation_service.check_and_split(
    node_id="node-123",
    new_message="This is a new message that might cause token overflow",
    token_limit=2_000_000  # Optional, defaults to config value
)

if target_node_id != "node-123":
    print(f"Created continuation node: {target_node_id}")
else:
    print("Message can be added to original node")
```

### 2. Retrieving Continuation Chains

```python
# Get the full continuation chain for a node
chain = await continuation_service.get_chain("node-123")

print(f"Root node: {chain.root_node_id}")
print(f"Chain length: {len(chain.nodes)}")

for i, node in enumerate(chain.nodes):
    print(f"Node {i}: {node['id']} ({node['node_type']}) - Status: {node['status']}")
```

### 3. Getting Active Node

```python
# Get the active (latest) node in a continuation chain
active_node = await continuation_service.get_active_node("node-123")

print(f"Active node: {active_node['id']}")
print(f"Status: {active_node['status']}")
```

## API Endpoints

The Continuation Service is exposed through the following API endpoints:

- `POST /continuation/check-and-split` - Check and split node if needed
- `GET /continuation/chain/{node_id}` - Get full continuation chain
- `GET /continuation/active/{node_id}` - Get active node in chain
- `GET /continuation/chain/{node_id}/summary` - Get chain summary
- `GET /continuation/health` - Health check

Example API usage:

```bash
# Check and split a node
curl -X POST http://localhost:8000/continuation/check-and-split \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "node-123",
    "new_message": "This is a new message that might cause token overflow"
  }'

# Get continuation chain
curl -X GET http://localhost:8000/continuation/chain/node-123

# Get active node
curl -X GET http://localhost:8000/continuation/active/node-123
```

## Integration with Router Agent

The Router Agent can use the Continuation Service to retrieve fragments across continuation chains:

```python
# In your Router Agent implementation
from backend.services.continuation_service import make_continuation_service_from_env
from backend.services.vector_services import make_vector_service_from_env

class RouterAgent:
    def __init__(self):
        self.continuation_service = make_continuation_service_from_env()
        self.vector_service = make_vector_service_from_env()
    
    async def build_context_package(self, active_node_id: str, query: str, top_k: int = 5):
        """Build a context package from a node and its continuation chain."""
        # Get the continuation chain
        chain = await self.continuation_service.get_chain(active_node_id)
        
        # Collect fragments from all nodes in the chain
        all_fragments = []
        
        for node in chain.nodes:
            # Run semantic search across each node in the chain
            frags = self.vector_service.search(
                node_id=node["id"],
                query=query,
                top_k=3  # Get top 3 from each node
            )
            all_fragments.extend(frags)
        
        # Sort fragments by relevance score and take top_k
        all_fragments.sort(key=lambda x: x["score"], reverse=True)
        selected_fragments = all_fragments[:top_k]
        
        # Build context package
        context = self._build_context_from_fragments(selected_fragments, query)
        
        return context
    
    def _build_context_from_fragments(self, fragments: List[Dict], query: str) -> str:
        """Build context string from fragments."""
        # Implementation depends on your specific needs
        # This is a simplified example
        context_parts = []
        
        for fragment in fragments:
            context_parts.append(f"[Relevance: {fragment['score']:.2f}] {fragment['text']}")
        
        return "\n\n".join(context_parts)
```

## Integration with Node Chat History

When adding new messages to nodes, use the Continuation Service to check if splitting is needed:

```python
# In your chat history management code
async def add_message_to_node(node_id: str, message: str):
    """Add a message to a node, creating continuation if needed."""
    continuation_service = make_continuation_service_from_env()
    
    # Check if we need to split
    target_node_id = await continuation_service.check_and_split(
        node_id=node_id,
        new_message=message
    )
    
    # Add the message to the appropriate node
    # (Implementation depends on your specific storage mechanism)
    await _store_message(target_node_id, message)
    
    return target_node_id
```

## Database Schema Details

The migration adds the following to the nodes table:

1. `continuation_of` - UUID reference to parent node
2. `token_count` - Integer count of tokens in node (optional)
3. Indexes for performance on both new columns

Helper functions added:
1. `get_continuation_root(node_id)` - Find root of continuation chain
2. `get_continuation_chain(root_node_id)` - Get all nodes in chain
3. `node_continuation_chains` - View for querying chains

## Performance Considerations

1. **Token Counting**: The service approximates token counts (1 token ≈ 4 characters). For production, integrate with a proper tokenizer like tiktoken.
2. **Chain Traversal**: Chain traversal is O(n) where n is chain length. Keep chains reasonably short.
3. **Database Indexes**: Proper indexing is crucial for performance.
4. **Caching**: Consider caching chain information for frequently accessed nodes.

## Troubleshooting

1. **Database Connection Issues**: Verify PG_DSN or DATABASE_URL environment variables
2. **Missing Dependencies**: Ensure psycopg and other dependencies are installed
3. **Permission Issues**: Ensure database user has proper permissions on the nodes table
4. **Chain Traversal Errors**: Check for circular references in continuation_of links

## Future Enhancements

1. **Intelligent Splitting**: Split nodes at logical boundaries rather than token limits
2. **Compression**: Compress older parts of chains
3. **Archiving**: Automatically archive older chains
4. **Migration Tools**: Tools to migrate existing large nodes to continuation chains
