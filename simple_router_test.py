"""
Simple test for Router Agent components
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

print("Router Agent components test")
print("============================")

# Test importing the router module
try:
    from distributed.router import RouterAgent
    print("✓ RouterAgent import successful")
except ImportError as e:
    print(f"✗ RouterAgent import failed: {e}")

# Test importing the router API
try:
    from api.router_queries import router
    print("✓ Router API import successful")
except ImportError as e:
    print(f"✗ Router API import failed: {e}")

# Test importing the websocket module
try:
    from api.websocket import router as websocket_router
    print("✓ WebSocket router import successful")
except ImportError as e:
    print(f"✗ WebSocket router import failed: {e}")

print("\nComponent tests completed.")
