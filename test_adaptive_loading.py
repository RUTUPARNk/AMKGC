#!/usr/bin/env python3
"""
Test script for adaptive loading functionality
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

try:
    import psutil
    print("✅ psutil is available")
    print(f"   Version: {psutil.__version__}")
    mem = psutil.virtual_memory()
    print(f"   Memory usage: {mem.percent}%")
except ImportError:
    print("❌ psutil is not available")
    print("   Please install it with: pip install psutil")
except Exception as e:
    print(f"❌ Error with psutil: {e}")

# Test the adaptive loading functions
try:
    from ollama_warmup_service import memory_ok, is_model_loaded, unload_model, load_model
    print("\n✅ Adaptive loading functions imported successfully")
    print(f"   Memory OK: {memory_ok()}")
except Exception as e:
    print(f"\n❌ Error importing adaptive loading functions: {e}")

print("\nTest completed.")
