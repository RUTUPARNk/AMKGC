from neo4j import GraphDatabase
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class Neo4jService:
    def __init__(self, uri: str, user: str, password: str):
        """Initialize Neo4j driver"""
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            logger.info("Connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close Neo4j driver connection"""
        if self.driver:
            self.driver.close()
    
    def create_node(self, node_id: str, name: str, node_type: str, 
                   context_window: str, status: str = "active", 
                   llm_model_used: str = "ollama", **properties) -> bool:
        """Create a node in Neo4j"""
        try:
            with self.driver.session() as session:
                query = """
                MERGE (n:Node {id: $node_id})
                SET n.name = $name,
                    n.type = $node_type,
                    n.context_window = $context_window,
                    n.status = $status,
                    n.llm_model_used = $llm_model_used,
                    n.created_at = CASE WHEN n.created_at IS NULL THEN datetime() ELSE n.created_at END,
                    n.updated_at = datetime()
                """
                
                # Add any additional properties
                for key, value in properties.items():
                    query += f"\nSET n.{key} = ${key}"
                
                params = {
                    "node_id": node_id,
                    "name": name,
                    "node_type": node_type,
                    "context_window": context_window,
                    "status": status,
                    "llm_model_used": llm_model_used,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    **properties
                }
                
                session.run(query, params)
                return True
        except Exception as e:
            logger.error(f"Error creating node {node_id}: {e}")
            return False
    
    def create_edge(self, source_id: str, target_id: str, relationship_type: str, 
                   **properties) -> bool:
        """Create a relationship between two nodes"""
        try:
            with self.driver.session() as session:
                query = f"""
                MATCH (a:Node {{id: $source_id}}), (b:Node {{id: $target_id}})
                MERGE (a)-[r:{relationship_type}]->(b)
                """
                
                # Add any additional properties
                for key, value in properties.items():
                    query += f"\nSET r.{key} = ${key}"
                
                params = {
                    "source_id": source_id,
                    "target_id": target_id,
                    "updated_at": datetime.now().isoformat(),
                    **properties
                }
                
                session.run(query, params)
                return True
        except Exception as e:
            logger.error(f"Error creating edge from {source_id} to {target_id}: {e}")
            return False
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node by ID"""
        try:
            with self.driver.session() as session:
                query = "MATCH (n:Node {id: $node_id}) RETURN n"
                result = session.run(query, {"node_id": node_id})
                record = result.single()
                if record:
                    node = dict(record["n"])
                    return node
                return None
        except Exception as e:
            logger.error(f"Error getting node {node_id}: {e}")
            return None
    
    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """Get all nodes"""
        try:
            with self.driver.session() as session:
                query = "MATCH (n:Node) RETURN n ORDER BY n.created_at DESC"
                result = session.run(query)
                nodes = []
                for record in result:
                    node = dict(record["n"])
                    nodes.append(node)
                return nodes
        except Exception as e:
            logger.error(f"Error getting all nodes: {e}")
            return []
    
    def get_child_nodes(self, parent_id: str) -> List[Dict[str, Any]]:
        """Get all child nodes of a parent node"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (parent:Node {id: $parent_id})-[:PARENT_CHILD]->(child:Node)
                RETURN child
                ORDER BY child.created_at DESC
                """
                result = session.run(query, {"parent_id": parent_id})
                nodes = []
                for record in result:
                    node = dict(record["child"])
                    nodes.append(node)
                return nodes
        except Exception as e:
            logger.error(f"Error getting child nodes for {parent_id}: {e}")
            return []
    
    def get_parent_node(self, child_id: str) -> Optional[Dict[str, Any]]:
        """Get parent node of a child node"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (parent:Node)-[:PARENT_CHILD]->(child:Node {id: $child_id})
                RETURN parent
                """
                result = session.run(query, {"child_id": child_id})
                record = result.single()
                if record:
                    return dict(record["parent"])
                return None
        except Exception as e:
            logger.error(f"Error getting parent node for {child_id}: {e}")
            return None
    
    def update_node_context(self, node_id: str, new_context: str) -> bool:
        """Update node's context window"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (n:Node {id: $node_id})
                SET n.context_window = $new_context,
                    n.updated_at = datetime()
                """
                session.run(query, {
                    "node_id": node_id,
                    "new_context": new_context,
                    "updated_at": datetime.now().isoformat()
                })
                return True
        except Exception as e:
            logger.error(f"Error updating node context {node_id}: {e}")
            return False
    
    def delete_node(self, node_id: str) -> bool:
        """Delete a node and all its relationships"""
        try:
            with self.driver.session() as session:
                query = "MATCH (n:Node {id: $node_id}) DETACH DELETE n"
                session.run(query, {"node_id": node_id})
                return True
        except Exception as e:
            logger.error(f"Error deleting node {node_id}: {e}")
            return False
    
    def create_version_snapshot(self, node_id: str, version_number: int, 
                               context_window: str) -> bool:
        """Create a version snapshot of a node"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (n:Node {id: $node_id})
                CREATE (v:VersionSnapshot {
                    version_number: $version_number,
                    context_window: $context_window,
                    created_at: datetime()
                })
                CREATE (n)-[:HAS_VERSION]->(v)
                """
                session.run(query, {
                    "node_id": node_id,
                    "version_number": version_number,
                    "context_window": context_window
                })
                return True
        except Exception as e:
            logger.error(f"Error creating version snapshot for {node_id}: {e}")
            return False
    
    def get_version_snapshots(self, node_id: str) -> List[Dict[str, Any]]:
        """Get all version snapshots for a node"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (n:Node {id: $node_id})-[:HAS_VERSION]->(v:VersionSnapshot)
                RETURN v
                ORDER BY v.version_number DESC
                """
                result = session.run(query, {"node_id": node_id})
                versions = []
                for record in result:
                    version = dict(record["v"])
                    versions.append(version)
                return versions
        except Exception as e:
            logger.error(f"Error getting version snapshots for {node_id}: {e}")
            return []
    
    def mark_node_stale(self, node_id: str) -> bool:
        """Mark a node as stale"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (n:Node {id: $node_id})
                SET n.status = 'stale',
                    n.stale_at = datetime()
                """
                session.run(query, {
                    "node_id": node_id,
                    "stale_at": datetime.now().isoformat()
                })
                return True
        except Exception as e:
            logger.error(f"Error marking node {node_id} as stale: {e}")
            return False
    
    def get_stale_nodes(self, days_threshold: int = 7) -> List[Dict[str, Any]]:
        """Get all nodes that are stale based on threshold"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (n:Node)
                WHERE n.status = 'stale' 
                AND n.stale_at < datetime() - duration({days: $days_threshold})
                RETURN n
                """
                result = session.run(query, {"days_threshold": days_threshold})
                nodes = []
                for record in result:
                    node = dict(record["n"])
                    nodes.append(node)
                return nodes
        except Exception as e:
            logger.error(f"Error getting stale nodes: {e}")
            return []
    
    def propagate_staleness(self, node_id: str) -> bool:
        """Propagate staleness to dependent nodes"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (n:Node {id: $node_id})-[:DEPENDS_ON*]->(dependent:Node)
                WHERE dependent.status <> 'stale'
                SET dependent.status = 'stale',
                    dependent.stale_at = datetime()
                """
                session.run(query, {"node_id": node_id})
                return True
        except Exception as e:
            logger.error(f"Error propagating staleness from {node_id}: {e}")
            return False
