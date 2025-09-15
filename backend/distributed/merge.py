"""
Merge Agent for Node-LLM System
Responsible for computing diffs between child and parent nodes, producing semantic summaries,
enforcing merge policy, applying approved merges, creating snapshots, handling conflicts, 
and propagating staleness.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import difflib
import uuid

# Local imports
from services.neo4j_service import Neo4jService
from services.versioning_service import VersioningService
from config.neo4j import neo4j_settings

logger = logging.getLogger(__name__)

class MergePreview:
    def __init__(self, merge_id: str = None, text_diff: str = "", json_patch: List[Dict] = None, 
                 diff_summary: str = "", impact: Dict = None, conflict: bool = False, 
                 conflict_node_id: str = None):
        self.merge_id = merge_id
        self.text_diff = text_diff
        self.json_patch = json_patch or []
        self.diff_summary = diff_summary
        self.impact = impact or {}
        self.conflict = conflict
        self.conflict_node_id = conflict_node_id
    
    def to_dict(self):
        return {
            "merge_id": self.merge_id,
            "text_diff": self.text_diff,
            "json_patch": self.json_patch,
            "diff_summary": self.diff_summary,
            "impact": self.impact,
            "conflict": self.conflict,
            "conflict_node_id": self.conflict_node_id
        }

class ApplyResult:
    def __init__(self, success: bool = False, commit_id: str = None, error: str = None):
        self.success = success
        self.commit_id = commit_id
        self.error = error
    
    def to_dict(self):
        return {
            "success": self.success,
            "commit_id": self.commit_id,
            "error": self.error
        }

class MergeAgent:
    """Merge Agent for handling node merges in the Node-LLM System"""
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        """Initialize the Merge Agent with service connections"""
        # Initialize Neo4j connection
        try:
            self.neo4j_service = Neo4jService(
                neo4j_settings.NEO4J_URI,
                neo4j_settings.NEO4J_USER,
                neo4j_settings.NEO4J_PASSWORD
            )
            logger.info("Neo4j connection established for MergeAgent")
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}")
            self.neo4j_service = None
        
        # Initialize VersioningService
        try:
            self.versioning_service = VersioningService()
            logger.info("VersioningService initialized for MergeAgent")
        except Exception as e:
            logger.warning(f"VersioningService initialization failed: {e}")
            self.versioning_service = None
    
    def _load_node_content(self, node_id: str) -> str:
        """Fetch latest content snapshot for node"""
        if not self.neo4j_service:
            return ""
        
        try:
            node = self.neo4j_service.get_node(node_id)
            if node:
                return node.get('context_window', '')
            return ""
        except Exception as e:
            logger.error(f"Error loading content for node {node_id}: {e}")
            return ""
    
    def _compute_unified_diff(self, a: str, b: str) -> str:
        """Compute unified diff between two strings"""
        try:
            diff = difflib.unified_diff(
                a.splitlines(keepends=True),
                b.splitlines(keepends=True),
                fromfile='parent',
                tofile='child'
            )
            return ''.join(diff)
        except Exception as e:
            logger.error(f"Error computing unified diff: {e}")
            return ""
    
    def _compute_json_patch(self, a_json: Dict, b_json: Dict) -> List[Dict]:
        """Compute JSON Patch operations (RFC 6902)"""
        # This is a simplified implementation
        # In practice, you would use a proper JSON Patch library
        patch = []
        
        # For now, we'll just create a simple replace operation if the objects are different
        if a_json != b_json:
            patch.append({
                "op": "replace",
                "path": "/",
                "value": b_json
            })
        
        return patch
    
    def _semantic_summarizer(self, parent_snippet: str, child_snippet: str, diff_text: str) -> str:
        """Call LLM to summarize changes semantically"""
        # This is a placeholder implementation
        # In practice, this would call an LLM service
        
        # Simple heuristic-based summary for now
        parent_lines = len(parent_snippet.splitlines())
        child_lines = len(child_snippet.splitlines())
        diff_lines = len(diff_text.splitlines())
        
        summary = f"""Changes Summary:
- Parent content has {parent_lines} lines
- Child content has {child_lines} lines
- Diff shows {diff_lines} lines of changes

This is a placeholder summary. In production, this would be generated by an LLM."""
        
        return summary
    
    def _create_snapshot(self, node_id: str, author: str, reason: str) -> str:
        """Create snapshot of current node state and return commit_id"""
        if not self.versioning_service or not self.neo4j_service:
            return ""
        
        try:
            # Get current node content
            node = self.neo4j_service.get_node(node_id)
            if not node:
                return ""
            
            context_window = node.get('context_window', '')
            
            # Get current version count to determine next version number
            versions = self.versioning_service.get_version_snapshots(node_id)
            version_number = len(versions) + 1
            
            # Create the snapshot
            success = self.versioning_service.create_version_snapshot(
                node_id, context_window, version_number
            )
            
            if success:
                commit_id = f"commit_{uuid.uuid4().hex}"
                logger.info(f"Created snapshot {commit_id} for node {node_id}")
                return commit_id
            
            return ""
        except Exception as e:
            logger.error(f"Error creating snapshot for node {node_id}: {e}")
            return ""
    
    def _apply_json_patch_to_content(self, content: Dict, patch: List[Dict]) -> Dict:
        """Apply JSON patch safely"""
        # This is a simplified implementation
        # In practice, you would use a proper JSON Patch library
        result = content.copy()
        
        for operation in patch:
            op = operation.get('op')
            path = operation.get('path')
            value = operation.get('value')
            
            if op == 'replace' and path == '/':
                result = value
            # Add more operations as needed
        
        return result
    
    def _is_structured(self, content: str) -> bool:
        """Check if content is structured (JSON/YAML)"""
        content = content.strip()
        return content.startswith('{') and content.endswith('}')
    
    def _parse_structured(self, content: str) -> Dict:
        """Parse structured content (JSON/YAML)"""
        try:
            import json
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error parsing structured content: {e}")
            return {}
    
    def _estimate_impact(self, text_diff: str) -> Dict:
        """Estimate impact of changes"""
        lines = text_diff.splitlines()
        added_lines = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
        removed_lines = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
        
        return {
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "total_changes": added_lines + removed_lines
        }
    
    def _create_merge_conflict_node(self, parent_id: str, conflicting_merge_ids: List[str]) -> str:
        """Create a conflict node that references both merges"""
        if not self.neo4j_service:
            return ""
        
        try:
            conflict_node_id = f"conflict_{uuid.uuid4().hex}"
            conflict_description = f"Merge conflict between merges: {', '.join(conflicting_merge_ids)}"
            
            success = self.neo4j_service.create_node(
                node_id=conflict_node_id,
                name=f"Merge Conflict for {parent_id}",
                node_type="merge_conflict",
                context_window=conflict_description,
                parent_id=parent_id,
                conflicting_merges=conflicting_merge_ids
            )
            
            if success:
                # Create relationship to parent
                self.neo4j_service.create_edge(
                    source_id=conflict_node_id,
                    target_id=parent_id,
                    relationship_type="CONFLICTS_WITH"
                )
                return conflict_node_id
            
            return ""
        except Exception as e:
            logger.error(f"Error creating conflict node: {e}")
            return ""
    
    async def compute_merge(self, child_id: str) -> MergePreview:
        """Compute merge preview for a child node"""
        if not self.neo4j_service:
            return MergePreview(error="Neo4j service not available")
        
        try:
            # Get child node
            child = self.neo4j_service.get_node(child_id)
            if not child:
                return MergePreview(error=f"Child node {child_id} not found")
            
            # Get parent node
            parent = self.neo4j_service.get_parent_node(child_id)
            if not parent:
                return MergePreview(error=f"Parent node for child {child_id} not found")
            
            parent_id = parent.get('id')
            
            # Extract content
            parent_content = self._load_node_content(parent_id)
            child_content = self._load_node_content(child_id)
            
            # Compute text diff
            text_diff = self._compute_unified_diff(parent_content, child_content)
            
            # Compute JSON patch if content is structured
            json_patch = None
            if self._is_structured(parent_content) and self._is_structured(child_content):
                parent_json = self._parse_structured(parent_content)
                child_json = self._parse_structured(child_content)
                json_patch = self._compute_json_patch(parent_json, child_json)
            
            # Conflict detection (simplified)
            # In a real implementation, this would check for overlapping patches
            # For now, we'll assume no conflicts
            
            # Semantic summarization
            summary = self._semantic_summarizer(parent_content, child_content, text_diff)
            
            # Estimate impact
            impact = self._estimate_impact(text_diff)
            
            # Create merge ID
            merge_id = f"merge_{uuid.uuid4().hex}"
            
            # In a real implementation, we would persist the MergeRequest record
            # For now, we'll just return the preview
            
            return MergePreview(
                merge_id=merge_id,
                text_diff=text_diff,
                json_patch=json_patch,
                diff_summary=summary,
                impact=impact
            )
            
        except Exception as e:
            logger.error(f"Error computing merge for child {child_id}: {e}")
            return MergePreview(error=str(e))
    
    async def apply_merge(self, child_id: str, approver: str) -> ApplyResult:
        """Apply an approved merge to update the parent node"""
        if not self.neo4j_service or not self.versioning_service:
            return ApplyResult(error="Required services not available")
        
        try:
            # Get child node
            child = self.neo4j_service.get_node(child_id)
            if not child:
                return ApplyResult(error=f"Child node {child_id} not found")
            
            # Get parent node
            parent = self.neo4j_service.get_parent_node(child_id)
            if not parent:
                return ApplyResult(error=f"Parent node for child {child_id} not found")
            
            parent_id = parent.get('id')
            
            # Create parent snapshot
            commit_id = self._create_snapshot(
                parent_id, 
                author=approver, 
                reason=f'Applying merge for child {child_id}'
            )
            
            if not commit_id:
                return ApplyResult(error="Failed to create snapshot")
            
            # Get child content to apply
            child_content = self._load_node_content(child_id)
            
            # Update parent node content
            success = self.neo4j_service.update_node_context(parent_id, child_content)
            
            if not success:
                return ApplyResult(error="Failed to update parent node")
            
            # In a real implementation, we would:
            # 1. Update merge record status
            # 2. Create Version record linked to parent
            # 3. Mark dependents stale
            # 4. Emit events
            
            # For now, we'll just mark dependents stale
            if self.versioning_service:
                self.versioning_service.propagate_staleness(parent_id)
            
            return ApplyResult(success=True, commit_id=commit_id)
            
        except Exception as e:
            logger.error(f"Error applying merge for child {child_id}: {e}")
            return ApplyResult(error=str(e))

# Initialize merge agent
merge_agent = MergeAgent()
