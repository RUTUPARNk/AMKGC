# Node-Based LLM System

A comprehensive system for managing and interacting with LLM-powered nodes, featuring Ollama integration and conflict resolution.

## Features

- **Node Management**: Create, update, and manage nodes with structured context
- **Ollama Integration**: Primary LLM processing with local Ollama models
- **Conflict Resolution**: Automatic detection and resolution of node conflicts
- **Token Management**: Handle large contexts with continuation nodes
- **Interactive UI**: Canvas-based interface with drag-and-drop functionality
- **Real-time Chat**: Node-specific chat interfaces for context switching

## Architecture

### Backend
- **Framework**: FastAPI with SQLAlchemy
- **Database**: PostgreSQL for nodes, Redis for caching
- **LLM**: Ollama (primary), OpenAI (fallback)
- **API**: RESTful endpoints with WebSocket support

### Frontend
- **Framework**: React with TypeScript
- **Visualization**: D3.js for node graphs
- **UI**: Material-UI components
- **State Management**: Redux Toolkit

## Quick Start

### Prerequisites
1. Install Ollama: https://ollama.com/download
2. Install PostgreSQL and Redis
3. Python 3.8+ and Node.js 16+

### Backend Setup
```bash
cd backend
pip install -r ../requirements.txt
python -m alembic upgrade head
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Database Setup
```bash
# Create database
createdb node_llm_system

# Run migrations
cd backend
alembic upgrade head
```

## Usage

1. **Create Nodes**: Use the canvas to create new nodes
2. **Ask Questions**: Generate context by asking questions
3. **Resolve Conflicts**: System automatically detects and helps resolve conflicts
4. **Chat Interface**: Use node-specific chat for context switching

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## License

MIT License 