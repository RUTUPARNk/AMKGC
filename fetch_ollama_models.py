#!/usr/bin/env python3
"""
Ollama Model Fetcher

This script fetches and displays information about available Ollama models.
It can be used to:
- List all available models
- Get detailed information about specific models
- Check model status and availability
- Validate model names for the Node LLM System
"""

import subprocess
import json
import requests
import sys
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class OllamaModel:
    """Represents an Ollama model with its properties."""
    name: str
    size: Optional[int] = None
    modified_at: Optional[str] = None
    digest: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class OllamaModelFetcher:
    """Handles fetching and managing Ollama model information."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
    
    def check_ollama_status(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_available_models(self) -> List[OllamaModel]:
        """Fetch all available models from Ollama."""
        try:
            # Try API first
            response = requests.get(f"{self.api_url}/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = []
                for model_data in data.get("models", []):
                    model = OllamaModel(
                        name=model_data.get("name", ""),
                        size=model_data.get("size"),
                        modified_at=model_data.get("modified_at"),
                        digest=model_data.get("digest"),
                        details=model_data
                    )
                    models.append(model)
                return models
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
        
        # Fallback to CLI
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return self._parse_cli_output(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"CLI fallback failed: {e}")
        
        return []
    
    def _parse_cli_output(self, output: str) -> List[OllamaModel]:
        """Parse the output of 'ollama list' command."""
        models = []
        lines = output.strip().split('\n')
        
        # Skip header line
        for line in lines[1:]:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    size_str = parts[1] if len(parts) > 1 else None
                    size = self._parse_size(size_str) if size_str else None
                    
                    model = OllamaModel(name=name, size=size)
                    models.append(model)
        
        return models
    
    def _parse_size(self, size_str: str) -> Optional[int]:
        """Parse size string (e.g., '3.8GB') to bytes."""
        if not size_str:
            return None
        
        try:
            size_str = size_str.upper()
            if 'GB' in size_str:
                size = float(size_str.replace('GB', '')) * 1024 * 1024 * 1024
            elif 'MB' in size_str:
                size = float(size_str.replace('MB', '')) * 1024 * 1024
            elif 'KB' in size_str:
                size = float(size_str.replace('KB', '')) * 1024
            else:
                size = float(size_str)
            return int(size)
        except ValueError:
            return None
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model."""
        try:
            response = requests.post(
                f"{self.api_url}/show",
                json={"name": model_name},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to get model info for {model_name}: {e}")
        
        return None
    
    def validate_model(self, model_name: str) -> bool:
        """Check if a model exists and is available."""
        models = self.get_available_models()
        return any(model.name == model_name for model in models)
    
    def get_model_names(self) -> List[str]:
        """Get a simple list of model names."""
        models = self.get_available_models()
        return [model.name for model in models]
    
    def format_size(self, size_bytes: Optional[int]) -> str:
        """Format size in bytes to human-readable format."""
        if size_bytes is None:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}PB"
    
    def print_models(self, models: List[OllamaModel], detailed: bool = False):
        """Print model information in a formatted way."""
        if not models:
            print("No models found.")
            return
        
        print(f"\n📋 Found {len(models)} Ollama model(s):")
        print("=" * 80)
        
        for i, model in enumerate(models, 1):
            print(f"\n{i}. Model: {model.name}")
            
            if model.size:
                print(f"   Size: {self.format_size(model.size)}")
            
            if model.modified_at:
                try:
                    dt = datetime.fromisoformat(model.modified_at.replace('Z', '+00:00'))
                    print(f"   Modified: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                except ValueError:
                    print(f"   Modified: {model.modified_at}")
            
            if detailed and model.details:
                print(f"   Details: {json.dumps(model.details, indent=2)}")
            
            print("-" * 40)


def main():
    """Main function to run the Ollama model fetcher."""
    print("🤖 Ollama Model Fetcher")
    print("=" * 50)
    
    fetcher = OllamaModelFetcher()
    
    # Check if Ollama is running
    print("Checking Ollama status...")
    if not fetcher.check_ollama_status():
        print("❌ Ollama is not running or not accessible!")
        print("Please start Ollama first:")
        print("  ollama serve")
        sys.exit(1)
    
    print("✅ Ollama is running and accessible!")
    
    # Get available models
    print("\nFetching available models...")
    models = fetcher.get_available_models()
    
    if not models:
        print("❌ No models found!")
        print("You may need to pull some models first:")
        print("  ollama pull llama2")
        print("  ollama pull mistral")
        sys.exit(1)
    
    # Display models
    fetcher.print_models(models, detailed=False)
    
    # Show model names for easy copying
    print(f"\n📝 Model names (for use in .env file):")
    print("Available models:")
    for model in models:
        print(f"  - {model.name}")
    
    # Interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        print(f"\n🔍 Interactive mode:")
        while True:
            try:
                model_name = input("\nEnter model name to get details (or 'quit' to exit): ").strip()
                if model_name.lower() in ['quit', 'exit', 'q']:
                    break
                
                if model_name:
                    if fetcher.validate_model(model_name):
                        info = fetcher.get_model_info(model_name)
                        if info:
                            print(f"\n📊 Details for '{model_name}':")
                            print(json.dumps(info, indent=2))
                        else:
                            print(f"Could not fetch detailed info for '{model_name}'")
                    else:
                        print(f"❌ Model '{model_name}' not found!")
                        print("Available models:", ", ".join(fetcher.get_model_names()))
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except EOFError:
                break


if __name__ == "__main__":
    main() 