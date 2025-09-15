"""
Stress test for pipeline execution
Runs multiple parallel tasks to test for deadlocks, memory leaks, or task starvation
"""

import asyncio
import httpx
import time
import psutil
import os
from concurrent.futures import ThreadPoolExecutor
import threading

# Test configuration
NUM_PARALLEL_TASKS = 50
PIPELINE_NAME = "multi_model_analysis"
TEST_TEXT = "The quick brown fox jumps over the lazy dog. This is a sample text for stress testing the pipeline execution system. We are testing parallel execution to ensure there are no deadlocks, memory leaks, or task starvation issues."

async def run_single_pipeline(client, task_id):
    """Run a single pipeline execution task"""
    test_input = {
        "pipeline": PIPELINE_NAME,
        "input_data": {
            "text": f"{TEST_TEXT} Task ID: {task_id}"
        }
    }
    
    try:
        start_time = time.time()
        response = await client.post(
            "http://localhost:8000/api/v1/run_pipeline",
            json=test_input,
            timeout=120.0
        )
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status', 'unknown')
            return {
                'task_id': task_id,
                'status': status,
                'execution_time': execution_time,
                'success': True
            }
        else:
            return {
                'task_id': task_id,
                'status': 'error',
                'execution_time': execution_time,
                'error': f"HTTP {response.status_code}: {response.text}",
                'success': False
            }
    except Exception as e:
        return {
            'task_id': task_id,
            'status': 'exception',
            'execution_time': 0,
            'error': str(e),
            'success': False
        }

async def run_parallel_pipelines(num_tasks):
    """Run multiple pipeline executions in parallel"""
    print(f"Starting stress test with {num_tasks} parallel tasks...")
    
    # Monitor system resources
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    print(f"Initial memory usage: {initial_memory:.2f} MB")
    
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        # Create tasks
        tasks = [run_single_pipeline(client, i) for i in range(num_tasks)]
        
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Check final memory usage
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_diff = final_memory - initial_memory
    
    print(f"\nStress test completed in {total_time:.2f} seconds")
    print(f"Final memory usage: {final_memory:.2f} MB")
    print(f"Memory difference: {memory_diff:.2f} MB")
    
    # Analyze results
    successful = 0
    failed = 0
    exceptions = 0
    total_execution_time = 0
    
    for result in results:
        if isinstance(result, Exception):
            exceptions += 1
            print(f"Exception: {result}")
        elif result['success']:
            successful += 1
            total_execution_time += result['execution_time']
        else:
            failed += 1
            print(f"Task {result['task_id']} failed: {result.get('error', 'Unknown error')}")
    
    print(f"\nResults:")
    print(f"  Successful: {successful}/{num_tasks}")
    print(f"  Failed: {failed}/{num_tasks}")
    print(f"  Exceptions: {exceptions}/{num_tasks}")
    
    if successful > 0:
        avg_execution_time = total_execution_time / successful
        print(f"  Average execution time: {avg_execution_time:.2f} seconds")
    
    # Check for potential issues
    if memory_diff > 100:  # More than 100MB increase
        print("⚠️  WARNING: Significant memory increase detected - possible memory leak")
    
    if failed > 0 or exceptions > 0:
        print("⚠️  WARNING: Some tasks failed or threw exceptions")
    
    if successful == num_tasks:
        print("✅ All tasks completed successfully")
    else:
        print("❌ Some tasks failed")
    
    return {
        'total_tasks': num_tasks,
        'successful': successful,
        'failed': failed,
        'exceptions': exceptions,
        'total_time': total_time,
        'avg_execution_time': avg_execution_time if successful > 0 else 0,
        'memory_increase': memory_diff
    }

async def run_subpipeline_stress_test(num_tasks):
    """Run stress test specifically for sub-pipelines"""
    print(f"\nStarting sub-pipeline stress test with {num_tasks} parallel tasks...")
    
    # For now, we'll simulate this by running the same pipeline multiple times
    # In a full implementation, we would specifically test sub-pipelines
    
    return await run_parallel_pipelines(num_tasks)

def monitor_system_resources():
    """Monitor system resources during stress test"""
    while True:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        print(f"CPU: {cpu_percent}% | Memory: {memory.percent}%")

async def main():
    """Main stress test function"""
    print("Pipeline Executor Stress Test")
    print("=" * 40)
    
    # Start resource monitoring in background
    # monitor_thread = threading.Thread(target=monitor_system_resources, daemon=True)
    # monitor_thread.start()
    
    try:
        # Run stress test with regular pipelines
        results = await run_parallel_pipelines(NUM_PARALLEL_TASKS)
        
        # Run stress test with sub-pipelines
        # subpipeline_results = await run_subpipeline_stress_test(NUM_PARALLEL_TASKS // 2)
        
        print("\n" + "=" * 40)
        print("Stress Test Summary")
        print("=" * 40)
        print(f"Total tasks: {results['total_tasks']}")
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")
        print(f"Exceptions: {results['exceptions']}")
        print(f"Total time: {results['total_time']:.2f} seconds")
        print(f"Average execution time: {results['avg_execution_time']:.2f} seconds")
        print(f"Memory increase: {results['memory_increase']:.2f} MB")
        
        if results['successful'] == results['total_tasks']:
            print("\n🎉 All stress tests passed!")
        else:
            print("\n⚠️  Some stress tests failed. Check the logs above for details.")
            
    except Exception as e:
        print(f"Error during stress test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
