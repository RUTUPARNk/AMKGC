import subprocess
import sys

try:
    # Try to check if Ollama is installed
    result = subprocess.run(['ollama', '--version'], capture_output=True, text=True, timeout=10)
    print("Ollama is installed:")
    print(result.stdout)
except FileNotFoundError:
    print("Ollama is not installed or not in PATH")
    sys.exit(1)
except Exception as e:
    print(f"Error checking Ollama: {e}")
    sys.exit(1)

try:
    # Try to list models
    result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
    print("\nAvailable models:")
    print(result.stdout)
except Exception as e:
    print(f"Error listing models: {e}")
