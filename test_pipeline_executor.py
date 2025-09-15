"""
Test script for pipeline executor
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from pipeline.executor import PipelineExecutor
    print("✅ Successfully imported PipelineExecutor")
    
    # Test the executor
    executor = PipelineExecutor("pipelines/graph_config.json")
    print(f"✅ Loaded {len(executor.graphs)} pipeline(s)")
    
    # List available pipelines
    if executor.graphs:
        print("Available pipelines:")
        for graph in executor.graphs:
            print(f"  - {graph.get('id', 'Unknown ID')}: {graph.get('description', 'No description')}")
    else:
        print("⚠️ No pipelines found")
        
    print("✅ Pipeline executor test completed successfully")
    
except Exception as e:
    print(f"❌ Error testing pipeline executor: {e}")
    import traceback
    traceback.print_exc()
