import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/api/v1/ws/sessions"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Listen for messages
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    print(f"Received: {data}")
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed")
                    break
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
