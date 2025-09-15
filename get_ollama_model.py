#!/usr/bin/env python3
"""
Simple Ollama Model Getter

This script returns the first available Ollama model name.
Useful for automatically setting OLLAMA_MODEL in the Node LLM System.
"""

import subprocess
import requests
import sys
from typing import Optional


def get_first_ollama_model() -> Optional[str]:
    """Get the first available Ollama model name."""
    try:
        # Try API first
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            if models:
                return models[0].get("name")
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
    
    return None


def main():
    """Main function - prints the first available model name."""
    model_name = get_first_ollama_model()
    
    if model_name:
        print(model_name)
        return 0
    else:
        print("No Ollama models found", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 