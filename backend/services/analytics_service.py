#!/usr/bin/env python3
"""
AI-Driven Analytics & Recommendations Service

This service provides:
- Automated pattern detection in graph data
- Predictive analytics for graph outcomes
- Natural language query processing
- Smart suggestions and optimizations
- Graph neural network integration
"""

import json
import logging
import numpy as np
import networkx as nx
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, Counter
import redis
from sqlalchemy.orm import Session
from sqlalchemy import text

from services.llm_service import LLMService
from services.redis_service import RedisService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GraphPattern:
    """Represents a detected pattern in the graph"""
    pattern_type: str
    description: str
    confidence: float
    nodes_involved: List[str]
    edges_involved: List[Tuple[str, str]]
    metadata: Dict[str, Any]


@dataclass
class Prediction:
    """Represents a prediction about graph outcomes"""
    prediction_type: str
    description: str
    confidence: float
    affected_nodes: List[str]
    expected_outcome: str
    recommendations: List[str]


@dataclass
class QueryResult:
    """Represents the result of a natural language query"""
    query: str
    result_type: str
    data: Any
    confidence: float
    explanation: str
    suggestions: List[str]


class AnalyticsService:
    """Service for AI-driven analytics and recommendations"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.llm_service = LLMService(redis_url)
        self.redis_service = RedisService(redis_url)
        
        # Cache TTL for analytics results
        self.cache_ttl = 3600  # 1 hour
        
        # Pattern detection thresholds
        self.pattern_thresholds = {
            'frequency': 0.1,  # 10% of total nodes
            'centrality': 0.7,  # 70th percentile
            'clustering': 0.3,  # 30% clustering coefficient
            'connectivity': 0.5  # 50% connectivity
        }
    
    def _get_cache_key(self, operation: str, **kwargs) -> str:
        """Generate cache key for analytics results"""
        key_parts = ['analytics', operation]
        for k, v in sorted(kwargs.items()):
            key_parts.extend([k, str(v)])
        return ':'.join(key_parts)
    
    def _cache_get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def _cache_set(self, key: str, value: str, ttl: int = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or self.cache_ttl
            return self.redis_client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def build_graph_from_database(self, db: Session) -> nx.Graph:
        """Build NetworkX graph from database data"""
        try:
            # Get nodes
            nodes_result = db.execute(text("""
                SELECT node_id, name, node_type, status, context_summary
                FROM nodes
                WHERE deleted_at IS NULL
            """))
            
            # Get relationships
            edges_result = db.execute(text("""
                SELECT parent_node_id, child_node_id, relationship_type
                FROM node_relationships
                WHERE deleted_at IS NULL
            """))
            
            # Build graph
            G = nx.Graph()
            
            # Add nodes
            for row in nodes_result:
                G.add_node(row.node_id, 
                          name=row.name,
                          type=row.node_type,
                          status=row.status,
                          context=row.context_summary)
            
            # Add edges
            for row in edges_result:
                G.add_edge(row.parent_node_id, row.child_node_id,
                          relationship_type=row.relationship_type)
            
            logger.info(f"Built graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
            return G
            
        except Exception as e:
            logger.error(f"Error building graph: {e}")
            return nx.Graph()
    
    def detect_patterns(self, db: Session) -> List[GraphPattern]:
        """Detect patterns in the graph using AI and graph analysis"""
        cache_key = self._get_cache_key('patterns')
        cached_result = self._cache_get(cache_key)
        
        if cached_result:
            patterns_data = json.loads(cached_result)
            return [GraphPattern(**pattern) for pattern in patterns_data]
        
        try:
            G = self.build_graph_from_database(db)
            if G.number_of_nodes() == 0:
                return []
            
            patterns = []
            
            # 1. Centrality patterns
            centrality_patterns = self._detect_centrality_patterns(G)
            patterns.extend(centrality_patterns)
            
            # 2. Clustering patterns
            clustering_patterns = self._detect_clustering_patterns(G)
            patterns.extend(clustering_patterns)
            
            # 3. Connectivity patterns
            connectivity_patterns = self._detect_connectivity_patterns(G)
            patterns.extend(connectivity_patterns)
            
            # 4. Node type patterns
            type_patterns = self._detect_node_type_patterns(G)
            patterns.extend(type_patterns)
            
            # 5. AI-driven pattern analysis
            ai_patterns = self._detect_ai_patterns(G, db)
            patterns.extend(ai_patterns)
            
            # Cache results
            patterns_data = [pattern.__dict__ for pattern in patterns]
            self._cache_set(cache_key, json.dumps(patterns_data))
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return []
    
    def _detect_centrality_patterns(self, G: nx.Graph) -> List[GraphPattern]:
        """Detect centrality-based patterns"""
        patterns = []
        
        try:
            # Calculate centrality measures
            degree_centrality = nx.degree_centrality(G)
            betweenness_centrality = nx.betweenness_centrality(G)
            closeness_centrality = nx.closeness_centrality(G)
            
            # Find highly central nodes
            high_degree_nodes = [node for node, centrality in degree_centrality.items() 
                               if centrality > self.pattern_thresholds['centrality']]
            
            if high_degree_nodes:
                patterns.append(GraphPattern(
                    pattern_type="high_centrality",
                    description=f"Found {len(high_degree_nodes)} highly connected nodes",
                    confidence=0.8,
                    nodes_involved=high_degree_nodes,
                    edges_involved=[],
                    metadata={
                        'centrality_type': 'degree',
                        'threshold': self.pattern_thresholds['centrality'],
                        'centrality_values': {node: degree_centrality[node] for node in high_degree_nodes}
                    }
                ))
            
            # Find bridge nodes (high betweenness)
            bridge_nodes = [node for node, centrality in betweenness_centrality.items() 
                          if centrality > self.pattern_thresholds['centrality']]
            
            if bridge_nodes:
                patterns.append(GraphPattern(
                    pattern_type="bridge_nodes",
                    description=f"Found {len(bridge_nodes)} bridge nodes connecting different parts of the graph",
                    confidence=0.7,
                    nodes_involved=bridge_nodes,
                    edges_involved=[],
                    metadata={
                        'centrality_type': 'betweenness',
                        'threshold': self.pattern_thresholds['centrality'],
                        'centrality_values': {node: betweenness_centrality[node] for node in bridge_nodes}
                    }
                ))
                
        except Exception as e:
            logger.error(f"Error detecting centrality patterns: {e}")
        
        return patterns
    
    def _detect_clustering_patterns(self, G: nx.Graph) -> List[GraphPattern]:
        """Detect clustering and community patterns"""
        patterns = []
        
        try:
            # Calculate clustering coefficient
            clustering_coeff = nx.average_clustering(G)
            
            if clustering_coeff > self.pattern_thresholds['clustering']:
                patterns.append(GraphPattern(
                    pattern_type="high_clustering",
                    description=f"Graph shows high clustering (coefficient: {clustering_coeff:.3f})",
                    confidence=0.6,
                    nodes_involved=list(G.nodes()),
                    edges_involved=list(G.edges()),
                    metadata={'clustering_coefficient': clustering_coeff}
                ))
            
            # Detect communities
            communities = list(nx.community.greedy_modularity_communities(G))
            
            if len(communities) > 1:
                patterns.append(GraphPattern(
                    pattern_type="communities",
                    description=f"Graph contains {len(communities)} distinct communities",
                    confidence=0.7,
                    nodes_involved=list(G.nodes()),
                    edges_involved=list(G.edges()),
                    metadata={
                        'num_communities': len(communities),
                        'community_sizes': [len(comm) for comm in communities]
                    }
                ))
                
        except Exception as e:
            logger.error(f"Error detecting clustering patterns: {e}")
        
        return patterns
    
    def _detect_connectivity_patterns(self, G: nx.Graph) -> List[GraphPattern]:
        """Detect connectivity and path patterns"""
        patterns = []
        
        try:
            # Check connectivity
            if nx.is_connected(G):
                patterns.append(GraphPattern(
                    pattern_type="fully_connected",
                    description="Graph is fully connected",
                    confidence=0.9,
                    nodes_involved=list(G.nodes()),
                    edges_involved=list(G.edges()),
                    metadata={'connectivity': 'full'}
                ))
            else:
                # Find connected components
                components = list(nx.connected_components(G))
                patterns.append(GraphPattern(
                    pattern_type="disconnected_components",
                    description=f"Graph has {len(components)} disconnected components",
                    confidence=0.8,
                    nodes_involved=list(G.nodes()),
                    edges_involved=list(G.edges()),
                    metadata={
                        'num_components': len(components),
                        'component_sizes': [len(comp) for comp in components]
                    }
                ))
            
            # Detect cycles
            cycles = list(nx.simple_cycles(G.to_directed()))
            if cycles:
                patterns.append(GraphPattern(
                    pattern_type="cycles",
                    description=f"Graph contains {len(cycles)} cycles",
                    confidence=0.7,
                    nodes_involved=list(set([node for cycle in cycles for node in cycle])),
                    edges_involved=[],
                    metadata={'num_cycles': len(cycles)}
                ))
                
        except Exception as e:
            logger.error(f"Error detecting connectivity patterns: {e}")
        
        return patterns
    
    def _detect_node_type_patterns(self, G: nx.Graph) -> List[GraphPattern]:
        """Detect patterns based on node types"""
        patterns = []
        
        try:
            # Group nodes by type
            type_groups = defaultdict(list)
            for node, attrs in G.nodes(data=True):
                node_type = attrs.get('type', 'unknown')
                type_groups[node_type].append(node)
            
            # Analyze type distributions
            for node_type, nodes in type_groups.items():
                if len(nodes) > G.number_of_nodes() * self.pattern_thresholds['frequency']:
                    patterns.append(GraphPattern(
                        pattern_type="type_concentration",
                        description=f"High concentration of {node_type} nodes ({len(nodes)} nodes)",
                        confidence=0.6,
                        nodes_involved=nodes,
                        edges_involved=[],
                        metadata={
                            'node_type': node_type,
                            'count': len(nodes),
                            'percentage': len(nodes) / G.number_of_nodes()
                        }
                    ))
            
            # Analyze connections between types
            type_connections = defaultdict(int)
            for u, v in G.edges():
                u_type = G.nodes[u].get('type', 'unknown')
                v_type = G.nodes[v].get('type', 'unknown')
                type_connections[(u_type, v_type)] += 1
            
            # Find strong type connections
            for (type1, type2), count in type_connections.items():
                if count > G.number_of_edges() * 0.1:  # 10% of edges
                    patterns.append(GraphPattern(
                        pattern_type="type_connections",
                        description=f"Strong connection between {type1} and {type2} nodes ({count} edges)",
                        confidence=0.7,
                        nodes_involved=[],
                        edges_involved=[],
                        metadata={
                            'type1': type1,
                            'type2': type2,
                            'connection_count': count
                        }
                    ))
                
        except Exception as e:
            logger.error(f"Error detecting node type patterns: {e}")
        
        return patterns
    
    def _detect_ai_patterns(self, G: nx.Graph, db: Session) -> List[GraphPattern]:
        """Use LLM to detect AI-driven patterns"""
        patterns = []
        
        try:
            # Prepare graph summary for LLM analysis
            graph_summary = self._prepare_graph_summary(G)
            
            # Generate AI analysis prompt
            prompt = f"""
            Analyze this graph structure and identify interesting patterns:
            
            {graph_summary}
            
            Look for:
            1. Unusual connection patterns
            2. Potential bottlenecks or single points of failure
            3. Clusters or communities that might benefit from reorganization
            4. Nodes that seem isolated or disconnected
            5. Potential optimization opportunities
            
            Return your analysis in JSON format with:
            - pattern_type: type of pattern detected
            - description: human-readable description
            - confidence: confidence level (0-1)
            - nodes_involved: list of relevant node IDs
            - recommendations: list of suggested actions
            """
            
            # Get LLM analysis
            result = self.llm_service.generate(prompt)
            
            if result.get('success'):
                try:
                    analysis = json.loads(result['content'])
                    if isinstance(analysis, list):
                        for pattern_data in analysis:
                            patterns.append(GraphPattern(
                                pattern_type=pattern_data.get('pattern_type', 'ai_detected'),
                                description=pattern_data.get('description', 'AI-detected pattern'),
                                confidence=pattern_data.get('confidence', 0.5),
                                nodes_involved=pattern_data.get('nodes_involved', []),
                                edges_involved=pattern_data.get('edges_involved', []),
                                metadata={
                                    'ai_generated': True,
                                    'recommendations': pattern_data.get('recommendations', [])
                                }
                            ))
                except json.JSONDecodeError:
                    logger.warning("Failed to parse AI analysis as JSON")
                    
        except Exception as e:
            logger.error(f"Error in AI pattern detection: {e}")
        
        return patterns
    
    def _prepare_graph_summary(self, G: nx.Graph) -> str:
        """Prepare a summary of the graph for LLM analysis"""
        summary_parts = []
        
        summary_parts.append(f"Graph Statistics:")
        summary_parts.append(f"- Nodes: {G.number_of_nodes()}")
        summary_parts.append(f"- Edges: {G.number_of_edges()}")
        
        # Node type distribution
        type_counts = Counter()
        for node, attrs in G.nodes(data=True):
            node_type = attrs.get('type', 'unknown')
            type_counts[node_type] += 1
        
        summary_parts.append(f"- Node types: {dict(type_counts)}")
        
        # Connectivity
        if nx.is_connected(G):
            summary_parts.append("- Graph is fully connected")
        else:
            components = list(nx.connected_components(G))
            summary_parts.append(f"- Graph has {len(components)} disconnected components")
        
        # Centrality
        if G.number_of_nodes() > 0:
            degree_centrality = nx.degree_centrality(G)
            avg_degree = sum(degree_centrality.values()) / len(degree_centrality)
            summary_parts.append(f"- Average degree centrality: {avg_degree:.3f}")
        
        # Sample nodes
        sample_nodes = list(G.nodes())[:5]
        summary_parts.append(f"- Sample nodes: {sample_nodes}")
        
        return "\n".join(summary_parts)
    
    def predict_outcomes(self, db: Session, scenario: str) -> List[Prediction]:
        """Predict outcomes based on graph structure and scenarios"""
        cache_key = self._get_cache_key('predictions', scenario=scenario)
        cached_result = self._cache_get(cache_key)
        
        if cached_result:
            predictions_data = json.loads(cached_result)
            return [Prediction(**pred) for pred in predictions_data]
        
        try:
            G = self.build_graph_from_database(db)
            if G.number_of_nodes() == 0:
                return []
            
            predictions = []
            
            # Generate prediction prompt
            graph_summary = self._prepare_graph_summary(G)
            
            prompt = f"""
            Based on this graph structure, predict what would happen if:
            {scenario}
            
            Graph Summary:
            {graph_summary}
            
            Consider:
            1. Impact on connectivity and flow
            2. Potential bottlenecks or improvements
            3. Risk assessment
            4. Recommended actions
            
            Return predictions in JSON format with:
            - prediction_type: type of prediction
            - description: what is predicted to happen
            - confidence: confidence level (0-1)
            - affected_nodes: list of nodes that would be affected
            - expected_outcome: brief description of expected outcome
            - recommendations: list of recommended actions
            """
            
            # Get LLM prediction
            result = self.llm_service.generate(prompt)
            
            if result.get('success'):
                try:
                    analysis = json.loads(result['content'])
                    if isinstance(analysis, list):
                        for pred_data in analysis:
                            predictions.append(Prediction(
                                prediction_type=pred_data.get('prediction_type', 'scenario_analysis'),
                                description=pred_data.get('description', 'Predicted outcome'),
                                confidence=pred_data.get('confidence', 0.5),
                                affected_nodes=pred_data.get('affected_nodes', []),
                                expected_outcome=pred_data.get('expected_outcome', ''),
                                recommendations=pred_data.get('recommendations', [])
                            ))
                except json.JSONDecodeError:
                    logger.warning("Failed to parse prediction as JSON")
            
            # Cache results
            predictions_data = [pred.__dict__ for pred in predictions]
            self._cache_set(cache_key, json.dumps(predictions_data))
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error making predictions: {e}")
            return []
    
    def process_natural_language_query(self, db: Session, query: str) -> QueryResult:
        """Process natural language queries about the graph"""
        cache_key = self._get_cache_key('nl_query', query=query)
        cached_result = self._cache_get(cache_key)
        
        if cached_result:
            result_data = json.loads(cached_result)
            return QueryResult(**result_data)
        
        try:
            G = self.build_graph_from_database(db)
            if G.number_of_nodes() == 0:
                return QueryResult(
                    query=query,
                    result_type="error",
                    data=None,
                    confidence=0.0,
                    explanation="No graph data available",
                    suggestions=[]
                )
            
            # Prepare graph data for query processing
            graph_data = self._prepare_graph_for_query(G)
            
            # Generate query processing prompt
            prompt = f"""
            Answer this question about the graph:
            "{query}"
            
            Graph Data:
            {graph_data}
            
            Provide your answer in JSON format with:
            - result_type: "data", "analysis", "suggestion", or "error"
            - data: the actual answer or data
            - confidence: confidence level (0-1)
            - explanation: brief explanation of your answer
            - suggestions: list of related questions or suggestions
            """
            
            # Get LLM response
            result = self.llm_service.generate(prompt)
            
            if result.get('success'):
                try:
                    response_data = json.loads(result['content'])
                    query_result = QueryResult(
                        query=query,
                        result_type=response_data.get('result_type', 'data'),
                        data=response_data.get('data'),
                        confidence=response_data.get('confidence', 0.5),
                        explanation=response_data.get('explanation', ''),
                        suggestions=response_data.get('suggestions', [])
                    )
                    
                    # Cache result
                    self._cache_set(cache_key, json.dumps(query_result.__dict__))
                    
                    return query_result
                    
                except json.JSONDecodeError:
                    logger.warning("Failed to parse query response as JSON")
            
            # Fallback response
            return QueryResult(
                query=query,
                result_type="error",
                data=None,
                confidence=0.0,
                explanation="Failed to process query",
                suggestions=["Try rephrasing your question", "Check if the graph has data"]
            )
            
        except Exception as e:
            logger.error(f"Error processing natural language query: {e}")
            return QueryResult(
                query=query,
                result_type="error",
                data=None,
                confidence=0.0,
                explanation=f"Error: {str(e)}",
                suggestions=[]
            )
    
    def _prepare_graph_for_query(self, G: nx.Graph) -> str:
        """Prepare graph data for natural language query processing"""
        data_parts = []
        
        # Basic stats
        data_parts.append(f"Total nodes: {G.number_of_nodes()}")
        data_parts.append(f"Total edges: {G.number_of_edges()}")
        
        # Node types
        type_counts = Counter()
        for node, attrs in G.nodes(data=True):
            node_type = attrs.get('type', 'unknown')
            type_counts[node_type] += 1
        
        data_parts.append(f"Node types: {dict(type_counts)}")
        
        # Node details
        data_parts.append("Node details:")
        for node, attrs in G.nodes(data=True):
            name = attrs.get('name', node)
            node_type = attrs.get('type', 'unknown')
            status = attrs.get('status', 'unknown')
            data_parts.append(f"  - {node}: {name} ({node_type}, {status})")
        
        # Edge details
        data_parts.append("Edge details:")
        for u, v, attrs in G.edges(data=True):
            relationship = attrs.get('relationship_type', 'connected')
            data_parts.append(f"  - {u} -> {v} ({relationship})")
        
        return "\n".join(data_parts)
    
    def get_smart_suggestions(self, db: Session) -> List[Dict[str, Any]]:
        """Generate smart suggestions for graph optimization"""
        cache_key = self._get_cache_key('suggestions')
        cached_result = self._cache_get(cache_key)
        
        if cached_result:
            return json.loads(cached_result)
        
        try:
            G = self.build_graph_from_database(db)
            if G.number_of_nodes() == 0:
                return []
            
            suggestions = []
            
            # Analyze graph for optimization opportunities
            graph_summary = self._prepare_graph_summary(G)
            
            prompt = f"""
            Analyze this graph and provide optimization suggestions:
            
            {graph_summary}
            
            Consider:
            1. Nodes that could be merged to reduce complexity
            2. Missing connections that would improve flow
            3. Potential bottlenecks or single points of failure
            4. Opportunities for better organization
            5. Performance improvements
            
            Return suggestions in JSON format with:
            - suggestion_type: type of suggestion
            - description: what the suggestion is about
            - priority: high/medium/low
            - impact: expected impact of the suggestion
            - actions: specific actions to take
            - affected_nodes: nodes that would be affected
            """
            
            # Get LLM suggestions
            result = self.llm_service.generate(prompt)
            
            if result.get('success'):
                try:
                    suggestions_data = json.loads(result['content'])
                    if isinstance(suggestions_data, list):
                        suggestions = suggestions_data
                except json.JSONDecodeError:
                    logger.warning("Failed to parse suggestions as JSON")
            
            # Cache suggestions
            self._cache_set(cache_key, json.dumps(suggestions))
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return []
    
    def get_analytics_summary(self, db: Session) -> Dict[str, Any]:
        """Get a comprehensive analytics summary"""
        try:
            G = self.build_graph_from_database(db)
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'graph_stats': {
                    'nodes': G.number_of_nodes(),
                    'edges': G.number_of_edges(),
                    'density': nx.density(G) if G.number_of_nodes() > 1 else 0,
                    'is_connected': nx.is_connected(G),
                    'components': len(list(nx.connected_components(G))),
                    'avg_clustering': nx.average_clustering(G) if G.number_of_nodes() > 2 else 0
                },
                'node_types': {},
                'centrality_stats': {},
                'recent_patterns': [],
                'top_suggestions': []
            }
            
            # Node type distribution
            type_counts = Counter()
            for node, attrs in G.nodes(data=True):
                node_type = attrs.get('type', 'unknown')
                type_counts[node_type] += 1
            summary['node_types'] = dict(type_counts)
            
            # Centrality statistics
            if G.number_of_nodes() > 0:
                degree_centrality = nx.degree_centrality(G)
                summary['centrality_stats'] = {
                    'avg_degree': sum(degree_centrality.values()) / len(degree_centrality),
                    'max_degree': max(degree_centrality.values()),
                    'min_degree': min(degree_centrality.values())
                }
            
            # Recent patterns (cached)
            patterns = self.detect_patterns(db)
            summary['recent_patterns'] = [
                {
                    'type': pattern.pattern_type,
                    'description': pattern.description,
                    'confidence': pattern.confidence
                }
                for pattern in patterns[:5]  # Top 5 patterns
            ]
            
            # Top suggestions (cached)
            suggestions = self.get_smart_suggestions(db)
            summary['top_suggestions'] = [
                {
                    'type': suggestion.get('suggestion_type', 'unknown'),
                    'description': suggestion.get('description', ''),
                    'priority': suggestion.get('priority', 'medium')
                }
                for suggestion in suggestions[:3]  # Top 3 suggestions
            ]
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating analytics summary: {e}")
            return {'error': str(e)} 