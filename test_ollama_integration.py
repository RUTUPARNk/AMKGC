import requests
import json
import time

OLLAMA_URL = "http://localhost:11434"

print("Testing Ollama Integration...")
print("=" * 40)

# 1. Check if Ollama is running
try:
    response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
    if response.status_code == 200:
        print("✅ Ollama is running and accessible")
        models = response.json()
        print(f"📦 Available models: {len(models.get('models', []))}")
        for model in models.get('models', []):
            print(f"  - {model['name']}")
    else:
        print(f"❌ Ollama returned status code: {response.status_code}")
        exit(1)
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to Ollama. Is it running?")
    exit(1)
except Exception as e:
    print(f"❌ Error checking Ollama: {e}")
    exit(1)

print()

# 2. Test a simple prompt with llama3 (assuming it exists)
model_to_test = "llama3:latest"
print(f"Testing model: {model_to_test}")

try:
    start_time = time.time()
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": model_to_test,
            "prompt": "Hello, world!",
            "stream": False
        },
        timeout=30
    )
    end_time = time.time()
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Model test successful!")
        print(f"⏱  Response time: {end_time - start_time:.2f} seconds")
        print(f"📝 Response: {result.get('response', '')[:50]}...")
    else:
        print(f"❌ Model test failed with status code: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Error testing model: {e}")

print()
print("Test completed.")
