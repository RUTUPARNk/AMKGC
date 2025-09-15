# Node LLM System API Reference

## Overview

The Node LLM System API provides a comprehensive REST API for managing nodes, detecting and resolving conflicts, and integrating with Large Language Models (Ollama and OpenAI).

**Base URL**: `http://localhost:8000`  
**API Version**: `v1`  
**Authentication**: JWT Bearer Token

## Authentication

All API endpoints require authentication using JWT Bearer tokens, except for registration and login.

### Headers
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

## Endpoints

### Authentication

#### Register User
```http
POST /api/v1/auth/register
```

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user_id": "uuid"
}
```

#### Login User
```http
POST /api/v1/auth/login
```

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "user": {
    "user_id": "uuid",
    "username": "string",
    "email": "string"
  }
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

#### Logout User
```http
POST /api/v1/auth/logout
```

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

### Node Management

#### Create Node
```http
POST /api/v1/nodes
```

**Request Body:**
```json
{
  "name": "string",
  "node_type": "schema|policy|resolution",
  "context_window": "string",
  "parent_node_id": "uuid (optional)"
}
```

**Response:**
```json
{
  "message": "Node created successfully",
  "node": {
    "id": "uuid",
    "name": "string",
    "node_type": "string",
    "context_window": "string",
    "parent_node_id": "uuid",
    "status": "pending|resolved|conflicting",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

#### Get All Nodes
```http
GET /api/v1/nodes
```

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "string",
    "node_type": "string",
    "context_window": "string",
    "parent_node_id": "uuid",
    "child_nodes": ["uuid"],
    "status": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
]
```

#### Get Node by ID
```http
GET /api/v1/nodes/{node_id}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "node_type": "string",
  "context_window": "string",
  "parent_node_id": "uuid",
  "child_nodes": ["uuid"],
  "status": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### Update Node
```http
PUT /api/v1/nodes/{node_id}
```

**Request Body:**
```json
{
  "name": "string (optional)",
  "context_window": "string (optional)"
}
```

**Response:**
```json
{
  "message": "Node updated successfully",
  "node": {
    "id": "uuid",
    "name": "string",
    "context_window": "string",
    "updated_at": "datetime"
  }
}
```

#### Delete Node
```http
DELETE /api/v1/nodes/{node_id}
```

**Response:**
```json
{
  "message": "Node deleted successfully"
}
```

#### Get Node Graph
```http
GET /api/v1/nodes/graph
```

**Response:**
```json
{
  "nodes": [
    {
      "id": "uuid",
      "name": "string",
      "node_type": "string",
      "status": "string",
      "position": {"x": 0, "y": 0}
    }
  ],
  "edges": [
    {
      "source": "uuid",
      "target": "uuid",
      "type": "parent-child|dependency"
    }
  ]
}
```

#### Search Nodes
```http
GET /api/v1/nodes/search/{query}
```

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "string",
    "node_type": "string",
    "context_window": "string",
    "status": "string"
  }
]
```

### LLM Integration

#### Generate Content
```http
POST /api/v1/llm/generate
```

**Request Body:**
```json
{
  "prompt": "string",
  "model": "ollama|openai"
}
```

**Response:**
```json
{
  "content": "string",
  "model": "string",
  "tokens_used": "number",
  "provider": "ollama|openai",
  "timestamp": "datetime"
}
```

#### Generate Schema
```http
POST /api/v1/llm/schema
```

**Request Body:**
```json
{
  "table_name": "string",
  "description": "string (optional)"
}
```

**Response:**
```json
{
  "content": "string",
  "model": "string",
  "tokens_used": "number",
  "provider": "string",
  "timestamp": "datetime"
}
```

#### Generate Policy
```http
POST /api/v1/llm/policy
```

**Request Body:**
```json
{
  "policy_type": "string",
  "context": "string (optional)"
}
```

**Response:**
```json
{
  "content": "string",
  "model": "string",
  "tokens_used": "number",
  "provider": "string",
  "timestamp": "datetime"
}
```

#### Generate Node Context
```http
POST /api/v1/nodes/{node_id}/generate
```

**Request Body:**
```json
{
  "prompt": "string"
}
```

**Response:**
```json
{
  "content": "string",
  "model": "string",
  "tokens_used": "number",
  "provider": "string",
  "timestamp": "datetime"
}
```

### Conflict Management

#### Detect Conflicts
```http
POST /api/v1/nodes/conflicts/detect
```

**Request Body:**
```json
{
  "node1_id": "uuid",
  "node2_id": "uuid",
  "user_feedback": "string (optional)"
}
```

**Response:**
```json
{
  "id": "string",
  "node1_id": "uuid",
  "node2_id": "uuid",
  "node1_name": "string",
  "node2_name": "string",
  "description": "string",
  "conflicts": ["string"],
  "severity": "critical|high|medium|low",
  "priority": "number",
  "suggestions": ["string"],
  "user_feedback": "string",
  "created_at": "datetime",
  "status": "pending"
}
```

#### Resolve Conflict
```http
POST /api/v1/conflicts/{conflict_id}/resolve
```

**Request Body:**
```json
{
  "resolution_context": "string",
  "user_feedback": "string (optional)"
}
```

**Response:**
```json
{
  "conflict_id": "string",
  "resolution_node_id": "uuid",
  "resolution_content": "string",
  "user_feedback": "string",
  "resolved_at": "datetime",
  "llm_provider": "string"
}
```

#### Get All Conflicts
```http
GET /api/v1/conflicts
```

**Response:**
```json
[
  {
    "id": "string",
    "node1_id": "uuid",
    "node2_id": "uuid",
    "node1_name": "string",
    "node2_name": "string",
    "description": "string",
    "conflicts": ["string"],
    "severity": "string",
    "priority": "number",
    "suggestions": ["string"],
    "user_feedback": "string",
    "created_at": "datetime",
    "status": "string"
  }
]
```

### Token Management

#### Split Large Context
```http
POST /api/v1/nodes/{node_id}/split
```

**Response:**
```json
{
  "chunks": ["string"],
  "total_chunks": "number"
}
```

### Monitoring

#### Get Cache Statistics
```http
GET /api/v1/monitoring/cache-stats
```

**Response:**
```json
{
  "redis_info": {
    "used_memory": "string",
    "connected_clients": "number",
    "total_commands_processed": "number",
    "keyspace_hits": "number",
    "keyspace_misses": "number"
  },
  "cache_stats": {
    "total_cache_keys": "number",
    "total_sessions": "number",
    "total_graphs": "number",
    "total_searches": "number"
  },
  "token_usage": {
    "total_tokens": "number",
    "total_requests": "number",
    "by_model": {},
    "by_operation": {}
  }
}
```

#### Get Rate Limit Information
```http
GET /api/v1/monitoring/rate-limits/{action}/{identifier}
```

**Response:**
```json
{
  "allowed": "boolean",
  "remaining": "number",
  "reset_time": "number",
  "retry_after": "number"
}
```

### WebSocket

#### WebSocket Connection
```http
WS /api/v1/ws
```

**Message Format:**
```json
{
  "type": "string",
  "data": "object"
}
```

**Event Types:**
- `node_created` - New node created
- `node_updated` - Node updated
- `node_deleted` - Node deleted
- `node_context_generated` - Node context generated
- `conflict_detected` - New conflict detected
- `conflict_resolved` - Conflict resolved
- `context_split` - Context split into chunks

## Error Responses

### Standard Error Format
```json
{
  "detail": "Error message",
  "status_code": "number"
}
```

### Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error

### Rate Limiting

The API implements rate limiting to prevent abuse:

- **Login**: 5 attempts per minute
- **Register**: 3 attempts per minute
- **API Calls**: 100 requests per minute per user

When rate limited, the response includes:
```json
{
  "detail": "Rate limit exceeded. Retry after X seconds",
  "status_code": 429
}
```

## Pagination

For endpoints that return lists, pagination is supported:

```http
GET /api/v1/nodes?page=1&limit=20
```

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5
  }
}
```

## Filtering and Sorting

Many endpoints support filtering and sorting:

```http
GET /api/v1/nodes?node_type=schema&status=resolved&sort=created_at&order=desc
```

**Supported Filters:**
- `node_type` - Filter by node type
- `status` - Filter by status
- `created_after` - Filter by creation date
- `created_before` - Filter by creation date

**Supported Sort Fields:**
- `name` - Sort by name
- `created_at` - Sort by creation date
- `updated_at` - Sort by update date
- `status` - Sort by status

## Environment Variables

The API uses the following environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/node_llm_system

# Redis
REDIS_URL=redis://localhost:6379

# LLM Configuration
OLLAMA_MODEL=llama3
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Security
SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Rate Limiting
RATE_LIMIT_LOGIN=5
RATE_LIMIT_REGISTER=3
RATE_LIMIT_API=100

# Token Management
MAX_TOKENS=4096
TOKEN_SPLIT_THRESHOLD=0.8
```

## SDK Examples

### Python
```python
import requests

# Login
response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'username': 'user',
    'password': 'password'
})
token = response.json()['access_token']

# Create node
headers = {'Authorization': f'Bearer {token}'}
response = requests.post('http://localhost:8000/api/v1/nodes', json={
    'name': 'Test Node',
    'node_type': 'schema',
    'context_window': 'Test context'
}, headers=headers)
```

### JavaScript
```javascript
// Login
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'user',
    password: 'password'
  })
});
const { access_token } = await response.json();

// Create node
const nodeResponse = await fetch('http://localhost:8000/api/v1/nodes', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'Test Node',
    node_type: 'schema',
    context_window: 'Test context'
  })
});
```

## WebSocket Examples

### JavaScript
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws');

ws.onopen = () => {
  console.log('Connected to WebSocket');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
  
  switch (message.type) {
    case 'node_created':
      console.log('New node created:', message.data);
      break;
    case 'conflict_detected':
      console.log('Conflict detected:', message.data);
      break;
  }
};

ws.onclose = () => {
  console.log('WebSocket connection closed');
};
```

## Testing

The API includes comprehensive test coverage. Run tests with:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_llm_service.py

# Run with coverage
pytest --cov=backend
```

## Support

For API support and questions:

- **Documentation**: [GitHub Wiki](https://github.com/your-repo/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions) 