# Running Ollama Integration Tests

This document provides instructions for running the Ollama integration tests to confirm that the Node-LLM System is properly configured to work with Ollama.

## Prerequisites

1. **Ollama Service**: Ensure Ollama is installed and running on your system
   - Download from: https://ollama.ai
   - Start Ollama service (usually starts automatically after installation)

2. **Required Ollama Model**: Ensure the configured model is available
   - Default model: `qwen3:8b` (as configured in .env)
   - Pull model if needed: `ollama pull qwen3:8b`

3. **Backend Services**: Ensure the following services are running
   - Redis server (default: localhost:6379)
   - PostgreSQL with pgvector extension
   - Neo4j database (optional for router tests)

## Running Tests

### 1. Backend Tests

Run the Ollama integration tests using pytest:

```bash
# Navigate to the project root
cd node-llm-system

# Run Ollama-specific tests
pytest -k ollama -v

# Or run the specific test file
python tests/test_ollama_integration.py

# Run all tests (including Ollama integration)
pytest
```

### 2. Frontend Tests

Run the frontend tests using Jest:

```bash
# Navigate to the frontend directory
cd frontend-minimal

# Run frontend tests
npm test

# Run specific Ollama integration tests
npm test -- ollamaIntegration.test.tsx
```

## Test Coverage

The tests cover the following functionality:

### Backend Tests
- **Ollama Health Check**: Verifies Ollama service is accessible
- **Ollama Embedding**: Tests embedding generation with Ollama
- **Semantic Search**: Tests `/vector/search/semantic` endpoint with Ollama provider
- **Router Execution**: Tests `/router/plan_execution` endpoint with Ollama provider

### Frontend Tests
- **Provider Selection**: Tests setting Ollama as the active provider
- **Search Integration**: Tests semantic search with provider parameter
- **UI State Management**: Tests loading states and result handling

## Expected Results

### Successful Integration
- All tests should pass without errors
- Ollama embeddings should be generated successfully
- Semantic search should return relevant results
- Router execution should create valid execution plans

### Common Issues

1. **Ollama Not Running**
   - Error: `ConnectionError` when connecting to Ollama
   - Solution: Start Ollama service

2. **Model Not Available**
   - Error: Model not found
   - Solution: Pull the required model with `ollama pull <model_name>`

3. **Backend Services Not Running**
   - Error: Connection refused to Redis/PostgreSQL
   - Solution: Start required services

4. **Network Issues**
   - Error: Timeout when connecting to services
   - Solution: Check firewall settings and service configurations

## Manual Verification

You can also manually verify the integration using curl:

```bash
# Test Ollama health
curl http://localhost:11434/api/tags

# Test Ollama embedding
curl http://localhost:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3:8b", "input": "Hello, world!"}'

# Test semantic search with Ollama provider
curl http://localhost:8000/api/v1/vector/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "provider": "ollama"}'

# Test router execution with Ollama provider
curl http://localhost:8000/api/v1/router/plan_execution \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "provider": "ollama"}'
```

## Troubleshooting

If tests fail, check the following:

1. **Environment Variables**: Ensure `.env` file has correct OLLAMA configuration
2. **Service Status**: Verify all required services are running
3. **Network Connectivity**: Check that services can communicate with each other
4. **Model Availability**: Ensure the specified Ollama model is downloaded
5. **Logs**: Check service logs for detailed error information

For any issues, please review the service logs and ensure all dependencies are properly configured.
