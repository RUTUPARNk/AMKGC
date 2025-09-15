#!/usr/bin/env python3
"""
Test Model Fetcher

This script demonstrates the new Ollama model fetching capabilities
and shows how to integrate them with the Node LLM System.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.llm_service import LLMService


def test_model_fetcher():
    """Test the model fetching capabilities"""
    print("🤖 Testing Ollama Model Fetcher")
    print("=" * 50)
    
    # Initialize LLM service
    llm_service = LLMService()
    
    # Check Ollama status
    print("1. Checking Ollama status...")
    if llm_service.check_ollama_status():
        print("✅ Ollama is running and accessible!")
    else:
        print("❌ Ollama is not running or not accessible!")
        print("Please start Ollama first: ollama serve")
        return
    
    # Get available models
    print("\n2. Fetching available models...")
    available_models = llm_service.get_available_ollama_models()
    
    if not available_models:
        print("❌ No models found!")
        print("You may need to pull some models first:")
        print("  ollama pull llama2")
        print("  ollama pull mistral")
        return
    
    print(f"✅ Found {len(available_models)} model(s):")
    for i, model in enumerate(available_models, 1):
        print(f"   {i}. {model}")
    
    # Show current model
    print(f"\n3. Current model: {llm_service.ollama_model}")
    
    # Validate current model
    print(f"\n4. Validating current model...")
    if llm_service.validate_ollama_model(llm_service.ollama_model):
        print(f"✅ Model '{llm_service.ollama_model}' is available!")
    else:
        print(f"❌ Model '{llm_service.ollama_model}' is not available!")
        
        # Try to get first available model
        first_model = llm_service.get_first_available_model()
        if first_model:
            print(f"🔄 Updating to first available model: {first_model}")
            if llm_service.update_ollama_model(first_model):
                print(f"✅ Successfully updated to: {first_model}")
            else:
                print(f"❌ Failed to update model")
    
    # Test model switching
    print(f"\n5. Testing model switching...")
    if len(available_models) > 1:
        # Try switching to a different model
        for model in available_models:
            if model != llm_service.ollama_model:
                print(f"🔄 Testing switch to: {model}")
                if llm_service.update_ollama_model(model):
                    print(f"✅ Successfully switched to: {model}")
                    break
                else:
                    print(f"❌ Failed to switch to: {model}")
    
    # Test a simple generation
    print(f"\n6. Testing generation with current model...")
    try:
        result = llm_service.generate("Hello! Please respond with just 'Hello from Ollama!'")
        if result.get('success'):
            print(f"✅ Generation successful!")
            print(f"Response: {result.get('response', '')[:100]}...")
        else:
            print(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Generation error: {e}")
    
    print(f"\n🎉 Model fetcher test completed!")


def test_standalone_fetcher():
    """Test the standalone model fetcher script"""
    print("\n" + "=" * 50)
    print("🧪 Testing Standalone Model Fetcher")
    print("=" * 50)
    
    try:
        # Import and test the standalone fetcher
        from get_ollama_model import get_first_ollama_model
        
        model_name = get_first_ollama_model()
        if model_name:
            print(f"✅ Standalone fetcher found model: {model_name}")
        else:
            print("❌ Standalone fetcher found no models")
    except ImportError as e:
        print(f"❌ Could not import standalone fetcher: {e}")


if __name__ == "__main__":
    test_model_fetcher()
    test_standalone_fetcher() 