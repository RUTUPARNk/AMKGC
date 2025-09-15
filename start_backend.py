#!/usr/bin/env python3
"""
Simple startup script for the Node LLM System backend
"""

import uvicorn
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.config.config import settings

if __name__ == "__main__":
    print("🚀 Starting Node LLM System Backend...")
    print(f"📍 Host: {settings.API_HOST}")
    print(f"🔌 Port: {settings.API_PORT}")
    print(f"🤖 Ollama Model: {settings.OLLAMA_MODEL}")
    print(f"🔗 API Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print(f"🔗 Health Check: http://{settings.API_HOST}:{settings.API_PORT}/health")
    print("=" * 50)
    
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 