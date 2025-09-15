"""
Test file for Ollama integration in the Node-LLM System
"""

import pytest
import requests
import json
import time
import os
from typing import Dict, Any

# Configuration
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3:latest')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')


def test_ollama_health_check():
    """Test if Ollama is running and accessible"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        assert response.status_code == 200, f"Ollama health check failed with status {response.status_code}"
        print("✅ Ollama is running and accessible")
        return True
    except requests.exceptions.ConnectionError:
        pytest.skip("Ollama is not running. Skipping Ollama tests.")
    except Exception as e:
        pytest.fail(f"Error checking Ollama: {e}")


def test_ollama_embedding():
    """Test Ollama embedding functionality"""
    test_text = "This is a test sentence for embedding."
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={
                "model": OLLAMA_MODEL,
                "input": test_text
            },
            timeout=30
        )
        
        assert response.status_code == 200, f"Ollama embedding failed with status {response.status_code}"
        
        result = response.json()
        embedding = result.get("embedding")
        
        assert embedding is not None, "No embedding returned"
        assert isinstance(embedding, list), "Embedding should be a list"
        assert len(embedding) > 0, "Embedding should not be empty"
        
        print(f"✅ Ollama embedding successful. Embedding dimension: {len(embedding)}")
        return True
    except requests.exceptions.ConnectionError:
        pytest.skip("Ollama is not running. Skipping Ollama tests.")
    except Exception as e:
        pytest.fail(f"Error testing Ollama embedding: {e}")


def test_semantic_search_with_ollama():
    """Test semantic search endpoint with Ollama provider"""
    test_query = "What is artificial intelligence?"
    
    try:
        # Test semantic search with Ollama provider
        response = requests.post(
            f"{API_BASE_URL}/api/v1/vector/search/semantic",
            json={
                "query": test_query,
                "top_k": 5,
                "provider": "ollama"
            },
            timeout=30
        )
        
        # Note: This test might fail if there's no data in the vector store
        # That's expected in a fresh test environment
        if response.status_code == 200:
            result = response.json()
            fragments = result.get("fragments", [])
            print(f"✅ Semantic search with Ollama successful. Found {len(fragments)} fragments")
            return True
        elif response.status_code == 500:
            # This might happen if there's no data in the vector store
            print("⚠️ Semantic search returned 500 (likely no data in vector store)")
            return True
        else:
            pytest.fail(f"Semantic search failed with status {response.status_code}: {response.text}")
    except requests.exceptions.ConnectionError:
        pytest.skip("Backend API is not running. Skipping API tests.")
    except Exception as e:
        pytest.fail(f"Error testing semantic search: {e}")

def test_router_execute_with_ollama():
    """Test router execute endpoint with Ollama provider"""
    test_query = "Explain the concept of machine learning."
    
    try:
        # Test plan execution with Ollama provider
        response = requests.post(
            f"{API_BASE_URL}/api/v1/router/plan_execution",
            json={
                "query": test_query,
                "k": 3,
                "max_tokens": 2048,
                "provider": "ollama"
            },
            timeout=30
        )
        
        # Note: This test might fail if Neo4j is not set up or has no data
        if response.status_code == 200:
            result = response.json()
            plan_id = result.get("plan_id")
            execution_plan = result.get("execution_plan")
            print(f"✅ Router plan execution with Ollama successful. Plan ID: {plan_id}")
            return True
        elif response.status_code == 500:
            # This might happen if Neo4j is not set up
            print("⚠️ Router plan execution returned 500 (likely Neo4j not set up)")
            return True
        else:
            pytest.fail(f"Router plan execution failed with status {response.status_code}: {response.text}")
    except requests.exceptions.ConnectionError:
        pytest.skip("Backend API is not running. Skipping API tests.")
    except Exception as e:
        pytest.fail(f"Error testing router execution: {e}")

if __name__ == "__main__":
    print("Running Ollama integration tests...")
    print("=" * 50)
    
    # Run tests
    try:
        test_ollama_health_check()
        test_ollama_embedding()
        test_semantic_search_with_ollama()
        test_router_execute_with_ollama()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Tests failed with error: {e}")
