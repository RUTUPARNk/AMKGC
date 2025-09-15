# Versioning / Snapshots Service

This document explains how to use the Versioning Service for node versioning and snapshots in the Node-LLM system.

## Overview

The Versioning Service provides Git-like version control for nodes in the Node-LLM system. It allows you to:

1. Create snapshots of node states
2. Retrieve version history
3. Generate diffs between versions
4. Rollback to previous versions

## Components

1. **VersionService** - Main service class for versioning operations
2. **Database Schema** - PostgreSQL tables for storing versions
3. **API Endpoints** - FastAPI endpoints for versioning operations

## Setup

### 1. Database Setup

Apply the migration to create the versions table:

```sql
-- Run this SQL script to set up the database schema
-- database/migrations/003_add_versions_table.sql
```

### 2. Install Dependencies

```bash
# Install version service dependencies
pip install -r backend/requirements-version.txt
```

### 3. Environment Variables

Set the following environment variables:

```bash
# Database connection
PG_DSN=postgresql://user:password@localhost:5432/your_database

# Or alternatively
DATABASE_URL=postgresql://user:password@localhost:5432/your_database
```

## Usage

### 1. Creating Snapshots

```python
from backend.services.version_service import make_version_service_from_env

# Initialize service
version_service = make_version_service_from_env()

# Create a snapshot when merging
commit_id = version_service.create_snapshot(
    node_id="node-123",
    author="merge-agent",
    reason="merge",
    diff_summary="Updated authentication logic and error handling",
    diff_patch=[
        {"op": "replace", "path": "/context_window", "value": "new content"}
    ]
)
```

### 2. Retrieving Versions

```python
# Get all versions for a node
versions = version_service.get_versions("node-123")

for version in versions:
    print(f"Commit: {version.commit_id}")
    print(f"Author: {version.author}")
    print(f"Reason: {version.reason}")
    print(f"Created: {version.created_at}")
```

### 3. Generating Diffs

```python
# Generate a diff between two versions
diff_result = version_service.get_diff(
    commit_a="commit-abc123",
    commit_b="commit-def456"
)

print(f"Diff Summary: {diff_result.diff_summary}")
print(f"Changes: {diff_result.changes}")
```

### 4. Rolling Back

```python
# Rollback a node to a specific version
success = version_service.rollback(
    node_id="node-123",
    commit_id="commit-abc123"
)

if success:
    print("Rollback successful")
```

## API Endpoints

The Versioning Service is exposed through the following API endpoints:

- `POST /versions/snapshots` - Create a snapshot
- `GET /versions/nodes/{node_id}` - Get all versions for a node
- `GET /versions/{commit_id}` - Get a specific version
- `POST /versions/diff` - Generate a diff between two versions
- `POST /versions/rollback` - Rollback to a specific version
- `GET /versions/nodes/{node_id}/history` - Get simplified version history
- `GET /versions/health` - Health check

Example API usage:

```bash
# Create a snapshot
curl -X POST http://localhost:8000/versions/snapshots \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "node-123",
    "author": "merge-agent",
    "reason": "merge"
  }'

# Get version history
curl -X GET http://localhost:8000/versions/nodes/node-123/history

# Generate diff
curl -X POST http://localhost:8000/versions/diff \
  -H "Content-Type: application/json" \
  -d '{
    "commit_a": "commit-abc123",
    "commit_b": "commit-def456"
  }'
```

## Integration with Merge Agent

The Merge Agent can use the Versioning Service to create snapshots before applying merges:

```python
# In your Merge Agent implementation
from backend.services.version_service import make_version_service_from_env

class MergeAgent:
    def __init__(self):
        self.version_service = make_version_service_from_env()
    
    def apply_merge(self, parent_id: str, child_content: str, approver: str):
        """Apply a merge and create a snapshot."""
        # Create a snapshot before applying changes
        commit_id = self.version_service.create_snapshot(
            node_id=parent_id,
            author=approver,
            reason="merge",
            diff_summary="Applied changes from child node"
        )
        
        # Apply the merge (update node content)
        # ... merge logic ...
        
        return commit_id
```

## Integration with Frontend

The frontend can use the versioning API to display node history and diffs:

```javascript
// In your frontend service
async function getNodeHistory(nodeId) {
  const response = await fetch(`/versions/nodes/${nodeId}/history`);
  return await response.json();
}

async function getDiff(commitA, commitB) {
  const response = await fetch('/versions/diff', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ commit_a: commitA, commit_b: commitB })
  });
  return await response.json();
}
```

## Performance Considerations

1. **Indexing**: The schema includes indexes for efficient querying
2. **Snapshot Size**: Consider storing large snapshots in an object store (S3, GCS) rather than the database
3. **History Retention**: Implement a retention policy for old versions if needed
4. **Caching**: Cache frequently accessed versions

## Troubleshooting

1. **Database Connection Issues**: Verify PG_DSN or DATABASE_URL environment variables
2. **Missing Dependencies**: Install required packages from requirements-version.txt
3. **Permission Issues**: Ensure database user has proper permissions on the versions table

## Future Enhancements

1. **Branching**: Add support for branching and merging of node histories
2. **Tags**: Add support for tagging specific versions
3. **Search**: Add search functionality across version history
4. **Export**: Add export functionality for version history
