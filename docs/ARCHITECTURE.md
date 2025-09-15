# Node-Based LLM System Architecture

## Overview

The Node-Based LLM System is a comprehensive platform for managing and interacting with LLM-powered nodes, featuring Ollama integration, conflict resolution, and an interactive canvas interface.

## System Architecture

### Backend Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   PostgreSQL    │    │     Redis       │
│                 │    │   Database      │    │     Cache       │
│  - REST API     │◄──►│  - Nodes Table  │    │  - Context     │
│  - WebSocket    │    │  - Chat History │    │  - Sessions    │
│  - CORS         │    │  - Conflicts    │    │                │
│  - JWT Auth     │    │  - Auth Users   │    │                │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Ollama LLM    │    │   OpenAI API    │    │   Prometheus    │
│   (Primary)     │    │   (Fallback)    │    │   Monitoring    │
│                 │    │                 │    │                 │
│  - Local Model  │    │  - Cloud Model  │    │  - API Metrics  │
│  - Schema Gen   │    │  - Backup       │    │  - Error Track  │
│  - Conflict Det │    │                 │    │  - Latency      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Frontend Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │    │   Redux Store   │    │   Material-UI   │
│                 │    │                 │    │                 │
│  - Components   │◄──►│  - State Mgmt   │    │  - UI Library   │
│  - Routing      │    │  - Actions      │    │  - Theming      │
│  - Hooks        │    │  - Reducers     │    │  - Components   │
│  - JWT Auth     │    │  - Auth State   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐
│   D3.js Graph   │    │   WebSocket     │
│  Visualization  │    │   Real-time     │
│                 │    │                 │
│  - Force Layout │    │  - Live Updates │
│  - Node Dragging│    │  - Chat         │
│  - Edge Drawing │    │  - Notifications│
└─────────────────┘    └─────────────────┘
```

## Best Practices

### Security
- **JWT Authentication**: Implement JWT tokens for secure API access
- **Input Validation**: Validate all user inputs to prevent injection attacks
- **CORS Configuration**: Properly configure CORS for frontend-backend communication
- **Rate Limiting**: Implement rate limiting for API endpoints
- **SQL Injection Prevention**: Use SQLAlchemy ORM for safe database queries
- **Environment Variables**: Store sensitive configuration in environment variables

### Scalability
- **Redis Caching**: Use Redis for caching frequent node queries and session data
- **Database Connection Pooling**: Implement connection pooling for better performance
- **Async Operations**: Use async/await for I/O operations
- **Horizontal Scaling**: Design for stateless API deployment
- **Load Balancing**: Prepare for load balancer deployment

### Monitoring
- **Prometheus Integration**: Monitor API latency and error tracking
- **Logging**: Comprehensive logging for debugging and monitoring
- **Health Checks**: Implement health check endpoints
- **Performance Metrics**: Track response times and resource usage
- **Error Tracking**: Monitor and alert on system errors

### Testing
- **Unit Tests**: Add unit tests for LLM fallback and conflict resolution logic
- **Integration Tests**: Test API endpoints and database operations
- **E2E Tests**: End-to-end testing for user workflows
- **Performance Tests**: Load testing for scalability validation

## API Endpoints

### Node Management
| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/nodes` | POST | Create a new node | JWT Required |
| `/nodes/{id}` | GET | Retrieve node details | JWT Required |
| `/nodes/{id}` | PUT | Update node content | JWT Required |
| `/nodes/{id}` | DELETE | Delete a node | JWT Required |
| `/nodes/graph` | GET | Get full node graph data | JWT Required |
| `/nodes/search/{query}` | GET | Search nodes by name or content | JWT Required |

### Conflict Management
| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/conflicts` | GET | List all conflicts | JWT Required |
| `/conflicts/{id}` | POST | Resolve a conflict | JWT Required |
| `/nodes/conflicts/detect` | POST | Detect conflicts between nodes | JWT Required |
| `/nodes/conflicts/resolve` | POST | Create conflict resolution node | JWT Required |

### LLM Integration
| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/llm/generate` | POST | Generate LLM response | JWT Required |
| `/llm/schema` | POST | Generate database schema | JWT Required |
| `/llm/policy` | POST | Generate policy rules | JWT Required |
| `/nodes/{id}/generate` | POST | Generate context for specific node | JWT Required |

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | User login |
| `/auth/register` | POST | User registration |
| `/auth/refresh` | POST | Refresh JWT token |
| `/auth/logout` | POST | User logout |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `/ws` | Real-time updates and chat |

## Database Schema

### Enhanced Nodes Table
```sql
CREATE TABLE nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    type ENUM('schema', 'policy', 'general', 'correction') DEFAULT 'general',
    content JSON NOT NULL,
    parent_id UUID REFERENCES nodes(id),
    status ENUM('pending', 'resolved', 'conflicting', 'active') DEFAULT 'active',
    conflict_with UUID REFERENCES nodes(id),
    llm_model_used TEXT DEFAULT 'ollama',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);
```

### Users Table (for JWT Authentication)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);
```

### Node Relationships
```sql
CREATE TABLE node_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    child_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    relationship_type TEXT DEFAULT 'child',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(parent_id, child_id)
);
```

### Chat History
```sql
CREATE TABLE node_chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    message TEXT NOT NULL,
    sender TEXT NOT NULL,
    llm_model_used TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Conflicts
```sql
CREATE TABLE node_conflicts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_1_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    node_2_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    conflict_type TEXT NOT NULL,
    conflict_description TEXT,
    resolution_node_id UUID REFERENCES nodes(id),
    status TEXT DEFAULT 'pending',
    resolved_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);
```

### API Keys (for external integrations)
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP
);
```

## Core Components

### 1. Node Service
- **Purpose**: Manages node CRUD operations and relationships
- **Key Features**:
  - Create, update, delete nodes
  - Manage parent-child relationships
  - Handle node conflicts
  - Generate context using LLM
  - Search and filtering capabilities

### 2. Ollama Service
- **Purpose**: Primary LLM integration with fallback
- **Key Features**:
  - Local model processing
  - Schema generation
  - Policy generation
  - Conflict detection
  - Token management
  - Fallback to OpenAI API

### 3. Authentication Service
- **Purpose**: Handle user authentication and authorization
- **Key Features**:
  - JWT token generation and validation
  - User registration and login
  - Password hashing and verification
  - Role-based access control
  - Session management

### 4. Canvas Component
- **Purpose**: Interactive node visualization
- **Key Features**:
  - Drag-and-drop interface
  - Node graph visualization
  - Real-time updates
  - Zoom and pan controls
  - Node selection and editing

### 5. Node Chat
- **Purpose**: Node-specific conversation interface
- **Key Features**:
  - Context switching
  - LLM interaction
  - Message history
  - Real-time chat
  - User authentication

## Data Flow

### Node Creation Flow
```
1. User authenticates with JWT
2. User clicks "Create Node"
3. Frontend sends POST to /api/nodes/ with JWT
4. Backend validates JWT and creates node in database
5. If parent exists, updates parent's child_nodes
6. Returns node data to frontend
7. Frontend updates Redux store
8. Canvas re-renders with new node
```

### Conflict Detection Flow
```
1. System detects potential conflicts
2. Ollama analyzes node contexts
3. If conflicts found:
   - Mark nodes as "conflicting"
   - Create resolution node
   - Send notification via WebSocket
4. User resolves conflict
5. Update both nodes with resolution
6. Mark nodes as "resolved"
7. Log resolution in audit trail
```

### LLM Integration Flow
```
1. User requests LLM generation
2. Backend validates JWT and rate limits
3. Backend calls Ollama service
4. If Ollama fails, fallback to OpenAI
5. Process response and update node
6. Cache result in Redis
7. Send real-time update via WebSocket
8. Frontend updates UI
```

## Security Considerations

### API Security
- JWT authentication for all protected endpoints
- CORS configuration for frontend access
- Input validation and sanitization
- SQL injection prevention via SQLAlchemy
- Rate limiting for LLM API calls
- API key management for external integrations

### Data Security
- UUID primary keys for all entities
- Encrypted storage for sensitive data
- Audit trail for all node changes
- Secure WebSocket connections
- Password hashing with bcrypt
- Session management with Redis

### Network Security
- HTTPS enforcement in production
- Secure headers configuration
- CSRF protection
- XSS prevention
- Content Security Policy

## Performance Optimizations

### Backend
- Database connection pooling
- Redis caching for frequently accessed data
- Async/await for I/O operations
- Pagination for large datasets
- Database query optimization
- Background task processing

### Frontend
- React.memo for component optimization
- Redux state normalization
- Lazy loading for components
- Virtual scrolling for large lists
- Code splitting and bundling
- Service worker for caching

## Scalability

### Horizontal Scaling
- Stateless API design
- Database connection pooling
- Redis for session management
- Load balancer ready
- Microservices architecture ready
- Container orchestration support

### Vertical Scaling
- Efficient database queries
- Caching strategies
- Memory optimization
- Background task processing
- Resource monitoring
- Performance profiling

## Monitoring and Logging

### Backend Monitoring
- Prometheus metrics collection
- Request/response logging
- Database query performance
- LLM API response times
- Error tracking and alerting
- Resource usage monitoring

### Frontend Monitoring
- User interaction tracking
- Performance metrics
- Error boundary implementation
- Real-time user analytics
- Page load times
- API call performance

### Logging Strategy
- Structured logging with JSON format
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Centralized log aggregation
- Log rotation and retention
- Audit trail for security events

## Deployment

### Development
```bash
# Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm start
```

### Production
```bash
# Backend
cd backend
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Frontend
cd frontend
npm run build
```

### Docker Deployment
```dockerfile
# Backend Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker"]
```

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://localhost/node_llm_system
REDIS_URL=redis://localhost:6379

# LLM
OLLAMA_MODEL=llama3
OPENAI_API_KEY=your-openai-api-key

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Monitoring
PROMETHEUS_ENABLED=True
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
```

## Testing Strategy

### Backend Testing
- Unit tests for services (LLM fallback, conflict resolution)
- Integration tests for API endpoints
- Database migration tests
- LLM integration tests
- Authentication tests
- Performance tests

### Frontend Testing
- Component unit tests
- Redux store tests
- Integration tests
- E2E tests with Cypress
- Accessibility tests
- Performance tests

### Test Coverage
- Aim for 80%+ code coverage
- Critical path testing
- Security testing
- Load testing
- API contract testing

## Documentation

### API Documentation
- Swagger UI for FastAPI endpoints
- OpenAPI 3.0 specification
- Interactive API testing
- Request/response examples
- Authentication documentation

### User Guide
- Node creation workflow
- Conflict resolution steps
- Token management guide
- Canvas interaction tutorial
- Chat interface usage
- Troubleshooting guide

### Developer Documentation
- Architecture overview
- Setup instructions
- Development guidelines
- Deployment procedures
- Contributing guidelines

## Future Enhancements

### Planned Features
- Multi-user support with roles
- Advanced conflict resolution algorithms
- Node templates and libraries
- Export/import functionality
- Advanced analytics and insights
- Mobile app support
- Real-time collaboration
- Version control for nodes

### Technical Improvements
- GraphQL API implementation
- Microservices architecture
- Kubernetes deployment
- Advanced caching strategies
- Real-time collaboration features
- Machine learning integration
- Advanced security features
- Performance optimizations 