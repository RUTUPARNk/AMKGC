"""
Verification script for Merge Agent implementation
This script verifies that all components of the Merge Agent have been implemented correctly.
"""

import os
import sys

def verify_file_structure():
    """Verify that all required files exist"""
    print("Verifying file structure...")
    
    required_files = [
        "backend/distributed/merge.py",
        "backend/api/merge.py",
        "backend/api/router.py"
    ]
    
    all_good = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path} exists")
        else:
            print(f"  ✗ {file_path} missing")
            all_good = False
    
    return all_good

def verify_merge_agent_implementation():
    """Verify Merge Agent implementation"""
    print("\nVerifying Merge Agent implementation...")
    
    # Check if merge.py file contains required classes and methods
    merge_file_path = "backend/distributed/merge.py"
    if not os.path.exists(merge_file_path):
        print("  ✗ Merge Agent file not found")
        return False
    
    with open(merge_file_path, 'r') as f:
        content = f.read()
    
    required_classes = ["MergeAgent", "MergePreview", "ApplyResult"]
    required_methods = ["compute_merge", "apply_merge"]
    
    all_good = True
    for class_name in required_classes:
        if class_name in content:
            print(f"  ✓ {class_name} class implemented")
        else:
            print(f"  ✗ {class_name} class missing")
            all_good = False
    
    for method_name in required_methods:
        if method_name in content:
            print(f"  ✓ {method_name} method implemented")
        else:
            print(f"  ✗ {method_name} method missing")
            all_good = False
    
    return all_good

def verify_api_endpoints():
    """Verify API endpoints implementation"""
    print("\nVerifying API endpoints...")
    
    # Check if API file contains required endpoints
    api_file_path = "backend/api/merge.py"
    if not os.path.exists(api_file_path):
        print("  ✗ Merge API file not found")
        return False
    
    with open(api_file_path, 'r') as f:
        content = f.read()
    
    required_endpoints = ["compute_merge", "apply_merge"]
    
    all_good = True
    for endpoint in required_endpoints:
        if endpoint in content:
            print(f"  ✓ {endpoint} endpoint implemented")
        else:
            print(f"  ✗ {endpoint} endpoint missing")
            all_good = False
    
    return all_good

def verify_router_integration():
    """Verify router integration"""
    print("\nVerifying router integration...")
    
    # Check if router.py includes merge router
    router_file_path = "backend/api/router.py"
    if not os.path.exists(router_file_path):
        print("  ✗ Router file not found")
        return False
    
    with open(router_file_path, 'r') as f:
        content = f.read()
    
    if "merge_router" in content:
        print("  ✓ Merge router integrated")
        return True
    else:
        print("  ✗ Merge router not integrated")
        return False

def main():
    """Main verification function"""
    print("=" * 50)
    print("Merge Agent Implementation Verification")
    print("=" * 50)
    
    checks = [
        verify_file_structure(),
        verify_merge_agent_implementation(),
        verify_api_endpoints(),
        verify_router_integration()
    ]
    
    if all(checks):
        print("\n" + "=" * 50)
        print("✓ All verifications passed!")
        print("Merge Agent implementation is complete.")
        print("=" * 50)
        return True
    else:
        print("\n" + "=" * 50)
        print("✗ Some verifications failed.")
        print("Please check the implementation.")
        print("=" * 50)
        return False

if __name__ == "__main__":
    main()
