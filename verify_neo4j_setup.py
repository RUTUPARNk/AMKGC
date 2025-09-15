"""
Verify Neo4j setup and dependencies
"""

import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
if backend_path not in sys.path:
    sys.path.append(backend_path)

print("=" * 50)
print("Neo4j Setup Verification")
print("=" * 50)

# Check Python version
print(f"Python version: {sys.version}")

# Check if we can import required modules
required_modules = [
    'neo4j',
    'config.neo4j',
    'services.neo4j_service'
]

import_success = True

for module in required_modules:
    try:
        if module == 'neo4j':
            import neo4j
            print(f"✓ {module} - Version: {neo4j.__version__}")
        elif module == 'config.neo4j':
            from config import neo4j
            print(f"✓ {module} - Successfully imported")
        elif module == 'services.neo4j_service':
            from services import neo4j_service
            print(f"✓ {module} - Successfully imported")
    except ImportError as e:
        print(f"✗ {module} - Import failed: {e}")
        import_success = False

print("\n" + "=" * 50)

if import_success:
    print("✓ All required modules imported successfully!")
    print("\nThe Neo4j integration code is properly structured.")
    print("Next steps:")
    print("1. Set up a running Neo4j instance (see NEO4J_SETUP_GUIDE.md)")
    print("2. Run the comprehensive test: python test_neo4j_comprehensive.py")
else:
    print("✗ Some modules failed to import.")
    print("Please check your Python environment and dependencies.")

print("\nFor detailed setup instructions, see NEO4J_SETUP_GUIDE.md")
