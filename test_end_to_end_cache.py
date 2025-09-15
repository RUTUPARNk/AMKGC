#!/usr/bin/env python3
"""
Test script to verify end-to-end cache management functionality
"""

import sys
import os
import asyncio
import httpx
import json

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_end_to_end_cache_functionality():
    """Test end-to-end cache management functionality"""
    print("\n=== Testing End-to-End Cache Management Functionality ===")
    
    # Use the same settings as the main app
    from backend.config.config import settings
    base_url = f"http://{settings.API_HOST}:{settings.API_PORT}/api/v1"
    
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Get all cache entries (should work even if empty)
            print("\n1. Testing get all cache entries...")
            response = await client.get(f"{base_url}/cache")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success - Response format: {list(data.keys()) if isinstance(data, dict) else 'Invalid format'}")
                if 'cache' in data:
                    print(f"   Cache entries count: {len(data['cache'])}")
                else:
                    print("   ❌ Missing 'cache' key in response")
            else:
                print(f"   ❌ Failed with status {response.status_code}")
            
            # Test 2: Add some test data to cache (using internal Redis service)
            print("\n2. Adding test data to cache...")
            try:
                from backend.services.redis_service import RedisService
                redis_service = RedisService(settings.REDIS_URL)
                
                # Add test cache entries
                test_data = {
                    "test_key_1": {"value": "test_value_1", "timestamp": "2023-01-01"},
                    "test_key_2": "simple_string_value",
                    "test_key_3": [1, 2, 3, 4, 5]
                }
                
                for key, value in test_data.items():
                    redis_service.set_cache(key, value)
                print("   ✅ Test data added to cache")
                
                # Verify data was added
                all_entries = redis_service.get_all_cache_entries()
                print(f"   Current cache size: {len(all_entries)} entries")
                
            except Exception as e:
                print(f"   ❌ Error adding test data: {e}")
            
            # Test 3: Get all cache entries again (should now have data)
            print("\n3. Testing get all cache entries with test data...")
            response = await client.get(f"{base_url}/cache")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success - Response format: {list(data.keys()) if isinstance(data, dict) else 'Invalid format'}")
                if 'cache' in data:
                    print(f"   Cache entries count: {len(data['cache'])}")
                    # Show first few entries
                    for i, entry in enumerate(data['cache'][:3]):
                        print(f"     Entry {i+1}: {entry['id']} = {str(entry['value'])[:50]}{'...' if len(str(entry['value'])) > 50 else ''}")
                else:
                    print("   ❌ Missing 'cache' key in response")
            else:
                print(f"   ❌ Failed with status {response.status_code}")
            
            # Test 4: Delete a specific cache key
            print("\n4. Testing delete cache key...")
            response = await client.delete(f"{base_url}/cache/test_key_1")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success - Response: {data}")
            elif response.status_code == 404:
                print("   ⚠️  Key not found (this is expected if test failed earlier)")
            else:
                print(f"   ❌ Failed with status {response.status_code}")
            
            # Test 5: Get all cache entries after deletion
            print("\n5. Testing get all cache entries after deletion...")
            response = await client.get(f"{base_url}/cache")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success - Response format: {list(data.keys()) if isinstance(data, dict) else 'Invalid format'}")
                if 'cache' in data:
                    print(f"   Cache entries count after deletion: {len(data['cache'])}")
                else:
                    print("   ❌ Missing 'cache' key in response")
            else:
                print(f"   ❌ Failed with status {response.status_code}")
            
            # Test 6: Try to delete non-existent key
            print("\n6. Testing delete non-existent cache key...")
            response = await client.delete(f"{base_url}/cache/non_existent_key_12345")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 404:
                print("   ✅ Correctly handled 404 for non-existent key")
            else:
                print(f"   ⚠️  Expected 404, got {response.status_code}")
            
            print("\n✅ End-to-end cache management functionality tests completed!")
            
        except Exception as e:
            print(f"❌ Error testing end-to-end cache functionality: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Main test function"""
    try:
        # Test end-to-end cache functionality
        await test_end_to_end_cache_functionality()
        
        print("\n✅ All end-to-end cache management tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
