# Clarification Agent Service

This document explains how to use the Clarification Agent for detecting hallucinations and knowledge gaps in LLM responses.

## Overview

The Clarification Agent is a safety net that detects potential hallucinations or knowledge gaps in LLM responses. It provides functionality for:

1. Analyzing LLM responses for potential issues
2. Logging detected hallucinations
3. Creating clarification nodes
4. Retrieving hallucination logs

## Components

1. **ClarificationService** - Main service class for hallucination detection
2. **Database Schema** - PostgreSQL tables for storing hallucination records
3. **API Endpoints** - FastAPI endpoints for clarification operations

## Setup

### 1. Database Setup

Apply the migration to create the hallucinations table:

```sql
-- Run this SQL script to set up the database schema
-- database/migrations/004_add_hallucinations_table.sql
```

### 2. Install Dependencies

```bash
# The Clarification Service uses existing dependencies
# No additional installation needed beyond main requirements
```

### 3. Environment Variables

Set the following environment variables:

```bash
# Database connection
PG_DSN=postgresql://user:password@localhost:5432/your_database

# Or alternatively
DATABASE_URL=postgresql://user:password@localhost:5432/your_database

# LLM provider for secondary checking
CLARIFICATION_LLM_PROVIDER=ollama  # or openai

# Whether to auto-create clarification nodes
AUTO_CREATE_CLARIFICATION_NODES=false

# Minimum confidence threshold for logging hallucinations
CLARIFICATION_MIN_CONFIDENCE=0.7
```

## Usage

### 1. Analyzing LLM Responses

```python
from backend.services.clarification_service import make_clarification_service_from_env

# Initialize service
clarification_service = make_clarification_service_from_env()

# Analyze an LLM response
issues = await clarification_service.analyze_response(
    node_id="node-123",
    response_text="The Earth is flat and the sun revolves around it."
)

for issue in issues:
    print(f"Type: {issue.type.value}")
    print(f"Snippet: {issue.snippet}")
    print(f"Confidence: {issue.confidence}")
```

### 2. Retrieving Hallucination Records

```python
# Get hallucination records for a node
records = await clarification_service.get_hallucinations(
    node_id="node-123",
    unresolved_only=True
)

for record in records:
    print(f"ID: {record.id}")
    print(f"Type: {record.type.value}")
    print(f"Snippet: {record.snippet}")
    print(f"Created: {record.created_at}")
```

### 3. Creating Clarification Nodes

```python
# Create a clarification node for a specific issue
child_id = await clarification_service.create_clarification_node(
    parent_node_id="node-123",
    snippet="The Earth is flat and the sun revolves around it."
)

print(f"Created clarification node: {child_id}")
```

### 4. Resolving Hallucinations

```python
# Mark a hallucination as resolved
success = await clarification_service.resolve_hallucination(
    hallucination_id="hallucination-abc123",
    resolution_notes="Verified with external sources, corrected in parent node"
)

if success:
    print("Hallucination resolved successfully")
```

## API Endpoints

The Clarification Service is exposed through the following API endpoints:

- `POST /clarification/analyze` - Analyze an LLM response
- `GET /clarification/node/{node_id}` - Get hallucination records for a node
- `POST /clarification/node/{node_id}/child` - Create a clarification node
- `POST /clarification/hallucination/{hallucination_id}/resolve` - Resolve a hallucination
- `GET /clarification/node/{node_id}/summary` - Get hallucination summary for a node
- `GET /clarification/health` - Health check

Example API usage:

```bash
# Analyze a response
curl -X POST http://localhost:8000/clarification/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "node-123",
    "response_text": "The Earth is flat and the sun revolves around it."
  }'

# Get hallucination records
curl -X GET http://localhost:8000/clarification/node/node-123

# Create a clarification node
curl -X POST http://localhost:8000/clarification/node/node-123/child \
  -H "Content-Type: application/json" \
  -d '{
    "parent_node_id": "node-123",
    "snippet": "The Earth is flat and the sun revolves around it."
  }'
```

## Integration with Router Agent

The Router Agent can use the Clarification Service to analyze its responses:

```python
# In your Router Agent implementation
from backend.services.clarification_service import make_clarification_service_from_env

class RouterAgent:
    def __init__(self):
        self.clarification_service = make_clarification_service_from_env()
    
    async def execute_plan(self, node_id: str, query: str):
        """Execute a plan and analyze the response for hallucinations."""
        # Execute the plan (existing logic)
        response = await self._execute_plan_logic(node_id, query)
        
        # Analyze the response for hallucinations
        issues = await self.clarification_service.analyze_response(
            node_id=node_id,
            response_text=response
        )
        
        # Optionally auto-create clarification nodes for high-confidence issues
        if self.clarification_service.cfg.auto_create_children:
            for issue in issues:
                if issue.confidence > 0.9:  # High confidence threshold
                    await self.clarification_service.create_clarification_node(
                        parent_node_id=node_id,
                        snippet=issue.snippet
                    )
        
        return response
```

## Integration with Frontend

The frontend can use the clarification API to display hallucination warnings and create clarification nodes:

```javascript
// In your frontend service
async function analyzeResponse(nodeId, responseText) {
  const response = await fetch('/clarification/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ node_id: nodeId, response_text: responseText })
  });
  return await response.json();
}

async function getHallucinations(nodeId) {
  const response = await fetch(`/clarification/node/${nodeId}`);
  return await response.json();
}

async function createClarificationNode(parentNodeId, snippet) {
  const response = await fetch(`/clarification/node/${parentNodeId}/child`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ parent_node_id: parentNodeId, snippet })
  });
  return await response.json();
}
```

## Heuristic Detection Patterns

The Clarification Service uses several heuristic patterns to detect potential hallucinations:

1. **Speculation Patterns**:
   - "I think", "I believe", "probably", "likely", "possibly", "maybe", "perhaps"
   - "as far as I know", "to the best of my knowledge"
   - "I'm not sure", "I'm uncertain"

2. **Missing Fact Patterns**:
   - "I don't know", "I'm not familiar with"
   - "missing information", "not enough information"

3. **Wrong Assumption Patterns**:
   - "assuming that", "presuming that", "based on the assumption"
   - "typically", "usually", "commonly" followed by "but", "however"

## LLM-Based Detection

For deeper analysis, the Clarification Service can use a secondary LLM call with the following prompt:

```
You are a fact-checking assistant. Given an LLM output, identify possible issues:
- Missing facts that require clarification
- Wrong assumptions or contradictions
- Speculative or uncertain statements

Return a JSON list: [{ "type": "MissingFact|WrongAssumption|Speculation", "snippet": "...", "confidence": 0.0-1.0, "explanation": "..." }]

If no issues found, return an empty list [].
```

## Performance Considerations

1. **Heuristic First**: Heuristic scanning is fast and should catch most obvious issues
2. **LLM Check**: LLM-based checking is more thorough but slower and costs tokens
3. **Confidence Threshold**: Use confidence thresholds to avoid false positives
4. **Caching**: Consider caching analysis results for identical responses

## Troubleshooting

1. **Database Connection Issues**: Verify PG_DSN or DATABASE_URL environment variables
2. **LLM Integration Issues**: Verify CLARIFICATION_LLM_PROVIDER and API keys
3. **Missing Dependencies**: Ensure psycopg and other dependencies are installed
4. **Permission Issues**: Ensure database user has proper permissions on the hallucinations table

## Future Enhancements

1. **Advanced NLP**: Integrate with NLP libraries for more sophisticated analysis
2. **Custom Rules**: Allow defining custom hallucination detection rules
3. **Batch Processing**: Add support for batch analysis of multiple responses
4. **Integration with Fact-Checking APIs**: Connect to external fact-checking services
