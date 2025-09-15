import pytest
import unittest.mock as mock
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

from ..services.conflict_service import ConflictService, ConflictPriority, ConflictItem
from ..models.node import Node

class TestConflictService:
    """Test cases for ConflictService"""
    
    @pytest.fixture
    def conflict_service(self):
        """Create ConflictService instance for testing"""
        with patch('redis.from_url'):
            service = ConflictService("redis://localhost:6379")
            return service
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        with patch('redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_redis.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock()
    
    @pytest.fixture
    def sample_nodes(self):
        """Sample nodes for testing"""
        node1 = MagicMock(spec=Node)
        node1.id = "node1"
        node1.name = "Test Node 1"
        node1.context_window = "Context for node 1"
        node1.status = "pending"
        
        node2 = MagicMock(spec=Node)
        node2.id = "node2"
        node2.name = "Test Node 2"
        node2.context_window = "Context for node 2"
        node2.status = "pending"
        
        return node1, node2
    
    def test_init(self, mock_redis):
        """Test ConflictService initialization"""
        service = ConflictService("redis://localhost:6379")
        
        assert service.redis_url == "redis://localhost:6379"
        assert service.conflict_queue == []
        assert service.conflict_cache == {}
        assert service.cache_ttl == 1800
    
    def test_get_cache_key(self, conflict_service):
        """Test cache key generation"""
        key = conflict_service._get_cache_key('detect', node1='node1', node2='node2')
        assert key == "conflict:detect:node1:node1:node2:node2"
    
    def test_cache_operations(self, conflict_service, mock_redis):
        """Test cache get/set operations"""
        # Test cache set
        conflict_service.redis_client.setex.return_value = True
        result = conflict_service._cache_set("test_key", "test_value")
        assert result is True
        
        # Test cache get
        conflict_service.redis_client.get.return_value = "test_value"
        result = conflict_service._cache_get("test_key")
        assert result == "test_value"
        
        # Test cache get with None
        conflict_service.redis_client.get.return_value = None
        result = conflict_service._cache_get("test_key")
        assert result is None
    
    def test_detect_conflicts_success(self, conflict_service, mock_db, sample_nodes):
        """Test successful conflict detection"""
        node1, node2 = sample_nodes
        
        # Mock database query
        mock_db.query.return_value.filter.return_value.first.side_effect = [node1, node2]
        
        # Mock cache miss
        conflict_service.redis_client.get.return_value = None
        conflict_service.redis_client.setex.return_value = True
        
        # Mock LLM service
        with patch.object(conflict_service.llm_service, 'detect_conflicts') as mock_detect:
            mock_detect.return_value = {
                'conflicts': ['Conflict 1'],
                'severity': 'high',
                'priority': 8,
                'suggestions': ['Suggestion 1'],
                'raw_analysis': 'Analysis content'
            }
            
            result = conflict_service.detect_conflicts(
                mock_db, "node1", "node2", "User feedback"
            )
            
            assert result['node1_id'] == "node1"
            assert result['node2_id'] == "node2"
            assert result['severity'] == "high"
            assert result['priority'] == 2  # HIGH priority
            assert result['status'] == "pending"
            
            # Check that nodes were updated
            assert node1.status == "conflicting"
            assert node2.status == "conflicting"
            mock_db.commit.assert_called_once()
    
    def test_detect_conflicts_node_not_found(self, conflict_service, mock_db):
        """Test conflict detection with missing nodes"""
        # Mock database query returning None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="One or both nodes not found"):
            conflict_service.detect_conflicts(mock_db, "node1", "node2")
    
    def test_detect_conflicts_cache_hit(self, conflict_service, mock_db, sample_nodes):
        """Test conflict detection with cache hit"""
        node1, node2 = sample_nodes
        
        # Mock database query
        mock_db.query.return_value.filter.return_value.first.side_effect = [node1, node2]
        
        # Mock cache hit
        cached_result = {
            'id': 'conflict_123',
            'node1_id': 'node1',
            'node2_id': 'node2',
            'severity': 'medium',
            'priority': 5,
            'status': 'pending'
        }
        conflict_service.redis_client.get.return_value = json.dumps(cached_result)
        
        result = conflict_service.detect_conflicts(mock_db, "node1", "node2")
        
        assert result['id'] == 'conflict_123'
        # Should not call LLM service
        assert not hasattr(conflict_service.llm_service, 'detect_conflicts')
    
    def test_add_conflict_to_queue(self, conflict_service):
        """Test adding conflict to priority queue"""
        conflict_data = {
            'id': 'conflict_123',
            'priority': 2,
            'created_at': datetime.now().isoformat(),
            'node1_id': 'node1',
            'node2_id': 'node2',
            'description': 'Test conflict',
            'severity': 'high',
            'user_feedback': ''
        }
        
        conflict_service._add_conflict_to_queue(conflict_data)
        
        assert len(conflict_service.conflict_queue) == 1
        assert 'conflict_123' in conflict_service.conflict_cache
        assert conflict_service.conflict_cache['conflict_123']['priority'] == 2
    
    def test_get_next_conflict(self, conflict_service):
        """Test getting next conflict from queue"""
        # Add conflicts to queue
        conflict1 = {
            'id': 'conflict_1',
            'priority': 1,
            'created_at': datetime.now().isoformat(),
            'node1_id': 'node1',
            'node2_id': 'node2',
            'description': 'High priority conflict',
            'severity': 'critical',
            'user_feedback': ''
        }
        
        conflict2 = {
            'id': 'conflict_2',
            'priority': 3,
            'created_at': datetime.now().isoformat(),
            'node1_id': 'node3',
            'node2_id': 'node4',
            'description': 'Lower priority conflict',
            'severity': 'medium',
            'user_feedback': ''
        }
        
        conflict_service._add_conflict_to_queue(conflict1)
        conflict_service._add_conflict_to_queue(conflict2)
        
        # Get next conflict (should be highest priority)
        result = conflict_service.get_next_conflict()
        
        assert result['id'] == 'conflict_1'
        assert result['priority'] == 1
        assert len(conflict_service.conflict_queue) == 1
    
    def test_get_next_conflict_empty_queue(self, conflict_service):
        """Test getting next conflict from empty queue"""
        result = conflict_service.get_next_conflict()
        assert result is None
    
    def test_get_all_conflicts(self, conflict_service):
        """Test getting all conflicts"""
        # Add conflicts
        conflict1 = {
            'id': 'conflict_1',
            'priority': 1,
            'created_at': '2023-01-01T00:00:00',
            'node1_id': 'node1',
            'node2_id': 'node2',
            'description': 'Conflict 1',
            'severity': 'critical',
            'user_feedback': ''
        }
        
        conflict2 = {
            'id': 'conflict_2',
            'priority': 2,
            'created_at': '2023-01-02T00:00:00',
            'node1_id': 'node3',
            'node2_id': 'node4',
            'description': 'Conflict 2',
            'severity': 'high',
            'user_feedback': ''
        }
        
        conflict_service._add_conflict_to_queue(conflict1)
        conflict_service._add_conflict_to_queue(conflict2)
        
        conflicts = conflict_service.get_all_conflicts()
        
        assert len(conflicts) == 2
        # Should be sorted by priority
        assert conflicts[0]['priority'] == 1
        assert conflicts[1]['priority'] == 2
    
    def test_resolve_conflict_success(self, conflict_service, mock_db, sample_nodes):
        """Test successful conflict resolution"""
        node1, node2 = sample_nodes
        
        # Add conflict to cache
        conflict_data = {
            'id': 'conflict_123',
            'node1_id': 'node1',
            'node2_id': 'node2',
            'description': 'Test conflict'
        }
        conflict_service.conflict_cache['conflict_123'] = conflict_data
        
        # Mock database query
        mock_db.query.return_value.filter.return_value.first.side_effect = [node1, node2]
        
        # Mock LLM service
        with patch.object(conflict_service.llm_service, 'resolve_conflict') as mock_resolve:
            mock_resolve.return_value = {
                'content': 'Resolution content',
                'provider': 'ollama'
            }
            
            # Mock resolution node creation
            resolution_node = MagicMock(spec=Node)
            resolution_node.id = 'resolution_123'
            mock_db.add.return_value = None
            
            result = conflict_service.resolve_conflict(
                mock_db, 'conflict_123', 'Resolution context', 'User feedback'
            )
            
            assert result['conflict_id'] == 'conflict_123'
            assert result['resolution_content'] == 'Resolution content'
            assert result['llm_provider'] == 'ollama'
            
            # Check that conflict was removed from queue
            assert 'conflict_123' not in conflict_service.conflict_cache
    
    def test_resolve_conflict_not_found(self, conflict_service, mock_db):
        """Test conflict resolution with non-existent conflict"""
        with pytest.raises(ValueError, match="Conflict not found"):
            conflict_service.resolve_conflict(mock_db, 'nonexistent', 'context', 'feedback')
    
    def test_get_conflict_stats(self, conflict_service):
        """Test conflict statistics"""
        # Add conflicts with different statuses
        conflict1 = {'status': 'pending', 'severity': 'high', 'priority': 2}
        conflict2 = {'status': 'resolved', 'severity': 'medium', 'priority': 5}
        conflict3 = {'status': 'pending', 'severity': 'low', 'priority': 8}
        
        conflict_service.conflict_cache = {
            'conflict_1': conflict1,
            'conflict_2': conflict2,
            'conflict_3': conflict3
        }
        
        stats = conflict_service.get_conflict_stats()
        
        assert stats['total_conflicts'] == 3
        assert stats['pending_conflicts'] == 2
        assert stats['resolved_conflicts'] == 1
        assert stats['by_severity']['high'] == 1
        assert stats['by_severity']['medium'] == 1
        assert stats['by_severity']['low'] == 1
        assert stats['by_priority'][2] == 1
        assert stats['by_priority'][5] == 1
        assert stats['by_priority'][8] == 1
    
    def test_update_conflict_feedback(self, conflict_service):
        """Test updating conflict feedback"""
        conflict_data = {
            'id': 'conflict_123',
            'user_feedback': 'Old feedback'
        }
        conflict_service.conflict_cache['conflict_123'] = conflict_data
        
        # Add to queue
        conflict_item = ConflictItem(
            priority=2,
            timestamp=datetime.now(),
            conflict_id='conflict_123',
            node1_id='node1',
            node2_id='node2',
            description='Test',
            severity='high',
            user_feedback='Old feedback'
        )
        conflict_service.conflict_queue.append(conflict_item)
        
        result = conflict_service.update_conflict_feedback('conflict_123', 'New feedback')
        
        assert result is True
        assert conflict_service.conflict_cache['conflict_123']['user_feedback'] == 'New feedback'
        assert conflict_service.conflict_queue[0].user_feedback == 'New feedback'
    
    def test_update_conflict_feedback_not_found(self, conflict_service):
        """Test updating feedback for non-existent conflict"""
        result = conflict_service.update_conflict_feedback('nonexistent', 'New feedback')
        assert result is False
    
    def test_clear_resolved_conflicts(self, conflict_service):
        """Test clearing resolved conflicts"""
        # Add conflicts with different statuses
        conflict1 = {'status': 'resolved'}
        conflict2 = {'status': 'pending'}
        conflict3 = {'status': 'resolved'}
        
        conflict_service.conflict_cache = {
            'conflict_1': conflict1,
            'conflict_2': conflict2,
            'conflict_3': conflict3
        }
        
        # Add to queue
        for conflict_id in ['conflict_1', 'conflict_2', 'conflict_3']:
            conflict_item = ConflictItem(
                priority=2,
                timestamp=datetime.now(),
                conflict_id=conflict_id,
                node1_id='node1',
                node2_id='node2',
                description='Test',
                severity='high'
            )
            conflict_service.conflict_queue.append(conflict_item)
        
        cleared_count = conflict_service.clear_resolved_conflicts()
        
        assert cleared_count == 2
        assert 'conflict_1' not in conflict_service.conflict_cache
        assert 'conflict_3' not in conflict_service.conflict_cache
        assert 'conflict_2' in conflict_service.conflict_cache  # Pending conflict remains
        assert len(conflict_service.conflict_queue) == 1  # Only pending conflict remains

class TestConflictPriority:
    """Test ConflictPriority enum"""
    
    def test_priority_values(self):
        """Test priority enum values"""
        assert ConflictPriority.CRITICAL.value == 1
        assert ConflictPriority.HIGH.value == 2
        assert ConflictPriority.MEDIUM.value == 3
        assert ConflictPriority.LOW.value == 4

class TestConflictItem:
    """Test ConflictItem dataclass"""
    
    def test_conflict_item_creation(self):
        """Test ConflictItem creation"""
        timestamp = datetime.now()
        item = ConflictItem(
            priority=2,
            timestamp=timestamp,
            conflict_id='conflict_123',
            node1_id='node1',
            node2_id='node2',
            description='Test conflict',
            severity='high',
            user_feedback='User feedback'
        )
        
        assert item.priority == 2
        assert item.timestamp == timestamp
        assert item.conflict_id == 'conflict_123'
        assert item.node1_id == 'node1'
        assert item.node2_id == 'node2'
        assert item.description == 'Test conflict'
        assert item.severity == 'high'
        assert item.user_feedback == 'User feedback'
    
    def test_conflict_item_comparison(self):
        """Test ConflictItem comparison for priority queue"""
        timestamp = datetime.now()
        item1 = ConflictItem(
            priority=1,  # Higher priority
            timestamp=timestamp,
            conflict_id='conflict_1',
            node1_id='node1',
            node2_id='node2',
            description='High priority',
            severity='critical'
        )
        
        item2 = ConflictItem(
            priority=3,  # Lower priority
            timestamp=timestamp,
            conflict_id='conflict_2',
            node1_id='node3',
            node2_id='node4',
            description='Lower priority',
            severity='medium'
        )
        
        # Higher priority (lower number) should be less than lower priority
        assert item1 < item2
        assert not item2 < item1 