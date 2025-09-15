"""
Migration script to move data from PostgreSQL to Neo4j
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.database import DATABASE_URL
from models.node import Node as SQLNode
from services.neo4j_service import Neo4jService
from config.neo4j import neo4j_settings


def migrate_nodes():
    """Migrate all nodes from PostgreSQL to Neo4j"""
    
    # Connect to PostgreSQL
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Connect to Neo4j
    neo4j_service = Neo4jService(
        neo4j_settings.NEO4J_URI,
        neo4j_settings.NEO4J_USER,
        neo4j_settings.NEO4J_PASSWORD
    )
    
    try:
        # Get all nodes from PostgreSQL
        sql_nodes = db.query(SQLNode).all()
        print(f"Found {len(sql_nodes)} nodes to migrate")
        
        # Migrate each node
        for sql_node in sql_nodes:
            success = neo4j_service.create_node(
                node_id=str(sql_node.id),
                name=sql_node.name,
                node_type=sql_node.node_type,
                context_window=sql_node.context_window,
                status=sql_node.status,
                llm_model_used=sql_node.llm_model_used or "ollama",
                created_at=sql_node.created_at.isoformat() if sql_node.created_at else None,
                updated_at=sql_node.updated_at.isoformat() if sql_node.updated_at else None
            )
            
            if success:
                print(f"Migrated node {sql_node.id}")
            else:
                print(f"Failed to migrate node {sql_node.id}")
        
        # Create parent-child relationships
        for sql_node in sql_nodes:
            if sql_node.parent_node:
                success = neo4j_service.create_edge(
                    source_id=str(sql_node.parent_node),
                    target_id=str(sql_node.id),
                    relationship_type="PARENT_CHILD"
                )
                if success:
                    print(f"Created parent-child relationship: {sql_node.parent_node} -> {sql_node.id}")
                else:
                    print(f"Failed to create parent-child relationship: {sql_node.parent_node} -> {sql_node.id}")
        
        print("Migration completed successfully")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        raise
    
    finally:
        db.close()
        neo4j_service.close()


def create_indexes_and_constraints():
    """Create indexes and constraints in Neo4j"""
    neo4j_service = Neo4jService(
        neo4j_settings.NEO4J_URI,
        neo4j_settings.NEO4J_USER,
        neo4j_settings.NEO4J_PASSWORD
    )
    
    try:
        with neo4j_service.driver.session() as session:
            # Create indexes
            indexes = [
                "CREATE INDEX node_id FOR (n:Node) ON (n.id)",
                "CREATE INDEX node_name FOR (n:Node) ON (n.name)",
                "CREATE INDEX node_status FOR (n:Node) ON (n.status)",
                "CREATE INDEX node_created FOR (n:Node) ON (n.created_at)",
                "CREATE INDEX node_updated FOR (n:Node) ON (n.updated_at)",
                "CREATE INDEX node_type FOR (n:Node) ON (n.type)",
                "CREATE INDEX version_node_id FOR (v:VersionSnapshot) ON (v.node_id)",
                "CREATE INDEX version_number FOR (v:VersionSnapshot) ON (v.version_number)",
                "CREATE INDEX merge_source FOR (m:MergeRequest) ON (m.source_node_id)",
                "CREATE INDEX merge_target FOR (m:MergeRequest) ON (m.target_node_id)",
                "CREATE INDEX merge_status FOR (m:MergeRequest) ON (m.status)"
            ]
            
            for index_query in indexes:
                try:
                    session.run(index_query)
                    print(f"Created index: {index_query}")
                except Exception as e:
                    print(f"Index creation failed (may already exist): {index_query} - {e}")
            
            # Create constraints
            constraints = [
                "CREATE CONSTRAINT node_id_unique FOR (n:Node) REQUIRE n.id IS UNIQUE",
                "CREATE CONSTRAINT version_id_unique FOR (v:VersionSnapshot) REQUIRE v.id IS UNIQUE",
                "CREATE CONSTRAINT merge_id_unique FOR (m:MergeRequest) REQUIRE m.id IS UNIQUE"
            ]
            
            for constraint_query in constraints:
                try:
                    session.run(constraint_query)
                    print(f"Created constraint: {constraint_query}")
                except Exception as e:
                    print(f"Constraint creation failed (may already exist): {constraint_query} - {e}")
                    
        print("Indexes and constraints setup completed")
        
    except Exception as e:
        print(f"Indexes and constraints setup failed: {e}")
        raise
    
    finally:
        neo4j_service.close()


def main():
    """Main migration function"""
    print("Starting migration from PostgreSQL to Neo4j...")
    
    # Create indexes and constraints first
    print("Setting up indexes and constraints...")
    create_indexes_and_constraints()
    
    # Migrate nodes
    print("Migrating nodes...")
    migrate_nodes()
    
    print("Migration completed!")


if __name__ == "__main__":
    main()
