import sys
print("Python version:", sys.version)
print("Python executable:", sys.executable)

try:
    import requests
    print("✅ requests module is available")
except ImportError:
    print("❌ requests module is not available")

try:
    import fastapi
    print("✅ fastapi module is available")
except ImportError:
    print("❌ fastapi module is not available")

try:
    import uvicorn
    print("✅ uvicorn module is available")
except ImportError:
    print("❌ uvicorn module is not available")
