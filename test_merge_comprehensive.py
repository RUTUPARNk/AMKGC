"""
Comprehensive test suite for Merge Agent
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.distributed.merge import MergeAgent, MergePreview, ApplyResult


class TestMergeAgent(unittest.TestCase):
    """Test suite for MergeAgent class"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.merge_agent = MergeAgent()
        # Mock services
        self.merge_agent.neo4j_service = Mock()
        self.merge_agent.versioning_service = Mock()
    
    def test_compute_unified_diff(self):
        """Test unified diff computation"""
        parent_content = "Line 1\nLine 2\nLine 3"
        child_content = "Line 1\nLine 2 modified\nLine 3\nLine 4"
        
        diff = self.merge_agent._compute_unified_diff(parent_content, child_content)
        self.assertIsInstance(diff, str)
        self.assertIn("@@", diff)  # Unified diff header
    
    def test_compute_json_patch(self):
        """Test JSON patch computation"""
        parent_content = '{"name": "test", "value": 1}'
        child_content = '{"name": "test modified", "value": 2, "new_field": "new"}'
        
        patch = self.merge_agent._compute_json_patch(parent_content, child_content)
        self.assertIsInstance(patch, list)
        self.assertGreater(len(patch), 0)
    
    def test_semantic_summarizer(self):
        """Test semantic summarization"""
        parent_content = "Original content"
        child_content = "Modified content"
        diff = "@@ -1 +1 @@\n-Original content\n+Modified content"
        
        summary = self.merge_agent._semantic_summarizer(parent_content, child_content, diff)
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)
    
    def test_estimate_impact(self):
        """Test impact estimation"""
        diff = "@@ -1 +1 @@\n-Original content\n+Modified content"
        
        impact = self.merge_agent._estimate_impact(diff)
        self.assertIsInstance(impact, dict)
        self.assertIn("nodes", impact)
        self.assertIn("edges", impact)
    
    @patch('backend.distributed.merge.uuid4')
    def test_create_conflict_node(self, mock_uuid):
        """Test conflict node creation"""
        mock_uuid.return_value = Mock(hex="1234567890abcdef")
        
        conflict_node_id = self.merge_agent._create_conflict_node(
            "parent123", "child123", "diff content"
        )
        self.assertEqual(conflict_node_id, "conflict_1234567890abcdef")
    
    def test_detect_conflicts(self):
        """Test conflict detection"""
        # Currently a placeholder, should return False
        has_conflict = self.merge_agent._detect_conflicts("diff content")
        self.assertFalse(has_conflict)


class TestMergePreview(unittest.TestCase):
    """Test suite for MergePreview class"""
    
    def test_merge_preview_creation(self):
        """Test MergePreview object creation"""
        preview = MergePreview(
            merge_id="merge123",
            text_diff="diff content",
            json_patch=[],
            diff_summary="summary",
            impact={},
            conflict=False
        )
        
        self.assertEqual(preview.merge_id, "merge123")
        self.assertEqual(preview.text_diff, "diff content")
        self.assertEqual(preview.diff_summary, "summary")
        self.assertFalse(preview.conflict)
    
    def test_merge_preview_to_dict(self):
        """Test MergePreview to_dict method"""
        preview = MergePreview(
            merge_id="merge123",
            text_diff="diff content",
            json_patch=[],
            diff_summary="summary",
            impact={},
            conflict=False
        )
        
        result = preview.to_dict()
        self.assertIsInstance(result, dict)
        self.assertEqual(result["merge_id"], "merge123")


class TestApplyResult(unittest.TestCase):
    """Test suite for ApplyResult class"""
    
    def test_apply_result_creation(self):
        """Test ApplyResult object creation"""
        result = ApplyResult(
            success=True,
            commit_id="commit123"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.commit_id, "commit123")
    
    def test_apply_result_to_dict(self):
        """Test ApplyResult to_dict method"""
        result = ApplyResult(
            success=True,
            commit_id="commit123"
        )
        
        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertTrue(result_dict["success"])
        self.assertEqual(result_dict["commit_id"], "commit123")


if __name__ == '__main__':
    unittest.main()
