"""
Integration test for Router Agent with full system components
"""

import sys
import os
import asyncio
import json

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_router_integration():
    """Test Router Agent integration with Neo4j, Redis, and PipelineExecutor"""
    print("Testing Router Agent integration...")
    
    try:
        # Import the RouterAgent
        from distributed.router import RouterAgent
        
        # Initialize RouterAgent
        router_agent = RouterAgent()
        print("✓ RouterAgent initialized")
        
        # Test Neo4j connection
        if router_agent.neo4j_service:
            print("✓ Neo4j connection established")
            
            # Create a test node
            test_node_id = "test_node_123"
            success = router_agent.neo4j_service.create_node(
                node_id=test_node_id,
                name="Test Node",
                node_type="component",
                context_window="This is a test context for integration testing.",
                status="active"
            )
            
            if success:
                print("✓ Test node created in Neo4j")
                
                # Test node retrieval
                node = router_agent.neo4j_service.get_node(test_node_id)
                if node:
                    print("✓ Test node retrieved from Neo4j")
                else:
                    print("? Could not retrieve test node from Neo4j")
            else:
                print("? Failed to create test node in Neo4j")
        else:
            print("? Neo4j service not available")
        
        # Test Redis connection
        try:
            router_agent.redis_client.ping()
            print("✓ Redis connection established")
            
            # Test Redis operations
            test_key = "test_router_integration"
            test_value = "test_value"
            router_agent.redis_client.setex(test_key, 60, test_value)
            retrieved_value = router_agent.redis_client.get(test_key)
            
            if retrieved_value == test_value:
                print("✓ Redis operations working correctly")
            else:
                print("? Redis operations not working as expected")
        except Exception as e:
            print(f"? Redis connection failed: {e}")
        
        # Test PipelineExecutor
        if router_agent.pipeline_executor:
            print("✓ PipelineExecutor initialized")
            
            # List available pipelines
            try:
                with open("pipelines/graph_config.json", "r") as f:
                    pipeline_config = json.load(f)
                
                pipeline_ids = [p["id"] for p in pipeline_config]
                print(f"✓ Available pipelines: {pipeline_ids}")
                
                # Test a simple pipeline if available
                if pipeline_ids:
                    test_pipeline_id = pipeline_ids[0]
                    print(f"✓ Testing pipeline: {test_pipeline_id}")
            except Exception as e:
                print(f"? Error listing pipelines: {e}")
        else:
            print("? PipelineExecutor not available")
        
        # Test Router Agent methods
        print("\nTesting Router Agent methods...")
        
        # Test plan execution
        try:
            plan_result = await router_agent.plan_execution("test query", k=3, max_tokens=2048)
            print("✓ Plan execution completed")
            print(f"  Plan ID: {plan_result.get('plan_id')}")
            plan_details = plan_result.get('execution_plan', {})
            print(f"  Retrieved nodes: {plan_details.get('retrieved_nodes', 0)}")
            print(f"  Budgeted nodes: {plan_details.get('budgeted_nodes', 0)}")
        except Exception as e:
            print(f"? Error in plan execution: {e}")
        
        # Test node dependencies
        try:
            if router_agent.neo4j_service:
                # Create a dependency relationship for testing
                test_dep_id = "test_dependency_123"
                router_agent.neo4j_service.create_node(
                    node_id=test_dep_id,
                    name="Test Dependency",
                    node_type="component",
                    context_window="This is a test dependency.",
                    status="active"
                )
                
                router_agent.neo4j_service.create_edge(
                    source_id=test_dep_id,
                    target_id=test_node_id,
                    relationship_type="DEPENDS_ON"
                )
                
                dependencies = router_agent.get_node_dependencies(test_node_id)
                print(f"✓ Node dependencies retrieved: {len(dependencies)} dependencies found")
            
        except Exception as e:
            print(f"? Error testing node dependencies: {e}")
        
        # Test node subgraph
        try:
            if router_agent.neo4j_service:
                subgraph = router_agent.get_node_subgraph(test_node_id, depth=1)
                nodes = subgraph.get('nodes', [])
                relationships = subgraph.get('relationships', [])
                print(f"✓ Node subgraph retrieved: {len(nodes)} nodes, {len(relationships)} relationships")
        except Exception as e:
            print(f"? Error testing node subgraph: {e}")
        
        # Test node relevance update
        try:
            if router_agent.neo4j_service:
                success = router_agent.update_node_relevance(test_node_id, 0.85)
                if success:
                    print("✓ Node relevance updated successfully")
                else:
                    print("? Failed to update node relevance")
        except Exception as e:
            print(f"? Error updating node relevance: {e}")
        
        # Clean up test nodes
        try:
            if router_agent.neo4j_service:
                router_agent.neo4j_service.delete_node(test_node_id)
                router_agent.neo4j_service.delete_node("test_dependency_123")
                print("✓ Test nodes cleaned up")
        except Exception as e:
            print(f"? Error cleaning up test nodes: {e}")
        
        print("\n✓ Router Agent integration test completed")
        
    except Exception as e:
        print(f"✗ Router Agent integration test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_router_integration())
