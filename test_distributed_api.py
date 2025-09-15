"""
Test script for distributed API endpoints
"""

import sys
import os
import asyncio
import httpx

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_distributed_api():
    try:
        # Import the distributed API module
        from api.distributed import router
        
        print("✅ Successfully imported distributed API module")
        
        # Check if required endpoints exist
        expected_endpoints = [
            '/distributed/run_pipeline',
            '/distributed/submit_task',
            '/distributed/agents',
            '/distributed/watchdog',
            '/distributed/task/{task_id}'
        ]
        
        # Get all routes from the router
        routes = [route.path for route in router.routes]
        print(f"Available routes: {routes}")
        
        missing_endpoints = []
        for endpoint in expected_endpoints:
            # Handle parameterized routes
            if '{task_id}' in endpoint:
                # Check if a route with task parameter exists
                has_task_route = any('task' in route for route in routes)
                if not has_task_route:
                    missing_endpoints.append(endpoint)
            elif endpoint not in routes:
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            print(f"❌ Missing endpoints: {missing_endpoints}")
        else:
            print("✅ All distributed API endpoints are present")
        
        print("✅ Distributed API verification completed")
        
    except ImportError as e:
        print(f"❌ Failed to import distributed API module: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_distributed_api()
