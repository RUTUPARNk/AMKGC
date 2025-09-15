"""
Simple test script for Merge Agent functionality
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from backend.distributed.merge import MergeAgent
    print("✓ Successfully imported MergeAgent")
    
    # Test creating an instance
    merge_agent = MergeAgent()
    print("✓ Successfully created MergeAgent instance")
    
    # Test helper methods
    parent_content = "Line 1\nLine 2\nLine 3"
    child_content = "Line 1\nLine 2 modified\nLine 3\nLine 4"
    
    diff = merge_agent._compute_unified_diff(parent_content, child_content)
    print(f"✓ Unified diff computed: {len(diff)} characters")
    
    print("All tests passed!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
