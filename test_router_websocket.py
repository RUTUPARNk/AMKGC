"""
Test script for Router Agent WebSocket functionality
"""

import asyncio
import websockets
import json
import time

async def test_router_websocket():
    """Test Router Agent WebSocket functionality"""
    print("Testing Router Agent WebSocket functionality...")
    
    # WebSocket URL
    ws_url = "ws://localhost:8000/api/v1/ws/router/test_session"
    
    try:
        # Connect to WebSocket
        async with websockets.connect(ws_url) as websocket:
            print("✓ Connected to Router WebSocket")
            
            # Subscribe to router updates
            subscribe_message = {
                "type": "SUBSCRIBE_ROUTER_UPDATES"
            }
            await websocket.send(json.dumps(subscribe_message))
            print("✓ Sent subscription request")
            
            # Wait for confirmation
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                if data.get("type") == "ROUTER_SUBSCRIPTION_CONFIRMED":
                    print("✓ Subscription confirmed")
                else:
                    print(f"? Unexpected response: {data}")
            except asyncio.TimeoutError:
                print("? No subscription confirmation received (timeout)")
            
            # Listen for updates for a short period
            print("Listening for router updates for 10 seconds...")
            start_time = time.time()
            
            try:
                while time.time() - start_time < 10:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(response)
                        if data.get("type") == "ROUTER_UPDATE":
                            print(f"✓ Received router update: {data.get('payload', {}).get('event', 'unknown')}")
                        else:
                            print(f"? Received non-router update: {data.get('type')}")
                    except asyncio.TimeoutError:
                        # No message received, continue
                        pass
            except Exception as e:
                print(f"? Error during update listening: {e}")
            
            print("✓ WebSocket test completed")
            
    except Exception as e:
        print(f"✗ WebSocket connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_router_websocket())
