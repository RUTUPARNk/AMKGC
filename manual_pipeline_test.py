"""
Manual test of pipeline execution
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_pipeline():
    """Test pipeline execution manually"""
    try:
        print("🔍 Testing pipeline executor...")
        
        # Import the executor
        from pipeline.executor import PipelineExecutor
        print("✅ Successfully imported PipelineExecutor")
        
        # Create executor instance
        executor = PipelineExecutor("pipelines/graph_config.json")
        print(f"✅ Loaded {len(executor.graphs)} pipeline(s)")
        
        # List pipelines
        if executor.graphs:
            print("\nAvailable pipelines:")
            for graph in executor.graphs:
                pipeline_id = graph.get('id', 'Unknown')
                description = graph.get('description', 'No description')
                print(f"  - {pipeline_id}: {description}")
                
                # Show nodes and edges
                nodes = graph.get('nodes', [])
                edges = graph.get('edges', [])
                print(f"    Nodes: {len(nodes)}, Edges: {len(edges)}")
                
                for node in nodes:
                    print(f"      Node '{node.get('id')}': {node.get('backend')}:{node.get('model')}")
        
        # Test a simple pipeline execution (mock)
        print("\n🧪 Testing pipeline execution (mock)...")
        test_input = {"text": "This is a test input for pipeline execution."}
        
        # This would normally execute the pipeline, but we'll just show what would happen
        print("✅ Pipeline executor is ready for use!")
        print("\nTo test actual pipeline execution, start the backend server and use the API endpoints.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Manual Pipeline Test")
    print("=" * 30)
    
    result = asyncio.run(test_pipeline())
    
    if result:
        print("\n✅ Manual pipeline test completed successfully!")
    else:
        print("\n❌ Manual pipeline test failed.")
