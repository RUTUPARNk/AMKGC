"""
Test script for Merge Agent functionality
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.distributed.merge import MergeAgent

async def test_merge_agent():
    """Test the Merge Agent functionality"""
    print("Testing Merge Agent...")
    
    # Initialize the merge agent
    merge_agent = MergeAgent()
    
    # Test 1: Check if services are available
    print("\n1. Checking service availability...")
    if merge_agent.neo4j_service:
        print("  ✓ Neo4j service available")
    else:
        print("  ✗ Neo4j service not available")
    
    if merge_agent.versioning_service:
        print("  ✓ Versioning service available")
    else:
        print("  ✗ Versioning service not available")
    
    # Test 2: Test helper methods
    print("\n2. Testing helper methods...")
    
    # Test unified diff computation
    parent_content = "This is the original content\nWith multiple lines\nFor testing purposes"
    child_content = "This is the modified content\nWith multiple lines\nFor testing purposes\nAnd an additional line"
    
    diff = merge_agent._compute_unified_diff(parent_content, child_content)
    print(f"  Unified diff computed: {len(diff)} characters")
    
    # Test semantic summarizer (placeholder)
    summary = merge_agent._semantic_summarizer(parent_content, child_content, diff)
    print(f"  Semantic summary generated: {len(summary)} characters")
    
    # Test impact estimation
    impact = merge_agent._estimate_impact(diff)
    print(f"  Impact estimation: {impact}")
    
    print("\nMerge Agent tests completed.")
    print("Note: Full functionality requires Neo4j database with existing nodes.")

if __name__ == "__main__":
    asyncio.run(test_merge_agent())
