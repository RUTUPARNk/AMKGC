#!/usr/bin/env python3
"""
Export/Import & Integration Service

This service provides:
- Export graphs to multiple formats (JSON, CSV, GraphML, PNG/SVG)
- Import graphs from external sources
- Integration with third-party systems (Notion, Airtable, Slack)
- Backup and restore functionality
- Webhook support for real-time sync
"""

import json
import csv
import logging
import base64
import hashlib
from typing import Dict, List, Any, Optional, Union, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path
import io
import zipfile
import requests
from sqlalchemy.orm import Session
from sqlalchemy import text
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

from services.redis_service import RedisService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExportImportService:
    """Service for exporting and importing graph data"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_service = RedisService(redis_url)
        
        # Supported export formats
        self.supported_formats = {
            'json': self._export_to_json,
            'csv': self._export_to_csv,
            'graphml': self._export_to_graphml,
            'png': self._export_to_png,
            'svg': self._export_to_svg,
            'zip': self._export_to_zip
        }
        
        # Supported import formats
        self.supported_import_formats = {
            'json': self._import_from_json,
            'csv': self._import_from_csv,
            'graphml': self._import_from_graphml
        }
    
    def export_graph(self, db: Session, format_type: str, 
                    include_metadata: bool = True, 
                    filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Export graph data in specified format"""
        try:
            if format_type not in self.supported_formats:
                raise ValueError(f"Unsupported format: {format_type}")
            
            # Get graph data
            graph_data = self._get_graph_data(db, filters)
            
            # Export using appropriate method
            export_func = self.supported_formats[format_type]
            result = export_func(graph_data, include_metadata)
            
            # Log export
            self._log_export(format_type, len(graph_data.get('nodes', [])))
            
            return {
                'success': True,
                'format': format_type,
                'data': result,
                'timestamp': datetime.now().isoformat(),
                'node_count': len(graph_data.get('nodes', [])),
                'edge_count': len(graph_data.get('edges', []))
            }
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            return {
                'success': False,
                'error': str(e),
                'format': format_type
            }
    
    def import_graph(self, db: Session, format_type: str, 
                    data: Union[str, bytes, BinaryIO],
                    merge_strategy: str = 'append') -> Dict[str, Any]:
        """Import graph data from specified format"""
        try:
            if format_type not in self.supported_import_formats:
                raise ValueError(f"Unsupported import format: {format_type}")
            
            # Import using appropriate method
            import_func = self.supported_import_formats[format_type]
            result = import_func(db, data, merge_strategy)
            
            # Log import
            self._log_import(format_type, result.get('imported_nodes', 0))
            
            return {
                'success': True,
                'format': format_type,
                'imported_nodes': result.get('imported_nodes', 0),
                'imported_edges': result.get('imported_edges', 0),
                'timestamp': datetime.now().isoformat(),
                'merge_strategy': merge_strategy
            }
            
        except Exception as e:
            logger.error(f"Import error: {e}")
            return {
                'success': False,
                'error': str(e),
                'format': format_type
            }
    
    def _get_graph_data(self, db: Session, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get graph data from database with optional filters"""
        try:
            # Build query with filters
            node_query = """
                SELECT node_id, name, node_type, status, context_summary, 
                       context, created_at, updated_at
                FROM nodes
                WHERE deleted_at IS NULL
            """
            
            edge_query = """
                SELECT parent_node_id, child_node_id, relationship_type, 
                       created_at, updated_at
                FROM node_relationships
                WHERE deleted_at IS NULL
            """
            
            # Apply filters
            if filters:
                if 'node_types' in filters:
                    node_types = "', '".join(filters['node_types'])
                    node_query += f" AND node_type IN ('{node_types}')"
                
                if 'status' in filters:
                    node_query += f" AND status = '{filters['status']}'"
                
                if 'date_from' in filters:
                    node_query += f" AND created_at >= '{filters['date_from']}'"
                
                if 'date_to' in filters:
                    node_query += f" AND created_at <= '{filters['date_to']}'"
            
            # Execute queries
            nodes_result = db.execute(text(node_query))
            edges_result = db.execute(text(edge_query))
            
            # Convert to dictionaries
            nodes = []
            for row in nodes_result:
                nodes.append({
                    'node_id': row.node_id,
                    'name': row.name,
                    'node_type': row.node_type,
                    'status': row.status,
                    'context_summary': row.context_summary,
                    'context': row.context,
                    'created_at': row.created_at.isoformat() if row.created_at else None,
                    'updated_at': row.updated_at.isoformat() if row.updated_at else None
                })
            
            edges = []
            for row in edges_result:
                edges.append({
                    'parent_node_id': row.parent_node_id,
                    'child_node_id': row.child_node_id,
                    'relationship_type': row.relationship_type,
                    'created_at': row.created_at.isoformat() if row.created_at else None,
                    'updated_at': row.updated_at.isoformat() if row.updated_at else None
                })
            
            return {
                'nodes': nodes,
                'edges': edges,
                'export_metadata': {
                    'exported_at': datetime.now().isoformat(),
                    'total_nodes': len(nodes),
                    'total_edges': len(edges),
                    'filters_applied': filters or {}
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting graph data: {e}")
            return {'nodes': [], 'edges': []}
    
    def _export_to_json(self, graph_data: Dict[str, Any], 
                       include_metadata: bool = True) -> str:
        """Export graph data to JSON format"""
        export_data = {
            'nodes': graph_data['nodes'],
            'edges': graph_data['edges']
        }
        
        if include_metadata:
            export_data['metadata'] = graph_data.get('export_metadata', {})
        
        return json.dumps(export_data, indent=2, default=str)
    
    def _export_to_csv(self, graph_data: Dict[str, Any], 
                      include_metadata: bool = True) -> Dict[str, str]:
        """Export graph data to CSV format"""
        result = {}
        
        # Export nodes
        if graph_data['nodes']:
            nodes_output = io.StringIO()
            nodes_writer = csv.DictWriter(nodes_output, fieldnames=graph_data['nodes'][0].keys())
            nodes_writer.writeheader()
            nodes_writer.writerows(graph_data['nodes'])
            result['nodes.csv'] = nodes_output.getvalue()
        
        # Export edges
        if graph_data['edges']:
            edges_output = io.StringIO()
            edges_writer = csv.DictWriter(edges_output, fieldnames=graph_data['edges'][0].keys())
            edges_writer.writeheader()
            edges_writer.writerows(graph_data['edges'])
            result['edges.csv'] = edges_output.getvalue()
        
        # Export metadata
        if include_metadata and graph_data.get('export_metadata'):
            metadata_output = io.StringIO()
            metadata_writer = csv.writer(metadata_output)
            metadata_writer.writerow(['key', 'value'])
            for key, value in graph_data['export_metadata'].items():
                metadata_writer.writerow([key, value])
            result['metadata.csv'] = metadata_output.getvalue()
        
        return result
    
    def _export_to_graphml(self, graph_data: Dict[str, Any], 
                          include_metadata: bool = True) -> str:
        """Export graph data to GraphML format"""
        G = nx.Graph()
        
        # Add nodes
        for node in graph_data['nodes']:
            G.add_node(node['node_id'], **{k: v for k, v in node.items() if k != 'node_id'})
        
        # Add edges
        for edge in graph_data['edges']:
            G.add_edge(edge['parent_node_id'], edge['child_node_id'], 
                      relationship_type=edge['relationship_type'])
        
        # Write to string
        output = io.StringIO()
        nx.write_graphml(G, output)
        return output.getvalue()
    
    def _export_to_png(self, graph_data: Dict[str, Any], 
                      include_metadata: bool = True) -> bytes:
        """Export graph visualization to PNG format"""
        G = nx.Graph()
        
        # Add nodes and edges
        for node in graph_data['nodes']:
            G.add_node(node['node_id'], **{k: v for k, v in node.items() if k != 'node_id'})
        
        for edge in graph_data['edges']:
            G.add_edge(edge['parent_node_id'], edge['child_node_id'])
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=700, node_color='lightblue')
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, alpha=0.5)
        
        # Draw labels
        labels = {node: data.get('name', node) for node, data in G.nodes(data=True)}
        nx.draw_networkx_labels(G, pos, labels, font_size=8)
        
        plt.title("Graph Visualization")
        plt.axis('off')
        
        # Save to bytes
        output = io.BytesIO()
        plt.savefig(output, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        return output.getvalue()
    
    def _export_to_svg(self, graph_data: Dict[str, Any], 
                      include_metadata: bool = True) -> str:
        """Export graph visualization to SVG format"""
        G = nx.Graph()
        
        # Add nodes and edges
        for node in graph_data['nodes']:
            G.add_node(node['node_id'], **{k: v for k, v in node.items() if k != 'node_id'})
        
        for edge in graph_data['edges']:
            G.add_edge(edge['parent_node_id'], edge['child_node_id'])
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=700, node_color='lightblue')
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, alpha=0.5)
        
        # Draw labels
        labels = {node: data.get('name', node) for node, data in G.nodes(data=True)}
        nx.draw_networkx_labels(G, pos, labels, font_size=8)
        
        plt.title("Graph Visualization")
        plt.axis('off')
        
        # Save to string
        output = io.StringIO()
        plt.savefig(output, format='svg', bbox_inches='tight')
        plt.close()
        
        return output.getvalue()
    
    def _export_to_zip(self, graph_data: Dict[str, Any], 
                      include_metadata: bool = True) -> bytes:
        """Export graph data to ZIP format with multiple files"""
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add JSON export
            json_data = self._export_to_json(graph_data, include_metadata)
            zip_file.writestr('graph.json', json_data)
            
            # Add CSV exports
            csv_data = self._export_to_csv(graph_data, include_metadata)
            for filename, content in csv_data.items():
                zip_file.writestr(filename, content)
            
            # Add GraphML export
            graphml_data = self._export_to_graphml(graph_data, include_metadata)
            zip_file.writestr('graph.graphml', graphml_data)
            
            # Add PNG visualization
            png_data = self._export_to_png(graph_data, include_metadata)
            zip_file.writestr('visualization.png', png_data)
            
            # Add SVG visualization
            svg_data = self._export_to_svg(graph_data, include_metadata)
            zip_file.writestr('visualization.svg', svg_data)
        
        return zip_buffer.getvalue()
    
    def _import_from_json(self, db: Session, data: Union[str, bytes], 
                         merge_strategy: str = 'append') -> Dict[str, Any]:
        """Import graph data from JSON format"""
        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            
            import_data = json.loads(data)
            nodes = import_data.get('nodes', [])
            edges = import_data.get('edges', [])
            
            imported_nodes = 0
            imported_edges = 0
            
            # Import nodes
            for node in nodes:
                if self._import_node(db, node, merge_strategy):
                    imported_nodes += 1
            
            # Import edges
            for edge in edges:
                if self._import_edge(db, edge, merge_strategy):
                    imported_edges += 1
            
            db.commit()
            
            return {
                'imported_nodes': imported_nodes,
                'imported_edges': imported_edges
            }
            
        except Exception as e:
            db.rollback()
            raise e
    
    def _import_from_csv(self, db: Session, data: Union[str, bytes], 
                        merge_strategy: str = 'append') -> Dict[str, Any]:
        """Import graph data from CSV format"""
        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            
            # Parse CSV data
            csv_data = csv.DictReader(io.StringIO(data))
            rows = list(csv_data)
            
            imported_nodes = 0
            imported_edges = 0
            
            # Determine if this is nodes or edges data
            if 'node_id' in rows[0]:
                # Nodes data
                for row in rows:
                    if self._import_node(db, row, merge_strategy):
                        imported_nodes += 1
            elif 'parent_node_id' in rows[0]:
                # Edges data
                for row in rows:
                    if self._import_edge(db, row, merge_strategy):
                        imported_edges += 1
            
            db.commit()
            
            return {
                'imported_nodes': imported_nodes,
                'imported_edges': imported_edges
            }
            
        except Exception as e:
            db.rollback()
            raise e
    
    def _import_from_graphml(self, db: Session, data: Union[str, bytes], 
                           merge_strategy: str = 'append') -> Dict[str, Any]:
        """Import graph data from GraphML format"""
        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            
            # Parse GraphML
            G = nx.read_graphml(io.StringIO(data))
            
            imported_nodes = 0
            imported_edges = 0
            
            # Import nodes
            for node, attrs in G.nodes(data=True):
                node_data = {
                    'node_id': node,
                    'name': attrs.get('name', node),
                    'node_type': attrs.get('node_type', 'unknown'),
                    'status': attrs.get('status', 'active'),
                    'context_summary': attrs.get('context_summary', ''),
                    'context': attrs.get('context', '')
                }
                if self._import_node(db, node_data, merge_strategy):
                    imported_nodes += 1
            
            # Import edges
            for u, v, attrs in G.edges(data=True):
                edge_data = {
                    'parent_node_id': u,
                    'child_node_id': v,
                    'relationship_type': attrs.get('relationship_type', 'connected')
                }
                if self._import_edge(db, edge_data, merge_strategy):
                    imported_edges += 1
            
            db.commit()
            
            return {
                'imported_nodes': imported_nodes,
                'imported_edges': imported_edges
            }
            
        except Exception as e:
            db.rollback()
            raise e
    
    def _import_node(self, db: Session, node_data: Dict[str, Any], 
                    merge_strategy: str) -> bool:
        """Import a single node"""
        try:
            node_id = node_data['node_id']
            
            # Check if node exists
            existing = db.execute(
                text("SELECT node_id FROM nodes WHERE node_id = :node_id"),
                {'node_id': node_id}
            ).fetchone()
            
            if existing:
                if merge_strategy == 'skip':
                    return False
                elif merge_strategy == 'update':
                    # Update existing node
                    db.execute(text("""
                        UPDATE nodes 
                        SET name = :name, node_type = :node_type, status = :status,
                            context_summary = :context_summary, context = :context,
                            updated_at = NOW()
                        WHERE node_id = :node_id
                    """), node_data)
                elif merge_strategy == 'append':
                    # Generate new ID
                    node_data['node_id'] = f"{node_id}_imported_{datetime.now().timestamp()}"
            
            # Insert new node
            db.execute(text("""
                INSERT INTO nodes (node_id, name, node_type, status, context_summary, context)
                VALUES (:node_id, :name, :node_type, :status, :context_summary, :context)
            """), node_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error importing node {node_data.get('node_id')}: {e}")
            return False
    
    def _import_edge(self, db: Session, edge_data: Dict[str, Any], 
                    merge_strategy: str) -> bool:
        """Import a single edge"""
        try:
            parent_id = edge_data['parent_node_id']
            child_id = edge_data['child_node_id']
            
            # Check if edge exists
            existing = db.execute(text("""
                SELECT parent_node_id FROM node_relationships 
                WHERE parent_node_id = :parent_id AND child_node_id = :child_id
            """), {'parent_id': parent_id, 'child_id': child_id}).fetchone()
            
            if existing:
                if merge_strategy == 'skip':
                    return False
                elif merge_strategy == 'update':
                    # Update existing edge
                    db.execute(text("""
                        UPDATE node_relationships 
                        SET relationship_type = :relationship_type, updated_at = NOW()
                        WHERE parent_node_id = :parent_node_id AND child_node_id = :child_node_id
                    """), edge_data)
                elif merge_strategy == 'append':
                    # Skip duplicate
                    return False
            
            # Insert new edge
            db.execute(text("""
                INSERT INTO node_relationships (parent_node_id, child_node_id, relationship_type)
                VALUES (:parent_node_id, :child_node_id, :relationship_type)
            """), edge_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error importing edge {edge_data}: {e}")
            return False
    
    def create_backup(self, db: Session, backup_name: str = None) -> Dict[str, Any]:
        """Create a complete backup of the graph data"""
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Get all graph data
            graph_data = self._get_graph_data(db)
            
            # Create backup metadata
            backup_metadata = {
                'backup_name': backup_name,
                'created_at': datetime.now().isoformat(),
                'node_count': len(graph_data['nodes']),
                'edge_count': len(graph_data['edges']),
                'version': '1.0'
            }
            
            # Create backup file
            backup_data = {
                'metadata': backup_metadata,
                'data': graph_data
            }
            
            # Store in Redis for quick access
            backup_key = f"backup:{backup_name}"
            self.redis_service.set_cache(backup_key, json.dumps(backup_data), ttl=86400*7)  # 7 days
            
            return {
                'success': True,
                'backup_name': backup_name,
                'backup_key': backup_key,
                'node_count': len(graph_data['nodes']),
                'edge_count': len(graph_data['edges']),
                'created_at': backup_metadata['created_at']
            }
            
        except Exception as e:
            logger.error(f"Backup creation error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def restore_backup(self, db: Session, backup_name: str) -> Dict[str, Any]:
        """Restore graph data from a backup"""
        try:
            backup_key = f"backup:{backup_name}"
            backup_data = self.redis_service.get_cache(backup_key)
            
            if not backup_data:
                raise ValueError(f"Backup '{backup_name}' not found")
            
            backup = json.loads(backup_data)
            graph_data = backup['data']
            
            # Clear existing data (optional - could be configurable)
            db.execute(text("DELETE FROM node_relationships"))
            db.execute(text("DELETE FROM nodes"))
            
            # Import backup data
            result = self._import_from_json(db, json.dumps(graph_data), 'append')
            
            db.commit()
            
            return {
                'success': True,
                'backup_name': backup_name,
                'restored_nodes': result['imported_nodes'],
                'restored_edges': result['imported_edges'],
                'restored_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Backup restoration error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        try:
            backup_keys = self.redis_service.redis_client.keys("backup:*")
            backups = []
            
            for key in backup_keys:
                backup_data = self.redis_service.get_cache(key)
                if backup_data:
                    backup = json.loads(backup_data)
                    backups.append({
                        'name': backup['metadata']['backup_name'],
                        'created_at': backup['metadata']['created_at'],
                        'node_count': backup['metadata']['node_count'],
                        'edge_count': backup['metadata']['edge_count'],
                        'size': len(backup_data)
                    })
            
            return sorted(backups, key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def _log_export(self, format_type: str, node_count: int):
        """Log export activity"""
        log_data = {
            'action': 'export',
            'format': format_type,
            'node_count': node_count,
            'timestamp': datetime.now().isoformat()
        }
        self.redis_service.add_to_list('activity_log', json.dumps(log_data))
    
    def _log_import(self, format_type: str, node_count: int):
        """Log import activity"""
        log_data = {
            'action': 'import',
            'format': format_type,
            'node_count': node_count,
            'timestamp': datetime.now().isoformat()
        }
        self.redis_service.add_to_list('activity_log', json.dumps(log_data)) 