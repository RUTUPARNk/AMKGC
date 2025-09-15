#!/usr/bin/env python3
"""
Test script to check backend startup and cache management endpoints
"""

import sys
import os
import asyncio
import httpx

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_cache_endpoints():
    """Test cache management endpoints"""
    print("\n=== Testing Cache Management Endpoints ===")
    
    # Use the same settings as the main app
    from backend.config.config import settings
    base_url = f"http://{settings.API_HOST}:{settings.API_PORT}"
    
    async with httpx.AsyncClient() as client:
        try:
            # Test health endpoint first
            response = await client.get(f"{base_url}/health")
            print(f"Health check: {response.status_code}")
            
            # Test cache stats endpoint (existing)
            response = await client.get(f"{base_url}/api/v1/monitoring/cache-stats")
            print(f"Cache stats endpoint: {response.status_code}")
            if response.status_code == 200:
                print(f"Cache stats: {response.json()}")
            
            # Test get all cache entries endpoint (new)
            response = await client.get(f"{base_url}/api/v1/cache")
            print(f"Get all cache entries: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Cache entries: {data}")
            
            print("✅ Cache endpoint tests completed!")
            
        except Exception as e:
            print(f"❌ Error testing cache endpoints: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Main test function"""
    try:
        print("Testing imports...")
        from backend.config.config import settings
        print("✅ Config imported successfully")
        
        from backend.main import app
        print("✅ FastAPI app imported successfully")
        
        print(f"Settings loaded:")
        print(f"  - API_HOST: {settings.API_HOST}")
        print(f"  - API_PORT: {settings.API_PORT}")
        print(f"  - OLLAMA_MODEL: {settings.OLLAMA_MODEL}")
        print(f"  - DEBUG: {settings.DEBUG}")
        
        # Test cache endpoints
        await test_cache_endpoints()
        
        print("\n✅ All backend tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())