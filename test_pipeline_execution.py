"""
Test script for pipeline execution
"""

import asyncio
import httpx
import json

async def test_pipeline_execution():
    """Test the pipeline execution endpoint"""
    # Test data
    test_input = {
        "pipeline": "summarize_and_translate",
        "input_data": {
            "text": "The quick brown fox jumps over the lazy dog. This is a sample text for testing the pipeline execution."
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/run_pipeline",
                json=test_input,
                timeout=60.0
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                print("Pipeline executed successfully!")
                result = response.json()
                print(f"Pipeline: {result.get('pipeline')}")
                print(f"Output: {result.get('output')}")
                print(f"Status: {result.get('status')}")
                
                # Print trace if available
                trace = result.get('trace', {})
                print("\nExecution Trace:")
                for node_id, node_result in trace.items():
                    print(f"  {node_id}: {node_result.get('status')} - {node_result.get('output', '')[:100]}...")
            else:
                print(f"Error: {response.text}")
                
    except Exception as e:
        print(f"Error executing pipeline: {e}")
        import traceback
        traceback.print_exc()

async def test_list_pipelines():
    """Test the list pipelines endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/api/v1/list_pipelines",
                timeout=30.0
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
    except Exception as e:
        print(f"Error listing pipelines: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing pipeline execution...")
    asyncio.run(test_list_pipelines())
    print("\n" + "="*50 + "\n")
    asyncio.run(test_pipeline_execution())
