#!/usr/bin/env python3
"""
Simple test script to verify the warm-up service is working
"""

import subprocess
import time
import requests

OLLAMA_API = "http://localhost:11434/api/generate"

print("Testing Ollama warm-up service...")

# Check if Ollama is running
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    print(f"✅ Ollama API is accessible: {response.status_code}")
except Exception as e:
    print(f"❌ Ollama API is not accessible: {e}")

# Check ollama ps
try:
    result = subprocess.check_output(["ollama", "ps"], stderr=subprocess.STDOUT)
    output = result.decode()
    print(f"✅ ollama ps command works:")
    print(output)
except Exception as e:
    print(f"❌ ollama ps command failed: {e}")

# Try to load a model
try:
    print("🔄 Loading llama3:latest...")
    response = requests.post(OLLAMA_API, json={
        "model": "llama3:latest",
        "prompt": "ping",
        "stream": False
    }, timeout=30)
    
    if response.status_code == 200:
        print("✅ Model loaded successfully")
        print(f"Response: {response.json().get('response', '')}")
    else:
        print(f"❌ Failed to load model: {response.status_code} - {response.text}")
except Exception as e:
    print(f"❌ Error loading model: {e}")

print("\nTest completed.")
