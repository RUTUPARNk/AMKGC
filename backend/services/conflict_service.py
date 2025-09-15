import json
import logging
import heapq
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import redis
from sqlalchemy.orm import Session

from models.node import Node
from services.llm_service import LLMService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConflictPriority(Enum):
    """Enum for conflict priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class ConflictItem:
    """Data class for conflict queue items"""
    priority: int
    timestamp: datetime
    conflict_id: str
    node1_id: str
    node2_id: str
    description: str
    severity: str
    user_feedback: str = ""
    
    def __lt__(self, other):
        # Lower priority number = higher priority
        if self.priority != other.priority:
            return self.priority < other.priority
        # If same priority, older conflicts come first
        return self.timestamp < other.timestamp

class ConflictService:
    """Service for managing node conflicts and resolution"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.llm_service = LLMService(redis_url)
        
        # Priority queue for conflicts (min-heap)
        self.conflict_queue = []
        self.conflict_cache = {}
        self.cache_ttl = 1800  # 30 minutes
        
        logger.info("ConflictService initialized")
    
    def _get_cache_key(self, operation: str, **kwargs) -> str:
        """Generate cache key for Redis"""
        key_parts = ['conflict', operation]
        for k, v in sorted(kwargs.items()):
            key_parts.extend([k, str(v)])
        return ':'.join(key_parts)
    
    def _cache_get(self, key: str) -> Optional[str]:
        """Get value from Redis cache"""
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def _cache_set(self, key: str, value: str, ttl: int = None) -> bool:
        """Set value in Redis cache with TTL"""
        try:
            ttl = ttl or self.cache_ttl
            return self.redis_client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def _invalidate_cache(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        try:
            keys = self.redis_client.keys(f"conflict:{pattern}")
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} conflict cache entries")
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    def detect_conflicts(self, db: Session, node1_id: str, node2_id: str, 
                        user_feedback: str = "") -> Dict[str, Any]:
        """Detect conflicts between two nodes"""
        try:
            # Get nodes from database
            node1 = db.query(Node).filter(Node.id == node1_id).first()
            node2 = db.query(Node).filter(Node.id == node2_id).first()
            
            if not node1 or not node2:
                raise ValueError("One or both nodes not found")
            
            # Check cache first
            cache_key = self._get_cache_key('detect', node1=node1_id, node2=node2_id, feedback=user_feedback)
            cached_result = self._cache_get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Use LLM to detect conflicts
            analysis = self.llm_service.detect_conflicts(
                node1.context_window,
                node2.context_window,
                user_feedback
            )
            
            # Determine priority based on severity
            priority_map = {
                'critical': ConflictPriority.CRITICAL.value,
                'high': ConflictPriority.HIGH.value,
                'medium': ConflictPriority.MEDIUM.value,
                'low': ConflictPriority.LOW.value
            }
            
            priority = priority_map.get(analysis['severity'].lower(), ConflictPriority.MEDIUM.value)
            
            # Create conflict record
            conflict_data = {
                'id': f"conflict_{node1_id}_{node2_id}_{datetime.now().timestamp()}",
                'node1_id': node1_id,
                'node2_id': node2_id,
                'node1_name': node1.name,
                'node2_name': node2.name,
                'description': analysis.get('raw_analysis', ''),
                'conflicts': analysis.get('conflicts', []),
                'severity': analysis['severity'],
                'priority': priority,
                'suggestions': analysis.get('suggestions', []),
                'user_feedback': user_feedback,
                'created_at': datetime.now().isoformat(),
                'status': 'pending'
            }
            
            # Add to priority queue
            self._add_conflict_to_queue(conflict_data)
            
            # Cache the result
            self._cache_set(cache_key, json.dumps(conflict_data))
            
            # Update node statuses
            node1.status = 'conflicting'
            node2.status = 'conflicting'
            db.commit()
            
            logger.info(f"Detected conflict between {node1.name} and {node2.name}")
            return conflict_data
            
        except Exception as e:
            logger.error(f"Error detecting conflicts: {e}")
            raise
    
    def _add_conflict_to_queue(self, conflict_data: Dict[str, Any]):
        """Add conflict to priority queue"""
        conflict_item = ConflictItem(
            priority=conflict_data['priority'],
            timestamp=datetime.fromisoformat(conflict_data['created_at']),
            conflict_id=conflict_data['id'],
            node1_id=conflict_data['node1_id'],
            node2_id=conflict_data['node2_id'],
            description=conflict_data['description'],
            severity=conflict_data['severity'],
            user_feedback=conflict_data.get('user_feedback', '')
        )
        
        heapq.heappush(self.conflict_queue, conflict_item)
        self.conflict_cache[conflict_data['id']] = conflict_data
        
        logger.info(f"Added conflict {conflict_data['id']} to queue with priority {conflict_data['priority']}")
    
    def get_next_conflict(self) -> Optional[Dict[str, Any]]:
        """Get the next highest priority conflict from the queue"""
        if not self.conflict_queue:
            return None
        
        conflict_item = heapq.heappop(self.conflict_queue)
        conflict_data = self.conflict_cache.get(conflict_item.conflict_id)
        
        if conflict_data:
            logger.info(f"Retrieved conflict {conflict_item.conflict_id} with priority {conflict_item.priority}")
            return conflict_data
        
        return None
    
    def get_all_conflicts(self) -> List[Dict[str, Any]]:
        """Get all conflicts sorted by priority"""
        return sorted(
            list(self.conflict_cache.values()),
            key=lambda x: (x['priority'], x['created_at'])
        )
    
    def resolve_conflict(self, db: Session, conflict_id: str, 
                        resolution_context: str, user_feedback: str = "") -> Dict[str, Any]:
        """Resolve a conflict with user-provided resolution"""
        try:
            conflict_data = self.conflict_cache.get(conflict_id)
            if not conflict_data:
                raise ValueError("Conflict not found")
            
            # Get nodes
            node1 = db.query(Node).filter(Node.id == conflict_data['node1_id']).first()
            node2 = db.query(Node).filter(Node.id == conflict_data['node2_id']).first()
            
            if not node1 or not node2:
                raise ValueError("One or both nodes not found")
            
            # Use LLM to generate final resolution
            llm_resolution = self.llm_service.resolve_conflict(
                conflict_data['description'],
                resolution_context,
                user_feedback
            )
            
            # Create resolution node
            resolution_node = Node(
                name=f"Resolution_{conflict_id}",
                context_window=llm_resolution['content'],
                parent_node=node1.id,
                node_type='resolution',
                status='resolved',
                llm_model_used=llm_resolution['provider']
            )
            
            db.add(resolution_node)
            db.commit()
            
            # Update parent nodes
            node1.status = 'resolved'
            node2.status = 'resolved'
            node1.child_nodes = node1.child_nodes or []
            node1.child_nodes.append(resolution_node.id)
            node2.child_nodes = node2.child_nodes or []
            node2.child_nodes.append(resolution_node.id)
            
            db.commit()
            
            # Remove from queue and cache
            self._remove_conflict_from_queue(conflict_id)
            
            # Invalidate related caches
            self._invalidate_cache(f"*{node1.id}*")
            self._invalidate_cache(f"*{node2.id}*")
            
            resolution_data = {
                'conflict_id': conflict_id,
                'resolution_node_id': resolution_node.id,
                'resolution_content': llm_resolution['content'],
                'user_feedback': user_feedback,
                'resolved_at': datetime.now().isoformat(),
                'llm_provider': llm_resolution['provider']
            }
            
            logger.info(f"Resolved conflict {conflict_id}")
            return resolution_data
            
        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            raise
    
    def _remove_conflict_from_queue(self, conflict_id: str):
        """Remove conflict from queue and cache"""
        # Remove from cache
        if conflict_id in self.conflict_cache:
            del self.conflict_cache[conflict_id]
        
        # Rebuild queue without this conflict
        new_queue = []
        for item in self.conflict_queue:
            if item.conflict_id != conflict_id:
                new_queue.append(item)
        
        heapq.heapify(new_queue)
        self.conflict_queue = new_queue
        
        logger.info(f"Removed conflict {conflict_id} from queue")
    
    def get_conflict_stats(self) -> Dict[str, Any]:
        """Get conflict statistics"""
        conflicts = list(self.conflict_cache.values())
        
        stats = {
            'total_conflicts': len(conflicts),
            'pending_conflicts': len([c for c in conflicts if c['status'] == 'pending']),
            'resolved_conflicts': len([c for c in conflicts if c['status'] == 'resolved']),
            'by_severity': {},
            'by_priority': {}
        }
        
        # Count by severity
        for conflict in conflicts:
            severity = conflict['severity']
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
        
        # Count by priority
        for conflict in conflicts:
            priority = conflict['priority']
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
        
        return stats
    
    def update_conflict_feedback(self, conflict_id: str, user_feedback: str) -> bool:
        """Update user feedback for a conflict"""
        try:
            if conflict_id in self.conflict_cache:
                self.conflict_cache[conflict_id]['user_feedback'] = user_feedback
                self.conflict_cache[conflict_id]['updated_at'] = datetime.now().isoformat()
                
                # Update in queue
                for item in self.conflict_queue:
                    if item.conflict_id == conflict_id:
                        item.user_feedback = user_feedback
                        break
                
                logger.info(f"Updated feedback for conflict {conflict_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating conflict feedback: {e}")
            return False
    
    def get_conflict_by_id(self, conflict_id: str) -> Optional[Dict[str, Any]]:
        """Get conflict by ID"""
        return self.conflict_cache.get(conflict_id)
    
    def clear_resolved_conflicts(self) -> int:
        """Clear resolved conflicts from cache"""
        try:
            resolved_conflicts = [
                conflict_id for conflict_id, data in self.conflict_cache.items()
                if data.get('status') == 'resolved'
            ]
            
            for conflict_id in resolved_conflicts:
                self._remove_conflict_from_queue(conflict_id)
            
            logger.info(f"Cleared {len(resolved_conflicts)} resolved conflicts")
            return len(resolved_conflicts)
            
        except Exception as e:
            logger.error(f"Error clearing resolved conflicts: {e}")
            return 0
    
    def export_conflicts(self) -> Dict[str, Any]:
        """Export all conflicts for backup/analysis"""
        return {
            'conflicts': list(self.conflict_cache.values()),
            'queue_size': len(self.conflict_queue),
            'exported_at': datetime.now().isoformat()
        }
    
    def import_conflicts(self, conflicts_data: Dict[str, Any]) -> bool:
        """Import conflicts from backup"""
        try:
            conflicts = conflicts_data.get('conflicts', [])
            
            for conflict in conflicts:
                if 'id' in conflict:
                    self.conflict_cache[conflict['id']] = conflict
                    self._add_conflict_to_queue(conflict)
            
            logger.info(f"Imported {len(conflicts)} conflicts")
            return True
            
        except Exception as e:
            logger.error(f"Error importing conflicts: {e}")
            return False 