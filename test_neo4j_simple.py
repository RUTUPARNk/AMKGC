"""
Simple test for Neo4j integration
"""

try:
    from neo4j import GraphDatabase
    print("✓ Neo4j driver imported successfully")
    
    # Test connection
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    print("✓ Neo4j driver created successfully")
    
    # Test connectivity
    driver.verify_connectivity()
    print("✓ Neo4j connectivity verified")
    
    # Test a simple query
    with driver.session() as session:
        result = session.run("RETURN 'Hello, Neo4j!' AS message")
        record = result.single()
        print(f"✓ Neo4j query test: {record['message']}")
    
    # Close driver
    driver.close()
    print("✓ Neo4j driver closed successfully")
    
    print("\nAll Neo4j tests passed!")
    
except Exception as e:
    print(f"✗ Neo4j test failed: {e}")
    print("\nThis might be because:")
    print("1. Neo4j is not running locally")
    print("2. Docker is not installed or running")
    print("3. Connection parameters are incorrect")
    print("\nTo run Neo4j locally, you can:")
    print("1. Install Docker and run: docker-compose -f docker-compose-neo4j.yaml up -d")
    print("2. Download and install Neo4j Desktop from https://neo4j.com/download/")
    print("3. Use a remote Neo4j instance by updating the connection parameters")
