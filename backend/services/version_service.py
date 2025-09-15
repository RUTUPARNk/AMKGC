"""
Version Service

This service handles versioning and snapshots for nodes in the Node-LLM system.
It provides functionality for creating snapshots, retrieving version history,
generating diffs, and rolling back to previous versions.
"""

from __future__ import annotations

import json
import uuid
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Version:
    """Represents a version/snapshot of a node."""
    commit_id: str
    node_id: str
    content_snapshot: Dict[str, Any]
    diff_summary: Optional[str]
    diff_patch: Optional[List[Dict[str, Any]]]
    author: Optional[str]
    reason: Optional[str]
    created_at: datetime
    parent_commit_id: Optional[str] = None


@dataclass(frozen=True)
class DiffResult:
    """Represents the result of comparing two versions."""
    commit_a: str
    commit_b: str
    diff_summary: str
    diff_patch: List[Dict[str, Any]]
    changes: Dict[str, Any]  # Detailed changes


@dataclass(frozen=True)
class VersionConfig:
    """Configuration for the VersionService."""
    pg_dsn: str  # PostgreSQL connection string


class VersionService:
    """
    Service for managing node versions and snapshots.
    
    Features:
    - Create snapshots of node states
    - Retrieve version history
    - Generate diffs between versions
    - Rollback to previous versions
    """
    
    def __init__(self, cfg: VersionConfig) -> None:
        self.cfg = cfg
        self._conn = psycopg.connect(cfg.pg_dsn, row_factory=dict_row)
        self._conn.execute("SET application_name = 'version_service'")
        self._conn.commit()
    
    def create_snapshot(
        self,
        node_id: str,
        author: str,
        reason: str,
        content_snapshot: Optional[Dict[str, Any]] = None,
        diff_summary: Optional[str] = None,
        diff_patch: Optional[List[Dict[str, Any]]] = None,
        parent_commit_id: Optional[str] = None
    ) -> str:
        """
        Create a snapshot of a node's current state.
        
        Args:
            node_id: ID of the node to snapshot
            author: Author of the snapshot
            reason: Reason for the snapshot (e.g., "merge", "manual edit")
            content_snapshot: Complete snapshot of node content (if None, will fetch from nodes table)
            diff_summary: LLM-generated summary of changes
            diff_patch: Structured diff representation (JSON Patch)
            parent_commit_id: ID of the parent commit (for history tracking)
            
        Returns:
            commit_id: ID of the created snapshot
        """
        try:
            # If no content snapshot provided, fetch current node state
            if content_snapshot is None:
                content_snapshot = self._get_node_content(node_id)
            
            # Generate commit ID if not provided
            commit_id = str(uuid.uuid4())
            
            # Insert snapshot into versions table
            with self._conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO versions (
                        commit_id, node_id, content_snapshot, diff_summary, 
                        diff_patch, author, reason, parent_commit_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        commit_id, node_id, json.dumps(content_snapshot), diff_summary,
                        json.dumps(diff_patch) if diff_patch else None, author, reason, parent_commit_id
                    )
                )
                
                # Update node's current commit ID
                cur.execute("""
                    UPDATE nodes SET current_commit_id = %s WHERE id = %s
                    """, (commit_id, node_id)
                )
            
            self._conn.commit()
            logger.info(f"Created snapshot {commit_id} for node {node_id}")
            
            return commit_id
            
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Failed to create snapshot for node {node_id}: {e}")
            raise
    
    def get_versions(self, node_id: str) -> List[Version]:
        """
        Retrieve all versions for a specific node, ordered by creation time.
        
        Args:
            node_id: ID of the node to retrieve versions for
            
        Returns:
            List of Version objects
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    SELECT commit_id, node_id, content_snapshot, diff_summary, 
                           diff_patch, author, reason, created_at, parent_commit_id
                    FROM versions 
                    WHERE node_id = %s 
                    ORDER BY created_at DESC
                    """, (node_id,)
                )
                
                rows = cur.fetchall()
                
            versions = []
            for row in rows:
                versions.append(Version(
                    commit_id=row["commit_id"],
                    node_id=row["node_id"],
                    content_snapshot=row["content_snapshot"],
                    diff_summary=row["diff_summary"],
                    diff_patch=row["diff_patch"],
                    author=row["author"],
                    reason=row["reason"],
                    created_at=row["created_at"],
                    parent_commit_id=row["parent_commit_id"]
                ))
                
            return versions
            
        except Exception as e:
            logger.error(f"Failed to retrieve versions for node {node_id}: {e}")
            raise
    
    def get_version(self, commit_id: str) -> Optional[Version]:
        """
        Retrieve a specific version by commit ID.
        
        Args:
            commit_id: ID of the commit to retrieve
            
        Returns:
            Version object or None if not found
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    SELECT commit_id, node_id, content_snapshot, diff_summary, 
                           diff_patch, author, reason, created_at, parent_commit_id
                    FROM versions 
                    WHERE commit_id = %s
                    """, (commit_id,)
                )
                
                row = cur.fetchone()
                if not row:
                    return None
                
            return Version(
                commit_id=row["commit_id"],
                node_id=row["node_id"],
                content_snapshot=row["content_snapshot"],
                diff_summary=row["diff_summary"],
                diff_patch=row["diff_patch"],
                author=row["author"],
                reason=row["reason"],
                created_at=row["created_at"],
                parent_commit_id=row["parent_commit_id"]
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve version {commit_id}: {e}")
            raise
    
    def get_diff(self, commit_a: str, commit_b: str) -> DiffResult:
        """
        Generate a diff between two versions.
        
        Args:
            commit_a: ID of the first commit
            commit_b: ID of the second commit
            
        Returns:
            DiffResult object containing the comparison
        """
        try:
            # Retrieve both versions
            version_a = self.get_version(commit_a)
            version_b = self.get_version(commit_b)
            
            if not version_a or not version_b:
                raise ValueError("One or both commit IDs not found")
            
            if version_a.node_id != version_b.node_id:
                raise ValueError("Cannot diff versions from different nodes")
            
            # Generate diff using jsondiff or similar library
            # For now, we'll return a simple diff result
            # In a real implementation, you might use a library like jsondiff
            # or generate a JSON Patch (RFC 6902)
            
            changes = self._calculate_changes(
                version_a.content_snapshot, 
                version_b.content_snapshot
            )
            
            # Generate a simple diff summary
            diff_summary = f"Compared commits {commit_a[:8]} and {commit_b[:8]}"
            
            # Generate a simple JSON Patch (this is a simplified version)
            diff_patch = self._generate_json_patch(
                version_a.content_snapshot,
                version_b.content_snapshot
            )
            
            return DiffResult(
                commit_a=commit_a,
                commit_b=commit_b,
                diff_summary=diff_summary,
                diff_patch=diff_patch,
                changes=changes
            )
            
        except Exception as e:
            logger.error(f"Failed to generate diff between {commit_a} and {commit_b}: {e}")
            raise
    
    def rollback(self, node_id: str, commit_id: str) -> bool:
        """
        Rollback a node to a specific version.
        
        Args:
            node_id: ID of the node to rollback
            commit_id: ID of the commit to rollback to
            
        Returns:
            True if rollback was successful
        """
        try:
            # Retrieve the version to rollback to
            version = self.get_version(commit_id)
            
            if not version:
                raise ValueError(f"Commit {commit_id} not found")
            
            if version.node_id != node_id:
                raise ValueError("Commit does not belong to the specified node")
            
            # Update the node with the snapshot content
            content = version.content_snapshot
            with self._conn.cursor() as cur:
                cur.execute("""
                    UPDATE nodes 
                    SET name = %s, context_window = %s, parent_node = %s, 
                        child_nodes = %s, llm_model_used = %s, node_type = %s, 
                        status = %s, updated_at = NOW(), current_commit_id = %s
                    WHERE id = %s
                    """, (
                        content.get("name"),
                        content.get("context_window"),
                        content.get("parent_node"),
                        json.dumps(content.get("child_nodes", [])),
                        content.get("llm_model_used"),
                        content.get("node_type"),
                        content.get("status"),
                        commit_id,  # Set current commit ID to the rollback commit
                        node_id
                    )
                )
                
                # Create a new snapshot for the rollback
                self.create_snapshot(
                    node_id=node_id,
                    author="system",
                    reason="rollback",
                    content_snapshot=content,
                    diff_summary=f"Rolled back to commit {commit_id[:8]}",
                    parent_commit_id=commit_id
                )
            
            self._conn.commit()
            logger.info(f"Rolled back node {node_id} to commit {commit_id}")
            
            return True
            
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Failed to rollback node {node_id} to commit {commit_id}: {e}")
            raise
    
    def _get_node_content(self, node_id: str) -> Dict[str, Any]:
        """
        Retrieve the current content of a node.
        
        Args:
            node_id: ID of the node to retrieve
            
        Returns:
            Dictionary containing node content
        """
        with self._conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, context_window, parent_node, child_nodes,
                       llm_model_used, node_type, status, created_at, updated_at
                FROM nodes 
                WHERE id = %s
                """, (node_id,)
            )
            
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Node {node_id} not found")
            
        return dict(row)
    
    def _calculate_changes(self, content_a: Dict[str, Any], content_b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate detailed changes between two content snapshots.
        
        Args:
            content_a: First content snapshot
            content_b: Second content snapshot
            
        Returns:
            Dictionary describing the changes
        """
        changes = {}
        
        # Simple field-by-field comparison
        all_keys = set(content_a.keys()) | set(content_b.keys())
        
        for key in all_keys:
            value_a = content_a.get(key)
            value_b = content_b.get(key)
            
            if value_a != value_b:
                changes[key] = {
                    "from": value_a,
                    "to": value_b
                }
        
        return changes
    
    def _generate_json_patch(self, content_a: Dict[str, Any], content_b: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate a JSON Patch (RFC 6902) representation of the differences.
        
        Args:
            content_a: First content snapshot
            content_b: Second content snapshot
            
        Returns:
            List of JSON Patch operations
        """
        patch = []
        
        # Simple implementation - in a real system, you'd use a proper JSON Patch library
        all_keys = set(content_a.keys()) | set(content_b.keys())
        
        for key in all_keys:
            value_a = content_a.get(key)
            value_b = content_b.get(key)
            
            if key not in content_a:
                # Added field
                patch.append({
                    "op": "add",
                    "path": f"/{key}",
                    "value": value_b
                })
            elif key not in content_b:
                # Removed field
                patch.append({
                    "op": "remove",
                    "path": f"/{key}"
                })
            elif value_a != value_b:
                # Modified field
                patch.append({
                    "op": "replace",
                    "path": f"/{key}",
                    "value": value_b
                })
        
        return patch
    
    def close(self) -> None:
        """Close the database connection."""
        try:
            self._conn.close()
        except Exception:
            pass


def make_version_service_from_env() -> VersionService:
    """
    Factory function to create a VersionService from environment variables.
    """
    import os
    
    dsn = os.getenv("PG_DSN") or os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("PG_DSN or DATABASE_URL must be set")
    
    cfg = VersionConfig(pg_dsn=dsn)
    return VersionService(cfg)
