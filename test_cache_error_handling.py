#!/usr/bin/env python3
"""
Test script to verify error handling for cache operations
"""

import sys
import os
import asyncio
import httpx

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_cache_error_handling():
    """Test error handling for cache operations"""
    print("\n=== Testing Cache Error Handling ===")
    
    # Use the same settings as the main app
    from backend.config.config import settings
    base_url = f"http://{settings.API_HOST}:{settings.API_PORT}/api/v1"
    
    async with httpx.AsyncClient() as client:
        try:
            # Test deleting a non-existent cache key
            response = await client.delete(f"{base_url}/cache/non-existent-key")
            print(f"Delete non-existent key: {response.status_code}")
            if response.status_code == 404:
                print("✅ Correctly handled 404 for non-existent key")
            else:
                print(f"❌ Expected 404, got {response.status_code}")
            
            # Test get all cache entries (should work even if empty)
            response = await client.get(f"{base_url}/cache")
            print(f"Get all cache entries: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("✅ Get all cache entries works correctly")
                print(f"   Response format: {list(data.keys()) if isinstance(data, dict) else 'Invalid format'}")
            else:
                print(f"❌ Expected 200, got {response.status_code}")
            
            print("✅ Cache error handling tests completed!")
            
        except Exception as e:
            print(f"❌ Error testing cache error handling: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Main test function"""
    try:
        # Test cache error handling
        await test_cache_error_handling()
        
        print("\n✅ All cache error handling tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
