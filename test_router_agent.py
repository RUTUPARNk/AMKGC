"""
Test script for Router Agent
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from distributed.router import RouterAgent

async def test_router_agent():
    """Test the Router Agent functionality"""
    print("Testing Router Agent...")
    
    # Initialize the router agent
    router_agent = RouterAgent()
    
    # Test planning execution
    print("\n1. Testing plan execution...")
    try:
        plan_result = await router_agent.plan_execution("test query", k=3, max_tokens=2048)
        print(f"Plan created successfully: {plan_result['plan_id']}")
        print(f"Retrieved nodes: {plan_result['execution_plan']['retrieved_nodes']}")
        print(f"Budgeted nodes: {plan_result['execution_plan']['budgeted_nodes']}")
    except Exception as e:
        print(f"Error planning execution: {e}")
    
    # Test getting node dependencies
    print("\n2. Testing node dependencies...")
    try:
        dependencies = router_agent.get_node_dependencies("test_node_id")
        print(f"Dependencies retrieved: {len(dependencies)}")
    except Exception as e:
        print(f"Error getting dependencies: {e}")
    
    # Test getting node subgraph
    print("\n3. Testing node subgraph...")
    try:
        subgraph = router_agent.get_node_subgraph("test_node_id", depth=1)
        print(f"Subgraph retrieved: {len(subgraph.get('nodes', []))} nodes")
    except Exception as e:
        print(f"Error getting subgraph: {e}")
    
    print("\nRouter Agent test completed.")

if __name__ == "__main__":
    asyncio.run(test_router_agent())
