#!/usr/bin/env python3
"""
Simple test script to verify backend health and Ollama integration
"""

import requests
import time

BACKEND_URL = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"

def test_backend_health():
    """Test backend health endpoint"""
    print("Testing backend health...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend health check successful")
            health_data = response.json()
            for service in health_data:
                print(f"  {service['name']}: {service['status']}")
            return True
        else:
            print(f"❌ Backend health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False

def test_ollama_api():
    """Test Ollama API directly"""
    print("\nTesting Ollama API...")
    
    try:
        # Check if Ollama is responsive
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            print("✅ Ollama API is responsive")
            models = response.json()
            print(f"  Available models: {len(models.get('models', []))}")
            return True
        else:
            print(f"❌ Ollama API check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama API check error: {e}")
        return False

def test_ollama_model():
    """Test Ollama model with a simple prompt"""
    print("\nTesting Ollama model...")
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "llama3:latest",
                "prompt": "Hello, world!",
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Ollama model test successful")
            print(f"  Response: {result.get('response', '')[:50]}...")
            return True
        else:
            print(f"❌ Ollama model test failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ollama model test error: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("Backend and Ollama Integration Test")
    print("=" * 50)
    
    # Test backend health
    backend_ok = test_backend_health()
    
    # Test Ollama API
    ollama_api_ok = test_ollama_api()
    
    # Test Ollama model
    ollama_model_ok = test_ollama_model()
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    print(f"Backend Health: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"Ollama API: {'✅ PASS' if ollama_api_ok else '❌ FAIL'}")
    print(f"Ollama Model: {'✅ PASS' if ollama_model_ok else '❌ FAIL'}")
    
    if backend_ok and ollama_api_ok and ollama_model_ok:
        print("\n🎉 All tests passed! The system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the system configuration.")

if __name__ == "__main__":
    main()
