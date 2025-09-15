# Quick Start Guide

## Prerequisites

1. **Python 3.8+**
2. **Node.js 16+**
3. **PostgreSQL** (with pgvector extension)
4. **Redis**
5. **Ollama** (https://ollama.com/download)

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd node-llm-system
```

### 2. Run Setup Script
```bash
python setup.py
```

This will:
- Check prerequisites
- Install Python dependencies
- Install Node.js dependencies
- Create database
- Create `.env` file
- Install pgvector extension for PostgreSQL

### 3. Configure Environment
Edit the `.env` file with your configuration:
```bash
# Database
DATABASE_URL=postgresql://localhost/node_llm_system

# Redis
REDIS_URL=redis://localhost:6379

# LLM Configuration
OLLAMA_MODEL=llama3
OPENAI_API_KEY=your-openai-api-key-here

# Vector Service Configuration
EMBEDDER=local  # or openai
EMBEDDING_DIM=1536
VECTOR_DISTANCE=cosine
VECTOR_TOP_K=5

# Continuation Service Configuration
CONTINUATION_TOKEN_LIMIT=2000000
CONTINUATION_MIN_TOKENS=100000

# Clarification Service Configuration
CLARIFICATION_LLM_PROVIDER=ollama
AUTO_CREATE_CLARIFICATION_NODES=false
CLARIFICATION_MIN_CONFIDENCE=0.7

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
```

### 4. Start Ollama
```bash
# Install and run a model
ollama run llama3
```

### 5. Start the Backend
```bash
cd backend
uvicorn main:app --reload
```

The API will be available at: http://localhost:8000

### 6. Start the Frontend
```bash
cd frontend
npm start
```

The frontend will be available at: http://localhost:3000

## Usage

### Creating Nodes

1. **Open the Canvas**: Navigate to the main canvas view
2. **Create Node**: Click the "+" button in the toolbar
3. **Fill Details**: Enter node name, type, and context
4. **Save**: Click "Create Node" to save

### Node Types

- **General**: Default node type for general information
- **Schema**: Database schema definitions
- **Policy**: Security and access policies
- **Correction**: Conflict resolution nodes

### Using LLM Features

1. **Generate Context**: Click on a node and use the chat interface
2. **Ask Questions**: Type questions to generate node content
3. **Schema Generation**: Create schema nodes with table descriptions
4. **Policy Generation**: Create policy nodes with rule descriptions

### Conflict Resolution

1. **Detect Conflicts**: System automatically detects conflicts between nodes
2. **Review Conflicts**: Conflicting nodes are highlighted in red
3. **Resolve**: Use the conflict resolution interface to merge or correct
4. **Confirm**: Apply the resolution to update both nodes

### Canvas Features

- **Zoom**: Use zoom controls to adjust view
- **Pan**: Drag to move around the canvas
- **Select**: Click nodes to select them
- **Drag**: Drag nodes to reposition them
- **Connect**: Nodes automatically connect based on relationships

## API Endpoints

### Nodes
- `GET /api/nodes/` - List all nodes
- `POST /api/nodes/` - Create a new node
- `GET /api/nodes/{id}` - Get a specific node
- `PUT /api/nodes/{id}` - Update a node
- `DELETE /api/nodes/{id}` - Delete a node

### LLM
- `POST /api/llm/generate` - Generate LLM response
- `POST /api/llm/schema` - Generate schema
- `POST /api/llm/policy` - Generate policy

### Conflicts
- `POST /api/nodes/conflicts/detect` - Detect conflicts
- `POST /api/nodes/conflicts/resolve` - Resolve conflicts

### Graph
- `GET /api/nodes/graph` - Get node graph data
- `GET /api/nodes/search/{query}` - Search nodes

## WebSocket Events

### Node Updates
```json
{
  "type": "node_updated",
  "data": {
    "id": "node-id",
    "name": "Node Name",
    "context_window": "Updated context"
  }
}
```

### Conflict Detection
```json
{
  "type": "conflict_detected",
  "data": {
    "node1_id": "node-1-id",
    "node2_id": "node-2-id",
    "conflict_type": "schema",
    "description": "Conflict description"
  }
}
```

## Troubleshooting

### Common Issues

1. **Ollama Not Found**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Database Connection Error**
   ```bash
   # Create database
   createdb node_llm_system
   ```

3. **Redis Connection Error**
   ```bash
   # Start Redis
   redis-server
   ```

4. **Port Already in Use**
   ```bash
   # Change port in .env file
   API_PORT=8001
   ```

### Debug Mode

Enable debug mode for detailed logging:
```bash
# In .env file
DEBUG=True
```

### Logs

Check logs for errors:
```bash
# Backend logs
cd backend
uvicorn main:app --reload --log-level debug

# Frontend logs
cd frontend
npm start
```

## Development

### Backend Development
```bash
cd backend
pip install -r ../requirements.txt
uvicorn main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Database Migrations
```bash
cd backend
alembic upgrade head
```

### Testing
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Production Deployment

### Backend
```bash
cd backend
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend
```bash
cd frontend
npm run build
# Serve the build folder with nginx or similar
```

### Environment Variables
Set production environment variables:
```bash
export DATABASE_URL="postgresql://user:pass@host:port/db"
export REDIS_URL="redis://host:port"
export SECRET_KEY="your-secret-key"
export DEBUG=False
```

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the architecture documentation
3. Check the API documentation at http://localhost:8000/docs
4. Open an issue in the repository

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 