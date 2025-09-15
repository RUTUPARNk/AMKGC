from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Any, Optional, Tuple
import json
import uuid
import redis
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import heapq
from dataclasses import dataclass, field
from enum import Enum

from models.node import Node
from services.ollama_service import OllamaService
from services.neo4j_service import Neo4jService
from config.neo4j import neo4j_settings
from api.events import session_created, session_updated, session_deleted

logger = logging.getLogger(__name__)

class ConflictPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class ConflictItem:
    priority: ConflictPriority
    conflict_id: str
    node1_id: str
    node2_id: str
    conflict_type: str
    description: str
    created_at: datetime
    user_feedback: Optional[str] = None
    
    def __lt__(self, other):
        return self.priority.value < other.priority.value

class NodeService:
    def __init__(self, db_session: Session, ollama_service: OllamaService, 
                 redis_url: str = "redis://localhost:6379"):
        self.db = db_session
        self.ollama = ollama_service
        
        # Initialize Redis connection
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Redis connection established for NodeService")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None
        
        # Initialize Neo4j connection
        try:
            self.neo4j_service = Neo4jService(
                neo4j_settings.NEO4J_URI,
                neo4j_settings.NEO4J_USER,
                neo4j_settings.NEO4J_PASSWORD
            )
            logger.info("Neo4j connection established for NodeService")
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}")
            self.neo4j_service = None
        
        # Priority queue for conflicts
        self.conflict_queue = []
        self.conflict_cache = {}
        
        # Cache TTL settings
        self.cache_ttl = {
            'node_context': 1800,  # 30 minutes
            'graph_data': 300,     # 5 minutes
            'search_results': 600,  # 10 minutes
            'conflict_data': 900   # 15 minutes
        }
    
    def _get_cache_key(self, prefix: str, identifier: str) -> str:
        """Generate cache key"""
        return f"node:{prefix}:{identifier}"
    
    def _cache_get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache"""
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None
    
    def _cache_set(self, key: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Set data in cache with TTL"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.setex(key, ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def _invalidate_cache(self, pattern: str) -> bool:
        """Invalidate cache entries matching pattern"""
        if not self.redis_client:
            return False
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries for pattern: {pattern}")
            return True
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return False
    
    def create_node(self, name: str, context_window: str, node_type: str = "general", 
                   parent_node_id: Optional[str] = None, llm_model: str = "ollama",
                   created_by: Optional[str] = None) -> Node:
        """
        Create a new node with enhanced validation and caching
        """
        try:
            # Validate input
            if not name or not name.strip():
                raise ValueError("Node name cannot be empty")
            
            if len(name) > 255:
                raise ValueError("Node name too long (max 255 characters)")
            
            # Sanitize context_window to prevent XSS
            context_window = self._sanitize_input(context_window)
            
            node = Node(
                name=name.strip(),
                context_window=context_window,
                node_type=node_type,
                parent_node=uuid.UUID(parent_node_id) if parent_node_id else None,
                llm_model_used=llm_model
            )
            
            self.db.add(node)
            self.db.commit()
            self.db.refresh(node)
            
            # Update parent's child_nodes if parent exists
            if parent_node_id:
                parent = self.get_node_by_id(parent_node_id)
                if parent:
                    parent.add_child_node(str(node.id))
                    self.db.commit()
            
            # Create node in Neo4j if service is available
            if self.neo4j_service:
                try:
                    self.neo4j_service.create_node(
                        node_id=str(node.id),
                        name=node.name,
                        node_type=node.node_type,
                        context_window=node.context_window,
                        status=node.status,
                        llm_model_used=node.llm_model_used or "ollama"
                    )
                    
                    # Create parent-child relationship in Neo4j
                    if parent_node_id:
                        self.neo4j_service.create_edge(
                            source_id=parent_node_id,
                            target_id=str(node.id),
                            relationship_type="PARENT_CHILD"
                        )
                    
                    logger.info(f"Created Neo4j node: {node.id} ({node.name})")
                except Exception as e:
                    logger.error(f"Failed to create Neo4j node {node.id}: {e}")
            
            # Invalidate related caches
            self._invalidate_cache("node:graph:*")
            self._invalidate_cache("node:search:*")
            
            # Cache the new node
            self._cache_node_data(node)
            
            logger.info(f"Created node: {node.id} ({node.name})")
            
            # Broadcast session created event
            session_data = {
                "session_id": str(node.id),
                "title": node.name,
                "status": "pending",
                "created_at": node.created_at.isoformat() if node.created_at else None
            }
            session_created(session_data)
            
            return node
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating node: {e}")
            raise
    
    def get_node_by_id(self, node_id: str) -> Optional[Node]:
        """
        Get node by ID with caching
        """
        # Check cache first
        cache_key = self._get_cache_key("node", node_id)
        cached_node = self._cache_get(cache_key)
        if cached_node:
            return Node(**cached_node)
        
        try:
            node = self.db.query(Node).filter(Node.id == uuid.UUID(node_id)).first()
            if node:
                # Cache the node data
                self._cache_node_data(node)
            return node
        except Exception as e:
            logger.error(f"Error getting node {node_id}: {e}")
            return None
    
    def _cache_node_data(self, node: Node) -> bool:
        """Cache node data"""
        cache_key = self._get_cache_key("node", str(node.id))
        return self._cache_set(cache_key, node.to_dict(), self.cache_ttl['node_context'])
    
    def get_all_nodes(self) -> List[Node]:
        """
        Get all nodes with caching
        """
        cache_key = self._get_cache_key("all_nodes", "list")
        cached_nodes = self._cache_get(cache_key)
        if cached_nodes:
            return [Node(**node_data) for node_data in cached_nodes]
        
        try:
            nodes = self.db.query(Node).all()
            # Cache the nodes list
            if self.redis_client:
                node_data_list = [node.to_dict() for node in nodes]
                self._cache_set(cache_key, node_data_list, self.cache_ttl['node_context'])
            return nodes
        except Exception as e:
            logger.error(f"Error getting all nodes: {e}")
            return []
    
    def get_nodes_by_type(self, node_type: str) -> List[Node]:
        """
        Get nodes by type with caching
        """
        cache_key = self._get_cache_key("nodes_by_type", node_type)
        cached_nodes = self._cache_get(cache_key)
        if cached_nodes:
            return [Node(**node_data) for node_data in cached_nodes]
        
        try:
            nodes = self.db.query(Node).filter(Node.node_type == node_type).all()
            # Cache the filtered nodes
            if self.redis_client:
                node_data_list = [node.to_dict() for node in nodes]
                self._cache_set(cache_key, node_data_list, self.cache_ttl['node_context'])
            return nodes
        except Exception as e:
            logger.error(f"Error getting nodes by type {node_type}: {e}")
            return []
    
    def get_child_nodes(self, parent_id: str) -> List[Node]:
        """
        Get all child nodes of a parent with caching
        """
        cache_key = self._get_cache_key("child_nodes", parent_id)
        cached_nodes = self._cache_get(cache_key)
        if cached_nodes:
            return [Node(**node_data) for node_data in cached_nodes]
        
        try:
            nodes = self.db.query(Node).filter(Node.parent_node == uuid.UUID(parent_id)).all()
            # Cache the child nodes
            if self.redis_client:
                node_data_list = [node.to_dict() for node in nodes]
                self._cache_set(cache_key, node_data_list, self.cache_ttl['node_context'])
            return nodes
        except Exception as e:
            logger.error(f"Error getting child nodes for {parent_id}: {e}")
            return []
    
    def get_parent_node(self, child_id: str) -> Optional[Node]:
        """
        Get parent node of a child
        """
        child = self.get_node_by_id(child_id)
        if child and child.parent_node:
            return self.get_node_by_id(str(child.parent_node))
        return None
    
    def update_node_context(self, node_id: str, new_context: str, 
                           updated_by: Optional[str] = None) -> Optional[Node]:
        """
        Update node's context window with validation and caching
        """
        try:
            # Sanitize input
            new_context = self._sanitize_input(new_context)
            
            node = self.get_node_by_id(node_id)
            if node:
                node.context_window = new_context
                node.updated_at = datetime.now()
                self.db.commit()
                self.db.refresh(node)
                
                # Update node in Neo4j if service is available
                if self.neo4j_service:
                    try:
                        self.neo4j_service.update_node_context(node_id, new_context)
                        logger.info(f"Updated Neo4j node context: {node_id}")
                    except Exception as e:
                        logger.error(f"Failed to update Neo4j node context {node_id}: {e}")
                
                # Invalidate caches
                self._invalidate_cache(f"node:node:{node_id}")
                self._invalidate_cache("node:graph:*")
                
                # Update cache
                self._cache_node_data(node)
                
                logger.info(f"Updated node context: {node_id}")
                
                # Broadcast session updated event
                session_data = {
                    "session_id": str(node.id),
                    "title": node.name,
                    "status": "active" if node.status else "pending",
                    "created_at": node.created_at.isoformat() if node.created_at else None
                }
                session_updated(session_data)
                
                return node
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating node {node_id}: {e}")
        return None
    
    def delete_node(self, node_id: str) -> bool:
        """
        Delete a node and its children with cache invalidation
        """
        try:
            node = self.get_node_by_id(node_id)
            if node:
                # Remove from parent's child_nodes
                if node.parent_node:
                    parent = self.get_node_by_id(str(node.parent_node))
                    if parent:
                        parent.remove_child_node(str(node.id))
                        self.db.commit()
                
                # Delete all child nodes
                children = self.get_child_nodes(node_id)
                for child in children:
                    self.db.delete(child)
                
                self.db.delete(node)
                self.db.commit()
                
                # Delete node from Neo4j if service is available
                if self.neo4j_service:
                    try:
                        self.neo4j_service.delete_node(node_id)
                        logger.info(f"Deleted Neo4j node: {node_id}")
                    except Exception as e:
                        logger.error(f"Failed to delete Neo4j node {node_id}: {e}")
                
                # Invalidate all related caches
                self._invalidate_cache("node:*")
                self._invalidate_cache("node:graph:*")
                self._invalidate_cache("node:search:*")
                
                logger.info(f"Deleted node: {node_id}")
                
                # Broadcast session deleted event
                session_deleted({"session_id": node_id})
                
                return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting node {node_id}: {e}")
        return False
    
    def generate_node_context(self, node_id: str, prompt: str) -> Optional[Node]:
        """
        Generate context for a node using LLM with enhanced error handling
        """
        node = self.get_node_by_id(node_id)
        if not node:
            return None
        
        try:
            response = self.ollama.generate(prompt)
            node.context_window = response["text"]
            node.llm_model_used = response["model"]
            node.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(node)
            
            # Update cache
            self._cache_node_data(node)
            
            logger.info(f"Generated context for node: {node_id}")
            return node
        except Exception as e:
            logger.error(f"Error generating context for node {node_id}: {e}")
            return node
    
    def generate_schema_node(self, table_name: str, description: str, 
                           parent_id: Optional[str] = None) -> Node:
        """
        Generate a schema node using LLM
        """
        try:
            schema_data = self.ollama.generate_schema(table_name, description)
            context_window = json.dumps(schema_data, indent=2)
            
            node = self.create_node(
                name=f"{table_name}_Schema",
                context_window=context_window,
                node_type="schema",
                parent_node_id=parent_id
            )
            
            logger.info(f"Generated schema node: {node.id}")
            return node
        except Exception as e:
            logger.error(f"Error generating schema node: {e}")
            raise
    
    def generate_policy_node(self, policy_name: str, description: str, 
                           parent_id: Optional[str] = None) -> Node:
        """
        Generate a policy node using LLM
        """
        try:
            policy_data = self.ollama.generate_policy(policy_name, description)
            context_window = json.dumps(policy_data, indent=2)
            
            node = self.create_node(
                name=f"{policy_name}_Policy",
                context_window=context_window,
                node_type="policy",
                parent_node_id=parent_id
            )
            
            logger.info(f"Generated policy node: {node.id}")
            return node
        except Exception as e:
            logger.error(f"Error generating policy node: {e}")
            raise
    
    def detect_node_conflicts(self, node1_id: str, node2_id: str) -> Dict[str, Any]:
        """
        Detect conflicts between two nodes with priority assessment
        """
        node1 = self.get_node_by_id(node1_id)
        node2 = self.get_node_by_id(node2_id)
        
        if not node1 or not node2:
            return {"has_conflicts": False, "error": "One or both nodes not found"}
        
        try:
            conflict_analysis = self.ollama.detect_conflicts(
                node1.context_window,
                node2.context_window
            )
            
            # Mark nodes as conflicting if conflicts detected
            if conflict_analysis.get("has_conflicts", False):
                node1.mark_as_conflicting()
                node2.mark_as_conflicting()
                self.db.commit()
                
                # Add to priority queue
                self._add_conflict_to_queue(node1_id, node2_id, conflict_analysis)
                
                # Cache conflict data
                conflict_key = f"{node1_id}:{node2_id}"
                self._cache_set(
                    self._get_cache_key("conflict", conflict_key),
                    conflict_analysis,
                    self.cache_ttl['conflict_data']
                )
            
            return conflict_analysis
        except Exception as e:
            logger.error(f"Error detecting conflicts: {e}")
            return {"has_conflicts": False, "error": str(e)}
    
    def _add_conflict_to_queue(self, node1_id: str, node2_id: str, 
                              conflict_analysis: Dict[str, Any]):
        """Add conflict to priority queue"""
        try:
            priority_str = conflict_analysis.get("priority", "medium")
            priority = ConflictPriority[priority_str.upper()]
            
            conflict_item = ConflictItem(
                priority=priority,
                conflict_id=f"{node1_id}:{node2_id}",
                node1_id=node1_id,
                node2_id=node2_id,
                conflict_type=conflict_analysis.get("conflict_type", "unknown"),
                description=conflict_analysis.get("conflicts", [{}])[0].get("description", ""),
                created_at=datetime.now()
            )
            
            heapq.heappush(self.conflict_queue, conflict_item)
            self.conflict_cache[conflict_item.conflict_id] = conflict_item
            
            logger.info(f"Added conflict to queue: {conflict_item.conflict_id} (priority: {priority_str})")
        except Exception as e:
            logger.error(f"Error adding conflict to queue: {e}")
    
    def get_next_conflict(self) -> Optional[ConflictItem]:
        """Get next conflict from priority queue"""
        if self.conflict_queue:
            return heapq.heappop(self.conflict_queue)
        return None
    
    def create_conflict_resolution_node(self, node1_id: str, node2_id: str, 
                                     conflict_description: str,
                                     user_feedback: Optional[str] = None) -> Node:
        """
        Create a child node for conflict resolution with user feedback
        """
        node1 = self.get_node_by_id(node1_id)
        node2 = self.get_node_by_id(node2_id)
        
        if not node1 or not node2:
            raise ValueError("One or both nodes not found")
        
        try:
            # Create resolution prompt with user feedback
            feedback_context = f"\nUser Feedback: {user_feedback}" if user_feedback else ""
            
            resolution_prompt = f"""
            The following nodes suggest conflicting information. Please clarify:
            
            Node 1 ({node1.name}):
            {node1.context_window}
            
            Node 2 ({node2.name}):
            {node2.context_window}
            
            Conflict: {conflict_description}{feedback_context}
            
            Please provide a resolution that combines or corrects the conflicting information.
            """
            
            # Create resolution node as child of first node
            resolution_node = self.create_node(
                name=f"{node1.name}_Correction",
                context_window=resolution_prompt,
                node_type="correction",
                parent_node_id=node1_id
            )
            
            logger.info(f"Created conflict resolution node: {resolution_node.id}")
            return resolution_node
        except Exception as e:
            logger.error(f"Error creating conflict resolution node: {e}")
            raise
    
    def resolve_conflict(self, node1_id: str, node2_id: str, 
                        resolution_context: str,
                        user_feedback: Optional[str] = None,
                        resolved_by: Optional[str] = None) -> Tuple[Node, Node]:
        """
        Resolve conflict by updating both nodes with user feedback
        """
        node1 = self.get_node_by_id(node1_id)
        node2 = self.get_node_by_id(node2_id)
        
        if not node1 or not node2:
            raise ValueError("One or both nodes not found")
        
        try:
            # Sanitize resolution context
            resolution_context = self._sanitize_input(resolution_context)
            
            # Update both nodes with resolved context
            node1.context_window = resolution_context
            node1.mark_as_resolved()
            node1.updated_at = datetime.now()
            
            node2.context_window = resolution_context
            node2.mark_as_resolved()
            node2.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(node1)
            self.db.refresh(node2)
            
            # Remove from conflict queue
            conflict_id = f"{node1_id}:{node2_id}"
            if conflict_id in self.conflict_cache:
                del self.conflict_cache[conflict_id]
            
            # Invalidate caches
            self._invalidate_cache("node:*")
            self._invalidate_cache("node:conflict:*")
            
            # Update caches
            self._cache_node_data(node1)
            self._cache_node_data(node2)
            
            logger.info(f"Resolved conflict between {node1_id} and {node2_id}")
            return node1, node2
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error resolving conflict: {e}")
            raise
    
    def create_continuation_node(self, parent_id: str, new_context: str) -> Node:
        """
        Create a continuation node when context exceeds token limit
        """
        parent = self.get_node_by_id(parent_id)
        if not parent:
            raise ValueError("Parent node not found")
        
        try:
            continuation_node = self.create_node(
                name=f"{parent.name}_Continuation",
                context_window=new_context,
                node_type=parent.node_type,
                parent_node_id=parent_id,
                llm_model=parent.llm_model_used
            )
            
            logger.info(f"Created continuation node: {continuation_node.id}")
            return continuation_node
        except Exception as e:
            logger.error(f"Error creating continuation node: {e}")
            raise
    
    def split_large_context(self, node_id: str, threshold: str = "medium") -> List[Node]:
        """
        Split a node with large context into multiple continuation nodes
        """
        node = self.get_node_by_id(node_id)
        if not node:
            return []
        
        if not self.ollama.check_token_limit(node.context_window, threshold):
            return [node]
        
        try:
            # Split context into chunks
            chunks = self.ollama.split_context(node.context_window, threshold)
            
            # Keep first chunk in original node
            node.context_window = chunks[0]
            node.updated_at = datetime.now()
            self.db.commit()
            
            # Create continuation nodes for remaining chunks
            continuation_nodes = []
            for i, chunk in enumerate(chunks[1:], 1):
                continuation_node = self.create_node(
                    name=f"{node.name}_Continuation_{i}",
                    context_window=chunk,
                    node_type=node.node_type,
                    parent_node_id=str(node.id),
                    llm_model=node.llm_model_used
                )
                continuation_nodes.append(continuation_node)
            
            logger.info(f"Split node {node_id} into {len(chunks)} chunks")
            return [node] + continuation_nodes
        except Exception as e:
            logger.error(f"Error splitting large context: {e}")
            return [node]
    
    def get_node_graph(self) -> Dict[str, Any]:
        """
        Get the complete node graph structure with caching
        """
        cache_key = self._get_cache_key("graph", "complete")
        cached_graph = self._cache_get(cache_key)
        if cached_graph:
            return cached_graph
        
        try:
            nodes = self.get_all_nodes()
            graph = {
                "nodes": [],
                "edges": []
            }
            
            for node in nodes:
                graph["nodes"].append({
                    "id": str(node.id),
                    "name": node.name,
                    "type": node.node_type,
                    "status": node.status,
                    "model": node.llm_model_used
                })
                
                if node.parent_node:
                    graph["edges"].append({
                        "source": str(node.parent_node),
                        "target": str(node.id),
                        "type": "parent-child"
                    })
            
            # Cache graph data
            self._cache_set(cache_key, graph, self.cache_ttl['graph_data'])
            return graph
        except Exception as e:
            logger.error(f"Error getting node graph: {e}")
            return {"nodes": [], "edges": []}
    
    def search_nodes(self, query: str) -> List[Node]:
        """
        Search nodes by name or context content with caching
        """
        # Sanitize search query
        query = self._sanitize_input(query)
        
        cache_key = self._get_cache_key("search", str(hash(query)))
        cached_results = self._cache_get(cache_key)
        if cached_results:
            return [Node(**node_data) for node_data in cached_results]
        
        try:
            nodes = self.db.query(Node).filter(
                or_(
                    Node.name.ilike(f"%{query}%"),
                    Node.context_window.ilike(f"%{query}%")
                )
            ).all()
            
            # Cache search results
            if self.redis_client:
                node_data_list = [node.to_dict() for node in nodes]
                self._cache_set(cache_key, node_data_list, self.cache_ttl['search_results'])
            
            return nodes
        except Exception as e:
            logger.error(f"Error searching nodes: {e}")
            return []
    
    def _sanitize_input(self, text: str) -> str:
        """Sanitize user input to prevent XSS and SQL injection"""
        if not text:
            return text
        
        # Basic XSS prevention
        text = text.replace("<script>", "").replace("</script>", "")
        text = text.replace("javascript:", "")
        text = text.replace("onerror=", "")
        text = text.replace("onload=", "")
        
        # SQL injection prevention (basic)
        text = text.replace("'", "''")
        text = text.replace(";", "")
        text = text.replace("--", "")
        
        return text.strip()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        if not self.redis_client:
            return {"error": "Redis not available"}
        
        try:
            info = self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "conflict_queue_size": len(self.conflict_queue),
                "conflict_cache_size": len(self.conflict_cache)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}
    
    def clear_cache(self, pattern: str = "node:*") -> bool:
        """Clear cache entries matching pattern"""
        return self._invalidate_cache(pattern) 