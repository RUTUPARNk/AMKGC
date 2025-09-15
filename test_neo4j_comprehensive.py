"""
Comprehensive test for Neo4j integration with multiple connection options
"""

import os
import sys
from typing import List, Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from neo4j import GraphDatabase
    from config.neo4j import neo4j_settings
    print("✓ Neo4j dependencies imported successfully")
except ImportError as e:
    print(f"⚠ Warning: Could not import Neo4j dependencies: {e}")
    print("Please install neo4j package: pip install neo4j")
    sys.exit(1)


def test_connection(uri: str, user: str, password: str, description: str) -> bool:
    """Test a Neo4j connection with detailed feedback"""
    print(f"\nTesting {description}...")
    print(f"  URI: {uri}")
    print(f"  User: {user}")
    
    try:
        # Test connection
        driver = GraphDatabase.driver(uri, auth=(user, password))
        print("  ✓ Driver created successfully")
        
        # Test connectivity
        driver.verify_connectivity()
        print("  ✓ Connectivity verified")
        
        # Test a simple query
        with driver.session() as session:
            result = session.run("RETURN 'Hello, Neo4j!' AS message")
            record = result.single()
            print(f"  ✓ Query test: {record['message']}")
        
        # Close driver
        driver.close()
        print("  ✓ Connection test passed")
        return True
        
    except Exception as e:
        print(f"  ✗ Connection test failed: {e}")
        return False


def main():
    """Main test function"""
    print("=" * 50)
    print("Neo4j Comprehensive Connection Test")
    print("=" * 50)
    
    # Test configurations
    test_configs = [
        {
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "password",
            "description": "Default local connection"
        },
        {
            "uri": neo4j_settings.NEO4J_URI,
            "user": neo4j_settings.NEO4J_USER,
            "password": neo4j_settings.NEO4J_PASSWORD,
            "description": "Environment-based connection"
        }
    ]
    
    # Add any custom connections from environment variables
    custom_uri = os.getenv("CUSTOM_NEO4J_URI")
    if custom_uri:
        test_configs.append({
            "uri": custom_uri,
            "user": os.getenv("CUSTOM_NEO4J_USER", "neo4j"),
            "password": os.getenv("CUSTOM_NEO4J_PASSWORD", "password"),
            "description": "Custom environment connection"
        })
    
    # Test each configuration
    successful_connections = 0
    for config in test_configs:
        if test_connection(**config):
            successful_connections += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    print(f"Successful connections: {successful_connections}/{len(test_configs)}")
    
    if successful_connections > 0:
        print("\n✓ At least one connection is working!")
        print("\nNext steps:")
        print("1. Run the migration script to transfer data:")
        print("   python backend/scripts/migrate_to_neo4j.py")
        print("2. Test the full integration:")
        print("   python test_neo4j_integration.py")
    else:
        print("\n✗ No connections are working.")
        print("\nPlease check the Neo4j Setup Guide (NEO4J_SETUP_GUIDE.md) for help.")
        
    print("\nFor detailed setup instructions, see NEO4J_SETUP_GUIDE.md")


if __name__ == "__main__":
    main()
