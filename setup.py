#!/usr/bin/env python3
"""
Setup script for Node-Based LLM System
"""

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_prerequisites():
    """Check if required software is installed"""
    print("Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8+ is required")
        return False
    print("✓ Python version is compatible")
    
    # Check if Ollama is installed
    try:
        subprocess.run(["ollama", "--version"], check=True, capture_output=True)
        print("✓ Ollama is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ Ollama not found. Please install from https://ollama.com/download")
    
    # Check if PostgreSQL is running
    try:
        subprocess.run(["psql", "--version"], check=True, capture_output=True)
        print("✓ PostgreSQL is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ PostgreSQL not found. Please install PostgreSQL")
    
    # Check if Redis is running
    try:
        subprocess.run(["redis-cli", "ping"], check=True, capture_output=True)
        print("✓ Redis is running")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ Redis not found. Please install and start Redis")
    
    return True

def setup_backend():
    """Setup the backend"""
    print("\nSetting up backend...")
    
    # Install Python dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    # Create database
    if not run_command("createdb node_llm_system", "Creating database"):
        print("⚠ Database creation failed. You may need to create it manually:")
        print("  createdb node_llm_system")
    
    # Run database migrations
    if not run_command("cd backend && python -m alembic upgrade head", "Running database migrations"):
        print("⚠ Database migrations failed. You may need to run them manually:")
        print("  cd backend && python -m alembic upgrade head")
    
    return True

def setup_frontend():
    """Setup the frontend"""
    print("\nSetting up frontend...")
    
    # Install Node.js dependencies
    if not run_command("cd frontend && npm install", "Installing Node.js dependencies"):
        return False
    
    return True

def create_env_file():
    """Create .env file with default configuration"""
    env_content = """# Node-Based LLM System Configuration

# Database
DATABASE_URL=postgresql://localhost/node_llm_system

# Redis
REDIS_URL=redis://localhost:6379

# LLM Configuration
OLLAMA_MODEL=llama3
OPENAI_API_KEY=your-openai-api-key-here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# CORS
CORS_ORIGINS=*

# Token Limits
MAX_TOKENS=2000000

# Security
SECRET_KEY=your-secret-key-here
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✓ Created .env file with default configuration")
    print("⚠ Please update the .env file with your actual configuration")

def main():
    """Main setup function"""
    print("Node-Based LLM System Setup")
    print("=" * 40)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n✗ Prerequisites check failed. Please install required software.")
        return False
    
    # Setup backend
    if not setup_backend():
        print("\n✗ Backend setup failed.")
        return False
    
    # Setup frontend
    if not setup_frontend():
        print("\n✗ Frontend setup failed.")
        return False
    
    # Create environment file
    create_env_file()
    
    print("\n" + "=" * 40)
    print("✓ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Update the .env file with your configuration")
    print("2. Start the backend: cd backend && uvicorn main:app --reload")
    print("3. Start the frontend: cd frontend && npm start")
    print("4. Open http://localhost:3000 in your browser")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 