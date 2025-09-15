"""
Continuation Service

This service manages continuation nodes for handling token overflow in large node contexts.
It provides functionality for automatically splitting nodes when they exceed token limits
and traversing continuation chains.
"""

from __future__ import annotations

import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NodeChain:
    """Represents a chain of continuation nodes."""
    root_node_id: str
    nodes: List[Dict[str, Any]]  # List of nodes in chronological order


@dataclass(frozen=True)
class ContinuationConfig:
    """Configuration for the ContinuationService."""
    pg_dsn: str  # PostgreSQL connection string
    default_token_limit: int = 2_000_000  # Default token limit before splitting
    min_tokens_to_keep: int = 100_000   # Minimum tokens to keep in parent node


class ContinuationService:
    """
    Service for managing continuation nodes to handle token overflow.
    
    Features:
    - Automatically split nodes when they exceed token limits
    - Traverse continuation chains
    - Manage node lifecycle during continuation creation
    """
    
    def __init__(self, cfg: ContinuationConfig) -> None:
        self.cfg = cfg
        self._conn = psycopg.connect(cfg.pg_dsn, row_factory=dict_row)
        self._conn.execute("SET application_name = 'continuation_service'")
        self._conn.commit()
    
    async def check_and_split(self, node_id: str, new_message: str, token_limit: Optional[int] = None) -> str:
        """
        Check if a node needs to be split due to token overflow and create a continuation node if needed.
        
        Args:
            node_id: ID of the node to check
            new_message: New message to be added
            token_limit: Token limit before splitting (defaults to config value)
            
        Returns:
            ID of the node where the message should be added (either original or continuation)
        """
        try:
            token_limit = token_limit or self.cfg.default_token_limit
            
            # 1. Count tokens for node history
            token_count = await self._count_node_tokens(node_id)
            new_message_tokens = await self._count_text_tokens(new_message)
            
            # 2. If within limit → just return the original node ID
            if token_count + new_message_tokens <= token_limit:
                logger.info(f"Node {node_id} is within token limit ({token_count + new_message_tokens} <= {token_limit})")
                return node_id
            
            # 3. Otherwise → create a continuation node
            logger.info(f"Node {node_id} exceeds token limit ({token_count + new_message_tokens} > {token_limit}), creating continuation")
            
            # Get the parent node details
            parent_node = await self._get_node(node_id)
            if not parent_node:
                raise ValueError(f"Node {node_id} not found")
            
            # Create a continuation node
            continuation_id = await self._create_continuation_node(
                parent_node=parent_node,
                initial_text=new_message
            )
            
            # 4. Mark parent as "archived"
            await self._archive_node(node_id)
            
            logger.info(f"Created continuation node {continuation_id} for parent {node_id}")
            
            return continuation_id
            
        except Exception as e:
            logger.error(f"Failed to check and split node {node_id}: {e}")
            raise
    
    async def get_chain(self, node_id: str) -> NodeChain:
        """
        Get the full continuation chain for a node.
        
        Args:
            node_id: ID of any node in the chain
            
        Returns:
            NodeChain object containing the root node ID and all nodes in the chain
        """
        try:
            # Find the root node (the one without continuation_of)
            root_node_id = await self._get_root_node(node_id)
            
            # Get all nodes in the chain
            chain_nodes = await self._get_continuation_chain(root_node_id)
            
            return NodeChain(
                root_node_id=root_node_id,
                nodes=chain_nodes
            )
            
        except Exception as e:
            logger.error(f"Failed to get continuation chain for node {node_id}: {e}")
            raise
    
    async def get_active_node(self, node_id: str) -> Dict[str, Any]:
        """
        Get the active (latest) node in a continuation chain.
        
        Args:
            node_id: ID of any node in the chain
            
        Returns:
            The active node in the chain
        """
        try:
            # Get the chain
            chain = await self.get_chain(node_id)
            
            # Return the last node in the chain (the active one)
            if chain.nodes:
                return chain.nodes[-1]
            
            # If no chain, return the original node
            return await self._get_node(node_id)
            
        except Exception as e:
            logger.error(f"Failed to get active node for {node_id}: {e}")
            raise
    
    async def _count_node_tokens(self, node_id: str) -> int:
        """
        Count the tokens in a node's context.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Token count
        """
        # In a real implementation, this would use a tokenizer service
        # For now, we'll simulate token counting
        
        try:
            node = await self._get_node(node_id)
            if not node:
                return 0
            
            # Simulate counting tokens in the context window
            # In a real implementation, you would use a tokenizer like tiktoken
            context_window = node.get("context_window", "")
            
            # Simple approximation: 1 token ≈ 4 characters
            # This is a very rough estimate and should be replaced with actual tokenization
            return len(context_window) // 4
            
        except Exception as e:
            logger.warning(f"Failed to count tokens for node {node_id}, returning 0: {e}")
            return 0
    
    async def _count_text_tokens(self, text: str) -> int:
        """
        Count the tokens in a text string.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Token count
        """
        # Simple approximation: 1 token ≈ 4 characters
        # This is a very rough estimate and should be replaced with actual tokenization
        return len(text) // 4
    
    async def _get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by ID.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Node data or None if not found
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, context_window, parent_node, child_nodes,
                           llm_model_used, node_type, status, created_at, updated_at,
                           continuation_of, token_count
                    FROM nodes 
                    WHERE id = %s
                    """, (node_id,)
                )
                
                row = cur.fetchone()
                if not row:
                    return None
                
            return dict(row)
            
        except Exception as e:
            logger.error(f"Failed to get node {node_id}: {e}")
            raise
    
    async def _get_root_node(self, node_id: str) -> str:
        """
        Get the root node of a continuation chain.
        
        Args:
            node_id: ID of any node in the chain
            
        Returns:
            ID of the root node
        """
        try:
            current_id = node_id
            
            # Traverse up the continuation chain to find the root
            while True:
                with self._conn.cursor() as cur:
                    cur.execute("""
                        SELECT continuation_of FROM nodes WHERE id = %s
                        """, (current_id,)
                    )
                    
                    row = cur.fetchone()
                    if not row or not row["continuation_of"]:
                        # We've found the root
                        return current_id
                    
                    current_id = row["continuation_of"]
            
        except Exception as e:
            logger.error(f"Failed to get root node for {node_id}: {e}")
            raise
    
    async def _get_continuation_chain(self, root_node_id: str) -> List[Dict[str, Any]]:
        """
        Get all nodes in a continuation chain.
        
        Args:
            root_node_id: ID of the root node
            
        Returns:
            List of nodes in chronological order
        """
        try:
            nodes = []
            current_id = root_node_id
            
            # Add the root node first
            root_node = await self._get_node(root_node_id)
            if root_node:
                nodes.append(root_node)
            
            # Traverse down the continuation chain
            while current_id:
                with self._conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, name, context_window, parent_node, child_nodes,
                               llm_model_used, node_type, status, created_at, updated_at,
                               continuation_of, token_count
                        FROM nodes 
                        WHERE continuation_of = %s
                        ORDER BY created_at ASC
                        """, (current_id,)
                    )
                    
                    row = cur.fetchone()
                    if not row:
                        # No more continuations
                        break
                    
                    node_data = dict(row)
                    nodes.append(node_data)
                    current_id = node_data["id"]
            
            return nodes
            
        except Exception as e:
            logger.error(f"Failed to get continuation chain for root {root_node_id}: {e}")
            raise
    
    async def _create_continuation_node(self, parent_node: Dict[str, Any], initial_text: str) -> str:
        """
        Create a continuation node.
        
        Args:
            parent_node: The parent node data
            initial_text: Initial text for the continuation node
            
        Returns:
            ID of the created continuation node
        """
        try:
            continuation_id = str(uuid.uuid4())
            
            # Create a new node with continuation_of pointing to parent
            with self._conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO nodes (
                        id, name, context_window, parent_node, child_nodes,
                        llm_model_used, node_type, status, continuation_of
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        continuation_id,
                        f"{parent_node['name']}-cont-{continuation_id[:8]}",
                        initial_text,  # Initial context is just the new message
                        parent_node.get("parent_node"),
                        '[]',  # Empty child nodes initially
                        parent_node.get("llm_model_used", "ollama"),
                        "continuation",  # Node type
                        "active",  # Status
                        parent_node["id"]  # continuation_of points to parent
                    )
                )
            
            self._conn.commit()
            
            # Update the parent node's child_nodes to include this continuation
            await self._add_child_to_parent(parent_node["id"], continuation_id)
            
            return continuation_id
            
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Failed to create continuation node: {e}")
            raise
    
    async def _add_child_to_parent(self, parent_id: str, child_id: str) -> None:
        """
        Add a child node to a parent's child_nodes list.
        
        Args:
            parent_id: ID of the parent node
            child_id: ID of the child node
        """
        try:
            with self._conn.cursor() as cur:
                # Get current child_nodes
                cur.execute("SELECT child_nodes FROM nodes WHERE id = %s", (parent_id,))
                row = cur.fetchone()
                
                if row:
                    import json
                    child_nodes = row["child_nodes"] or []
                    if isinstance(child_nodes, str):
                        child_nodes = json.loads(child_nodes) if child_nodes else []
                    
                    # Add the new child if not already present
                    if child_id not in child_nodes:
                        child_nodes.append(child_id)
                        
                        # Update the parent
                        cur.execute("""
                            UPDATE nodes SET child_nodes = %s WHERE id = %s
                            """, (json.dumps(child_nodes), parent_id)
                        )
                        
                        self._conn.commit()
            
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Failed to add child {child_id} to parent {parent_id}: {e}")
            raise
    
    async def _archive_node(self, node_id: str) -> None:
        """
        Mark a node as archived.
        
        Args:
            node_id: ID of the node to archive
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    UPDATE nodes SET status = 'archived' WHERE id = %s
                    """, (node_id,)
                )
            
            self._conn.commit()
            logger.info(f"Archived node {node_id}")
            
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Failed to archive node {node_id}: {e}")
            raise
    
    def close(self) -> None:
        """Close the database connection."""
        try:
            self._conn.close()
        except Exception:
            pass


def make_continuation_service_from_env() -> ContinuationService:
    """
    Factory function to create a ContinuationService from environment variables.
    """
    import os
    
    dsn = os.getenv("PG_DSN") or os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("PG_DSN or DATABASE_URL must be set")
    
    cfg = ContinuationConfig(
        pg_dsn=dsn,
        default_token_limit=int(os.getenv("CONTINUATION_TOKEN_LIMIT", "2000000")),
        min_tokens_to_keep=int(os.getenv("CONTINUATION_MIN_TOKENS", "100000"))
    )
    
    return ContinuationService(cfg)
