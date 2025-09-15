# 🚀 Getting Started with Node LLM System

## Quick Start (Recommended)

The easiest way to get started is to use our automated setup script:

```bash
python setup_and_run.py
```

This script will:
1. ✅ Check all prerequisites
2. 📦 Install Python dependencies
3. 🤖 Verify Ollama is running
4. 🔴 Check Redis is running
5. 🐘 Verify PostgreSQL is running
6. 🗄️ Create and setup the database
7. 🚀 Start the backend server

## Manual Setup

If you prefer to set up manually, follow these steps:

### 1. Prerequisites

Make sure you have the following installed:

- **Python 3.8+**
- **Ollama** (https://ollama.ai/download)
- **Redis** (https://redis.io/download)
- **PostgreSQL** (https://postgresql.org/download)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Services

#### Start Ollama
```bash
# Start Ollama server
ollama serve

# In another terminal, pull a model
ollama pull llama3
```

#### Start Redis
```bash
redis-server
```

#### Start PostgreSQL
```bash
# On macOS with Homebrew
brew services start postgresql

# On Ubuntu/Debian
sudo systemctl start postgresql

# On Windows
# Start PostgreSQL service from Services
```

### 4. Setup Database

```bash
# Create database
createdb node_llm_system

# Run migrations
psql -h localhost -U postgres -d node_llm_system -f database/migrations/001_initial_schema.sql
```

### 5. Configure Environment

Edit the `.env` file with your settings:

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/node_llm_system

# Redis
REDIS_URL=redis://localhost:6379

# LLM
OLLAMA_MODEL=llama3

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

### 6. Start the Backend

```bash
python start_backend.py
```

## 🎯 What You'll Get

Once running, you'll have access to:

- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🧪 Test the System

### 1. Check Health
```bash
curl http://localhost:8000/health
```

### 2. Test LLM Generation
```bash
curl -X POST "http://localhost:8000/api/v1/llm/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how are you?", "model": "ollama"}'
```

### 3. Register a User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'
```

## 🔧 Troubleshooting

### Common Issues

1. **Ollama not found**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Database connection error**
   ```bash
   # Check PostgreSQL is running
   psql -h localhost -U postgres -c "SELECT 1"
   ```

3. **Redis connection error**
   ```bash
   # Check Redis is running
   redis-cli ping
   ```

4. **Port already in use**
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

## 📚 Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Create Nodes**: Use the API to create and manage nodes
3. **Test LLM Integration**: Try generating content with Ollama
4. **Build Frontend**: Set up the React frontend (see frontend/README.md)

## 🆘 Need Help?

- Check the troubleshooting section above
- Review the API documentation at http://localhost:8000/docs
- Check the logs for error messages
- Open an issue in the repository

## 🎉 Success!

You now have a fully functional Node LLM System running with:
- ✅ Ollama integration for local LLM processing
- ✅ Redis caching for performance
- ✅ PostgreSQL for data persistence
- ✅ RESTful API with comprehensive endpoints
- ✅ WebSocket support for real-time updates
- ✅ Conflict detection and resolution
- ✅ Token management and context splitting

Happy coding! 🚀 