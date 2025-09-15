"""
Test script for sub-pipeline functionality
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_subpipelines():
    try:
        # Import the PipelineExecutor class
        from pipeline.executor import PipelineExecutor
        print("✅ Successfully imported PipelineExecutor")
        
        # Instantiate the executor
        executor = PipelineExecutor()
        print("✅ Successfully instantiated PipelineExecutor")
        
        # Check if subpipelines were loaded
        print(f"Loaded subpipelines: {list(executor.subpipelines.keys())}")
        
        # Test run_subpipeline method existence
        if hasattr(executor, 'run_subpipeline'):
            print("✅ run_subpipeline method is present")
        else:
            print("❌ run_subpipeline method is missing")
            return
            
        # Test get_node_by_id method existence
        if hasattr(executor, '_get_node_by_id'):
            print("✅ _get_node_by_id method is present")
        else:
            print("❌ _get_node_by_id method is missing")
            return
            
        print("✅ Sub-pipeline functionality verification completed")
        
    except ImportError as e:
        print(f"❌ Failed to import PipelineExecutor: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_subpipelines())
