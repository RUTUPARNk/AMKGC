import requests
import json

try:
    response = requests.get('http://localhost:11434/api/tags', timeout=5)
    print("Ollama is running!")
    print("Available models:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Failed to connect to Ollama: {e}")
