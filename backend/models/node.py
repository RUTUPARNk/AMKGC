from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

Base = declarative_base()

class Node(Base):
    __tablename__ = "nodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    context_window = Column(Text, nullable=False)
    parent_node = Column(UUID(as_uuid=True), nullable=True)
    child_nodes = Column(JSON, nullable=True)
    llm_model_used = Column(String, default='ollama')
    node_type = Column(String, default='general')
    status = Column(String, default='active')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __init__(self, name: str, context_window: str, **kwargs):
        self.name = name
        self.context_window = context_window
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'context_window': self.context_window,
            'parent_node': str(self.parent_node) if self.parent_node else None,
            'child_nodes': self.child_nodes or [],
            'llm_model_used': self.llm_model_used,
            'node_type': self.node_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_context_as_json(self) -> Dict[str, Any]:
        """Parse context_window as JSON"""
        try:
            return json.loads(self.context_window)
        except (json.JSONDecodeError, TypeError):
            return {"type": "text", "content": self.context_window}
    
    def set_context_from_json(self, context: Dict[str, Any]) -> None:
        """Set context_window from JSON"""
        self.context_window = json.dumps(context, indent=2)
    
    def add_child_node(self, child_id: str) -> None:
        """Add a child node ID to child_nodes"""
        if not self.child_nodes:
            self.child_nodes = []
        if isinstance(self.child_nodes, str):
            self.child_nodes = json.loads(self.child_nodes)
        if child_id not in self.child_nodes:
            self.child_nodes.append(child_id)
    
    def remove_child_node(self, child_id: str) -> None:
        """Remove a child node ID from child_nodes"""
        if self.child_nodes and child_id in self.child_nodes:
            self.child_nodes.remove(child_id)
    
    def is_conflicting(self) -> bool:
        """Check if node has conflicts"""
        return self.status == 'conflicting'
    
    def is_resolved(self) -> bool:
        """Check if node is resolved"""
        return self.status == 'resolved'
    
    def mark_as_conflicting(self) -> None:
        """Mark node as having conflicts"""
        self.status = 'conflicting'
    
    def mark_as_resolved(self) -> None:
        """Mark node as resolved"""
        self.status = 'resolved'
    
    def __repr__(self):
        return f"<Node(id={self.id}, name='{self.name}', type='{self.node_type}')>" 