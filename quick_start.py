#!/usr/bin/env python3
"""
Quick start script for Node LLM System with Ollama
This script will start the backend with minimal dependencies for testing.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def print_step(step, message):
    print(f"\n{'='*50}")
    print(f"STEP {step}: {message}")
    print(f"{'='*50}")

def check_ollama():
    """Check if Ollama is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
            return True
        else:
            print(f"⚠️  Ollama responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Ollama is not running")
        return False

def get_first_ollama_model():
    """Get the first available Ollama model"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            if models:
                return models[0].get("name", "llama3")
    except requests.exceptions.RequestException:
        pass
    
    # Fallback to CLI
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # Skip header line
                first_model_line = lines[1]
                if first_model_line.strip():
                    model_name = first_model_line.split()[0]
                    return model_name
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return "llama3"  # Default fallback

def create_minimal_env():
    """Create a minimal .env file for testing"""
    # Get the first available model
    model_name = get_first_ollama_model()
    print(f"📋 Using Ollama model: {model_name}")
    
    env_content = f"""# Minimal configuration for testing
DATABASE_URL=sqlite:///./test.db
REDIS_URL=redis://localhost:6379
OLLAMA_MODEL={model_name}
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
SECRET_KEY=test-secret-key-for-development
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    print("✅ Created minimal .env file")

def main():
    print("🚀 Node LLM System Quick Start")
    print("This script will help you get the system running with Ollama for testing.")
    
    # Step 1: Check Ollama
    print_step(1, "Checking Ollama")
    if not check_ollama():
        print("\n🔄 Starting Ollama...")
        print("Please make sure Ollama is running. You can start it with:")
        print("ollama serve")
        print("\nThen in another terminal, pull a model:")
        print("ollama pull llama3")
        print("ollama pull mistral")
        input("\nPress Enter when Ollama is running...")
    
    # Step 2: Create minimal environment
    print_step(2, "Creating Minimal Environment")
    create_minimal_env()
    
    # Step 3: Start the backend
    print_step(3, "Starting Backend Server")
    print("Starting the Node LLM System backend...")
    print("The API will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server")
    print("="*50)
    
    # Start the backend
    try:
        subprocess.run([sys.executable, "start_backend.py"])
    except KeyboardInterrupt:
        print("\n\n🛑 Backend server stopped")
        print("Thank you for using Node LLM System!")

if __name__ == "__main__":
    main() 