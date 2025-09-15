"""
Test imports for Merge Agent
"""

import sys
import os

print("Python path:")
for path in sys.path:
    print(f"  {path}")

print(f"\nCurrent working directory: {os.getcwd()}")

# Try different import approaches
print("\nTrying imports...")

try:
    # Try direct import
    from backend.distributed.merge import MergeAgent
    print("✓ Direct import successful")
except Exception as e:
    print(f"✗ Direct import failed: {e}")

try:
    # Try relative import
    sys.path.insert(0, 'backend')
    from distributed.merge import MergeAgent
    print("✓ Relative import successful")
except Exception as e:
    print(f"✗ Relative import failed: {e}")

try:
    # Check if file exists
    import os
    merge_file = os.path.join('backend', 'distributed', 'merge.py')
    if os.path.exists(merge_file):
        print(f"✓ Merge file exists at: {merge_file}")
    else:
        print(f"✗ Merge file not found at: {merge_file}")
except Exception as e:
    print(f"✗ Error checking file: {e}")
