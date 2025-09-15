"""
Test script for pipeline execution
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from pipeline.executor import PipelineExecutor

async def test_pipeline():
    """Test the pipeline executor"""
    print("Testing Pipeline Executor...")
    
    # Initialize the executor
    executor = PipelineExecutor("pipelines/graph_config.json")
    
    # Test listing pipelines
    print("\nAvailable pipelines:")
    for graph in executor.graphs:
        print(f"  - {graph.get('id', 'unnamed')}: {graph.get('description', 'No description')}")
    
    # Test a simple pipeline
    print("\nRunning summarize_and_translate pipeline...")
    input_data = {
        "text": "Artificial intelligence is a wonderful field that is developing rapidly. It has applications in many areas including healthcare, finance, and transportation."
    }
    
    result = await executor.run_pipeline("summarize_and_translate", input_data)
    print(f"\nPipeline result:")
    print(f"  Status: {result.get('status')}")
    print(f"  Output: {result.get('output', 'No output')}")
    
    if "trace" in result:
        print("\nExecution trace:")
        for node_id, node_result in result["trace"].items():
            print(f"  {node_id}: {node_result.get('status', 'unknown')} - {str(node_result.get('output', 'No output'))[:100]}...")
    
    if result.get("status") == "error":
        print(f"\nError: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
