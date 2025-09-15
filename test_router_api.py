"""
Test script for Router Agent API endpoints
"""

import requests
import json
import time

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"

def test_router_endpoints():
    """Test all Router Agent API endpoints"""
    print("Testing Router Agent API endpoints...")
    
    # Test 1: Plan execution
    print("\n1. Testing plan execution...")
    try:
        response = requests.post(
            f"{BASE_URL}/plan_execution",
            json={
                "query": "test query",
                "k": 3,
                "max_tokens": 2048
            }
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Plan execution successful: {result['plan_id']}")
            plan_id = result['plan_id']
        else:
            print(f"✗ Plan execution failed: {response.status_code} - {response.text}")
            plan_id = None
    except Exception as e:
        print(f"✗ Plan execution error: {e}")
        plan_id = None
    
    # Test 2: Execute plan (if plan was created)
    print("\n2. Testing plan execution...")
    if plan_id:
        try:
            response = requests.post(
                f"{BASE_URL}/execute_plan",
                json={
                    "plan_id": plan_id
                }
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Plan execution successful: {result['successful_executions']} successful executions")
            else:
                print(f"✗ Plan execution failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"✗ Plan execution error: {e}")
    else:
        print("✗ Skipping plan execution test (no plan ID available)")
    
    # Test 3: Get node dependencies
    print("\n3. Testing node dependencies...")
    try:
        response = requests.get(f"{BASE_URL}/node_dependencies/test_node_id")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Node dependencies successful: {len(result['dependencies'])} dependencies")
        else:
            print(f"✗ Node dependencies failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ Node dependencies error: {e}")
    
    # Test 4: Get node subgraph
    print("\n4. Testing node subgraph...")
    try:
        response = requests.get(f"{BASE_URL}/node_subgraph/test_node_id?depth=1")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Node subgraph successful: {len(result.get('nodes', []))} nodes")
        else:
            print(f"✗ Node subgraph failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ Node subgraph error: {e}")
    
    # Test 5: Update node relevance
    print("\n5. Testing node relevance update...")
    try:
        response = requests.post(
            f"{BASE_URL}/update_relevance",
            json={
                "node_id": "test_node_id",
                "relevance_score": 0.8
            }
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Node relevance update successful: {result['success']}")
        else:
            print(f"✗ Node relevance update failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ Node relevance update error: {e}")
    
    print("\nAPI endpoint tests completed.")

if __name__ == "__main__":
    test_router_endpoints()
