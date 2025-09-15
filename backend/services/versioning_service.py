from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from services.neo4j_service import Neo4jService
from config.neo4j import neo4j_settings

logger = logging.getLogger(__name__)

class VersioningService:
    def __init__(self):
        """Initialize VersioningService with Neo4j connection"""
        try:
            self.neo4j_service = Neo4jService(
                neo4j_settings.NEO4J_URI,
                neo4j_settings.NEO4J_USER,
                neo4j_settings.NEO4J_PASSWORD
            )
            logger.info("Neo4j connection established for VersioningService")
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}")
            self.neo4j_service = None
    
    def create_version_snapshot(self, node_id: str, context_window: str, 
                               version_number: int) -> bool:
        """Create a version snapshot of a node in Neo4j"""
        if not self.neo4j_service:
            logger.warning("Neo4j service not available for versioning")
            return False
        
        try:
            return self.neo4j_service.create_version_snapshot(
                node_id, version_number, context_window
            )
        except Exception as e:
            logger.error(f"Error creating version snapshot for {node_id}: {e}")
            return False
    
    def get_version_snapshots(self, node_id: str) -> List[Dict[str, Any]]:
        """Get all version snapshots for a node"""
        if not self.neo4j_service:
            logger.warning("Neo4j service not available for versioning")
            return []
        
        try:
            return self.neo4j_service.get_version_snapshots(node_id)
        except Exception as e:
            logger.error(f"Error getting version snapshots for {node_id}: {e}")
            return []
    
    def mark_node_stale(self, node_id: str) -> bool:
        """Mark a node as stale in Neo4j"""
        if not self.neo4j_service:
            logger.warning("Neo4j service not available for versioning")
            return False
        
        try:
            return self.neo4j_service.mark_node_stale(node_id)
        except Exception as e:
            logger.error(f"Error marking node {node_id} as stale: {e}")
            return False
    
    def get_stale_nodes(self, days_threshold: int = 7) -> List[Dict[str, Any]]:
        """Get all nodes that are stale based on threshold"""
        if not self.neo4j_service:
            logger.warning("Neo4j service not available for versioning")
            return []
        
        try:
            return self.neo4j_service.get_stale_nodes(days_threshold)
        except Exception as e:
            logger.error(f"Error getting stale nodes: {e}")
            return []
    
    def propagate_staleness(self, node_id: str) -> bool:
        """Propagate staleness to dependent nodes in Neo4j"""
        if not self.neo4j_service:
            logger.warning("Neo4j service not available for versioning")
            return False
        
        try:
            return self.neo4j_service.propagate_staleness(node_id)
        except Exception as e:
            logger.error(f"Error propagating staleness from {node_id}: {e}")
            return False
    
    def close(self):
        """Close Neo4j connection"""
        if self.neo4j_service:
            self.neo4j_service.close()
