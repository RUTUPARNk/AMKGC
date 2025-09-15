#!/usr/bin/env python3
"""
Demo script for Node LLM System with Ollama
This script demonstrates the core functionality without needing the full server setup.
"""

import sys
import os
import json
import time

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")

def print_section(title):
    print(f"\n📋 {title}")
    print("-" * 40)

def main():
    print_header("Node LLM System Demo with Ollama")
    
    try:
        # Import the LLM service
        print_section("Testing LLM Service")
        from backend.services.llm_service import LLMService
        
        # Initialize the LLM service
        llm_service = LLMService()
        print("✅ LLM Service initialized successfully")
        print(f"🤖 Using Ollama model: {llm_service.ollama_model}")
        
        # Test basic generation
        print_section("Testing Basic LLM Generation")
        prompt = "Hello! Can you tell me a short joke?"
        print(f"📝 Prompt: {prompt}")
        
        try:
            result = llm_service.generate(prompt, model='ollama')
            print("✅ LLM Generation successful!")
            print(f"🤖 Response: {result['content']}")
            print(f"📊 Tokens used: {result['tokens_used']}")
            print(f"🔧 Provider: {result['provider']}")
        except Exception as e:
            print(f"❌ LLM Generation failed: {e}")
            print("💡 Make sure Ollama is running with: ollama serve")
            print("💡 And pull a model with: ollama pull llama3")
            return
        
        # Test schema generation
        print_section("Testing Schema Generation")
        table_name = "users"
        description = "A table to store user information"
        
        try:
            schema_result = llm_service.generate_schema(table_name, description)
            print("✅ Schema Generation successful!")
            print(f"📋 Generated schema for table '{table_name}':")
            print(schema_result['content'])
        except Exception as e:
            print(f"❌ Schema Generation failed: {e}")
        
        # Test policy generation
        print_section("Testing Policy Generation")
        policy_type = "access control"
        context = "User authentication and authorization"
        
        try:
            policy_result = llm_service.generate_policy(policy_type, context)
            print("✅ Policy Generation successful!")
            print(f"📋 Generated {policy_type} policy:")
            print(policy_result['content'])
        except Exception as e:
            print(f"❌ Policy Generation failed: {e}")
        
        # Test conflict detection
        print_section("Testing Conflict Detection")
        node1_context = "Users should have admin access to all systems"
        node2_context = "Users should only have access to their own data"
        
        try:
            conflict_result = llm_service.detect_conflicts(node1_context, node2_context)
            print("✅ Conflict Detection successful!")
            print(f"🔍 Detected conflicts: {len(conflict_result['conflicts'])}")
            print(f"⚠️  Severity: {conflict_result['severity']}")
            print(f"🎯 Priority: {conflict_result['priority']}")
            print(f"💡 Suggestions: {len(conflict_result['suggestions'])}")
        except Exception as e:
            print(f"❌ Conflict Detection failed: {e}")
        
        # Test token management
        print_section("Testing Token Management")
        long_text = "This is a very long text. " * 1000  # Create a long text
        
        try:
            exceeds_limit, token_count = llm_service.check_token_limit(long_text)
            print(f"📊 Token count: {token_count}")
            print(f"⚠️  Exceeds limit: {exceeds_limit}")
            
            if exceeds_limit:
                print("🔄 Splitting content...")
                chunks = llm_service.split_context(long_text)
                print(f"✅ Split into {len(chunks)} chunks")
                for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                    print(f"   Chunk {i+1}: {len(chunk)} characters")
        except Exception as e:
            print(f"❌ Token Management failed: {e}")
        
        print_header("Demo Completed Successfully!")
        print("🎉 The Node LLM System is working with Ollama!")
        print("\n📚 What you can do next:")
        print("1. 🖥️  Start the full server: python start_backend.py")
        print("2. 🌐 Visit the API docs: http://localhost:8000/docs")
        print("3. 🧪 Test the API endpoints")
        print("4. 🎨 Build the frontend interface")
        print("5. 🔧 Customize the system for your needs")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 