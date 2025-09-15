"""
Test script for Neo4j integration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.neo4j_service import Neo4jService
from config.neo4j import neo4j_settings
import uuid


def test_neo4j_integration():
    """Test Neo4j integration"""
    print("Testing Neo4j integration...")
    
    # Initialize Neo4j service
    neo4j_service = Neo4jService(
        neo4j_settings.NEO4J_URI,
        neo4j_settings.NEO4J_USER,
        neo4j_settings.NEO4J_PASSWORD
    )
    
    # Generate test node ID
    test_node_id = str(uuid.uuid4())
    
    try:
        # Test creating a node
        print(f"Creating test node {test_node_id}...")
        success = neo4j_service.create_node(
            node_id=test_node_id,
            name="Test Node",
            node_type="test",
            context_window="This is a test context window",
            status="active",
            llm_model_used="ollama"
        )
        
        if success:
            print("✓ Node creation successful")
        else:
            print("✗ Node creation failed")
            return
        
        # Test getting the node
        print(f"Retrieving test node {test_node_id}...")
        node = neo4j_service.get_node(test_node_id)
        
        if node:
            print("✓ Node retrieval successful")
            print(f"  Node ID: {node.get('id')}")
            print(f"  Node Name: {node.get('name')}")
            print(f"  Node Type: {node.get('type')}")
        else:
            print("✗ Node retrieval failed")
            return
        
        # Test updating node context
        print(f"Updating node context for {test_node_id}...")
        success = neo4j_service.update_node_context(
            test_node_id, 
            "This is an updated test context window"
        )
        
        if success:
            print("✓ Node context update successful")
        else:
            print("✗ Node context update failed")
            return
        
        # Test creating a child node
        child_node_id = str(uuid.uuid4())
        print(f"Creating child node {child_node_id}...")
        success = neo4j_service.create_node(
            node_id=child_node_id,
            name="Child Test Node",
            node_type="test",
            context_window="This is a child test context window",
            status="active",
            llm_model_used="ollama"
        )
        
        if success:
            print("✓ Child node creation successful")
        else:
            print("✗ Child node creation failed")
            return
        
        # Test creating parent-child relationship
        print(f"Creating parent-child relationship...")
        success = neo4j_service.create_edge(
            source_id=test_node_id,
            target_id=child_node_id,
            relationship_type="PARENT_CHILD"
        )
        
        if success:
            print("✓ Parent-child relationship creation successful")
        else:
            print("✗ Parent-child relationship creation failed")
            return
        
        # Test getting child nodes
        print(f"Getting child nodes for {test_node_id}...")
        children = neo4j_service.get_child_nodes(test_node_id)
        
        if children:
            print("✓ Child nodes retrieval successful")
            print(f"  Found {len(children)} child nodes")
        else:
            print("✗ Child nodes retrieval failed or no children found")
        
        # Test creating version snapshot
        print(f"Creating version snapshot for {test_node_id}...")
        success = neo4j_service.create_version_snapshot(
            test_node_id, 
            1, 
            "This is version 1 context"
        )
        
        if success:
            print("✓ Version snapshot creation successful")
        else:
            print("✗ Version snapshot creation failed")
        
        # Test getting version snapshots
        print(f"Getting version snapshots for {test_node_id}...")
        versions = neo4j_service.get_version_snapshots(test_node_id)
        
        if versions:
            print("✓ Version snapshots retrieval successful")
            print(f"  Found {len(versions)} version snapshots")
        else:
            print("✗ Version snapshots retrieval failed or no versions found")
        
        # Test marking node as stale
        print(f"Marking node {test_node_id} as stale...")
        success = neo4j_service.mark_node_stale(test_node_id)
        
        if success:
            print("✓ Node staleness marking successful")
        else:
            print("✗ Node staleness marking failed")
        
        # Test getting stale nodes
        print("Getting stale nodes...")
        stale_nodes = neo4j_service.get_stale_nodes(1)  # 1 day threshold
        
        if stale_nodes:
            print("✓ Stale nodes retrieval successful")
            print(f"  Found {len(stale_nodes)} stale nodes")
        else:
            print("✗ Stale nodes retrieval failed or no stale nodes found")
        
        # Test deleting nodes
        print(f"Deleting child node {child_node_id}...")
        success = neo4j_service.delete_node(child_node_id)
        
        if success:
            print("✓ Child node deletion successful")
        else:
            print("✗ Child node deletion failed")
        
        print(f"Deleting test node {test_node_id}...")
        success = neo4j_service.delete_node(test_node_id)
        
        if success:
            print("✓ Test node deletion successful")
        else:
            print("✗ Test node deletion failed")
        
        print("\nAll tests completed!")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        raise
    
    finally:
        neo4j_service.close()


def main():
    """Main test function"""
    test_neo4j_integration()


if __name__ == "__main__":
    main()
