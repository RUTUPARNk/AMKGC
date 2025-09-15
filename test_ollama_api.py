import requests
import json

print("Testing Ollama API connection...")

try:
    # Test if Ollama API is accessible
    response = requests.get('http://localhost:11434/api/tags', timeout=5)
    if response.status_code == 200:
        print("✅ Ollama API is accessible!")
        models = response.json()
        print("Available models:")
        print(json.dumps(models, indent=2))
    else:
        print(f"❌ Ollama API returned status code: {response.status_code}")
        print(response.text)
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to Ollama API. Is Ollama running?")
except requests.exceptions.Timeout:
    print("❌ Request to Ollama API timed out")
except Exception as e:
    print(f"❌ Error testing Ollama API: {e}")
