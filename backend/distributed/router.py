"""
Router Agent for Node-LLM System
Implements top-k retrieval and token budgeting for efficient node execution
"""

import asyncio
import json
import redis
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import heapq
import logging

# Local imports
from services.neo4j_service import Neo4jService
from pipeline.executor import PipelineExecutor
from config.neo4j import neo4j_settings

logger = logging.getLogger(__name__)

class RouterAgent:
    """Router Agent for intelligent node retrieval and execution planning"""
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        """Initialize the Router Agent with Redis connection"""
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.node_queue = 'node_execution_queue'
        self.router_results = 'router_results'
        
        # Initialize Neo4j connection
        try:
            self.neo4j_service = Neo4jService(
                neo4j_settings.NEO4J_URI,
                neo4j_settings.NEO4J_USER,
                neo4j_settings.NEO4J_PASSWORD
            )
            logger.info("Neo4j connection established for RouterAgent")
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}")
            self.neo4j_service = None
        
        # Initialize PipelineExecutor
        try:
            self.pipeline_executor = PipelineExecutor("pipelines/graph_config.json")
            logger.info("PipelineExecutor initialized for RouterAgent")
        except Exception as e:
            logger.warning(f"PipelineExecutor initialization failed: {e}")
            self.pipeline_executor = None
    
    async def retrieve_top_k_nodes(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve top-k most relevant nodes based on query using Neo4j"""
        if not self.neo4j_service:
            logger.warning("Neo4j service not available for node retrieval")
            return []
        
        try:
            with self.neo4j_service.driver.session() as session:
                # Use Neo4j's full-text search capabilities or similarity matching
                # This is a simplified implementation - in practice, you might use embeddings
                query_text = query.lower()
                
                # Search for nodes that match the query in name or context
                # Also retrieve relationships to understand the graph structure
                cypher_query = """
                MATCH (n:Node)
                WHERE toLower(n.name) CONTAINS $query OR toLower(n.context_window) CONTAINS $query
                OPTIONAL MATCH (n)-[r]-(related:Node)
                RETURN n, collect({relation: type(r), related_node: related}) as relationships
                ORDER BY n.updated_at DESC
                LIMIT $limit
                """
                
                result = session.run(cypher_query, {
                    "query": query_text,
                    "limit": k
                })
                
                nodes = []
                for record in result:
                    node = dict(record["n"])
                    relationships = record["relationships"]
                    node["relationships"] = relationships
                    nodes.append(node)
                
                return nodes
        except Exception as e:
            logger.error(f"Error retrieving top-k nodes: {e}")
            return []
    
    def calculate_token_budget(self, nodes: List[Dict[str, Any]], max_tokens: int = 4096) -> List[Dict[str, Any]]:
        """Calculate token budget for nodes and filter based on budget constraints"""
        # This is a simplified implementation
        # In practice, you would use a tokenizer to accurately count tokens
        
        budgeted_nodes = []
        total_tokens = 0
        
        for node in nodes:
            # Estimate tokens (very rough approximation)
            context = node.get('context_window', '')
            estimated_tokens = len(context.split())  # Very rough estimation
            
            if total_tokens + estimated_tokens <= max_tokens:
                node['estimated_tokens'] = estimated_tokens
                budgeted_nodes.append(node)
                total_tokens += estimated_tokens
            else:
                # If we can't fit this node, we might split it or skip it
                # For now, we'll skip nodes that don't fit
                logger.info(f"Skipping node {node.get('id')} due to token budget constraints")
                node['estimated_tokens'] = estimated_tokens
                node['status'] = 'skipped_budget'
                # Still add to results but mark as skipped
                # budgeted_nodes.append(node)  # Uncomment if you want to include skipped nodes
        
        logger.info(f"Token budget calculation: {total_tokens}/{max_tokens} tokens used")
        return budgeted_nodes
    
    async def plan_execution(self, query: str, k: int = 5, max_tokens: int = 4096) -> Dict[str, Any]:
        """Plan execution by retrieving relevant nodes and applying token budgeting"""
        # Step 1: Retrieve top-k nodes
        nodes = await self.retrieve_top_k_nodes(query, k)
        
        # Step 2: Apply token budgeting
        budgeted_nodes = self.calculate_token_budget(nodes, max_tokens)
        
        # Step 3: Create execution plan
        execution_plan = {
            "query": query,
            "retrieved_nodes": len(nodes),
            "budgeted_nodes": len(budgeted_nodes),
            "nodes": budgeted_nodes,
            "total_estimated_tokens": sum(node.get('estimated_tokens', 0) for node in budgeted_nodes),
            "created_at": datetime.now().isoformat()
        }
        
        # Store execution plan in Redis for tracking
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.redis_client.setex(f"execution_plan:{plan_id}", 3600, json.dumps(execution_plan))
        
        # Publish update to Redis for WebSocket clients
        update_data = {
            "event": "plan_created",
            "plan_id": plan_id,
            "query": query,
            "retrieved_nodes": len(nodes),
            "budgeted_nodes": len(budgeted_nodes),
            "timestamp": datetime.now().isoformat()
        }
        self.redis_client.publish("router_updates:default", json.dumps(update_data))
        
        return {
            "plan_id": plan_id,
            "execution_plan": execution_plan
        }
    
    async def execute_plan(self, plan_id: str, pipeline_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a previously created plan using PipelineExecutor"""
        # Retrieve plan from Redis
        plan_json = self.redis_client.get(f"execution_plan:{plan_id}")
        if not plan_json:
            raise ValueError(f"Execution plan {plan_id} not found")
        
        plan = json.loads(plan_json)
        nodes = plan.get("nodes", [])
        
        results = {
            "plan_id": plan_id,
            "node_results": {},
            "successful_executions": 0,
            "failed_executions": 0,
            "pipeline_results": {}
        }
        
        # Publish execution start update
        update_data = {
            "event": "execution_started",
            "plan_id": plan_id,
            "node_count": len(nodes),
            "timestamp": datetime.now().isoformat()
        }
        self.redis_client.publish("router_updates:default", json.dumps(update_data))
        
        # If a pipeline_id is provided, execute the pipeline with the context from nodes
        if pipeline_id and self.pipeline_executor:
            try:
                # Prepare input data for the pipeline using node contexts
                input_data = {
                    "nodes_context": [node.get("context_window", "") for node in nodes],
                    "query": plan.get("query", "")
                }
                
                # Execute the pipeline
                pipeline_result = await self.pipeline_executor.run_pipeline(pipeline_id, input_data)
                results["pipeline_results"][pipeline_id] = pipeline_result
                
                if pipeline_result.get("status") == "success":
                    results["successful_executions"] += 1
                else:
                    results["failed_executions"] += 1
                    
                # Publish pipeline execution result
                update_data = {
                    "event": "pipeline_executed",
                    "plan_id": plan_id,
                    "pipeline_id": pipeline_id,
                    "status": pipeline_result.get("status"),
                    "timestamp": datetime.now().isoformat()
                }
                self.redis_client.publish("router_updates:default", json.dumps(update_data))
                    
            except Exception as e:
                logger.error(f"Error executing pipeline {pipeline_id}: {e}")
                results["pipeline_results"][pipeline_id] = {
                    "status": "error",
                    "error": str(e)
                }
                results["failed_executions"] += 1
                
                # Publish pipeline execution error
                update_data = {
                    "event": "pipeline_error",
                    "plan_id": plan_id,
                    "pipeline_id": pipeline_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                self.redis_client.publish("router_updates:default", json.dumps(update_data))
        
        # Execute individual nodes if needed
        for i, node in enumerate(nodes):
            node_id = node.get("id")
            try:
                # For individual node execution, we would determine what specific task to run
                # based on the node type and context
                
                # Publish node execution start
                update_data = {
                    "event": "node_execution_started",
                    "plan_id": plan_id,
                    "node_id": node_id,
                    "node_index": i,
                    "total_nodes": len(nodes),
                    "timestamp": datetime.now().isoformat()
                }
                self.redis_client.publish("router_updates:default", json.dumps(update_data))
                
                # For now, we'll just mark as executed
                results["node_results"][node_id] = {
                    "status": "executed",
                    "result": f"Executed node {node_id}",
                    "tokens_used": node.get("estimated_tokens", 0)
                }
                results["successful_executions"] += 1
                
                # Publish node execution result
                update_data = {
                    "event": "node_executed",
                    "plan_id": plan_id,
                    "node_id": node_id,
                    "status": "success",
                    "tokens_used": node.get("estimated_tokens", 0),
                    "timestamp": datetime.now().isoformat()
                }
                self.redis_client.publish("router_updates:default", json.dumps(update_data))
                
                # Update node status in Neo4j
                if self.neo4j_service:
                    try:
                        with self.neo4j_service.driver.session() as session:
                            session.run("""
                                MATCH (n:Node {id: $node_id})
                                SET n.last_executed = datetime(),
                                    n.execution_count = coalesce(n.execution_count, 0) + 1
                            """, {"node_id": node_id})
                    except Exception as e:
                        logger.error(f"Error updating node {node_id} in Neo4j: {e}")
                        
            except Exception as e:
                logger.error(f"Error executing node {node_id}: {e}")
                results["node_results"][node_id] = {
                    "status": "failed",
                    "error": str(e)
                }
                results["failed_executions"] += 1
                
                # Publish node execution error
                update_data = {
                    "event": "node_execution_error",
                    "plan_id": plan_id,
                    "node_id": node_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                self.redis_client.publish("router_updates:default", json.dumps(update_data))
        
        # Store results in Redis
        self.redis_client.setex(f"execution_results:{plan_id}", 3600, json.dumps(results))
        
        # Publish execution completion
        update_data = {
            "event": "execution_completed",
            "plan_id": plan_id,
            "successful_executions": results["successful_executions"],
            "failed_executions": results["failed_executions"],
            "timestamp": datetime.now().isoformat()
        }
        self.redis_client.publish("router_updates:default", json.dumps(update_data))
        
        return results
    
    def get_node_dependencies(self, node_id: str) -> List[Dict[str, Any]]:
        """Get dependencies for a specific node from Neo4j"""
        if not self.neo4j_service:
            return []
        
        try:
            with self.neo4j_service.driver.session() as session:
                query = """
                MATCH (n:Node {id: $node_id})<-[:DEPENDS_ON]-(dependent:Node)
                RETURN dependent
                """
                result = session.run(query, {"node_id": node_id})
                
                dependencies = []
                for record in result:
                    dependency = dict(record["dependent"])
                    dependencies.append(dependency)
                
                return dependencies
        except Exception as e:
            logger.error(f"Error getting dependencies for node {node_id}: {e}")
            return []
    
    def get_node_subgraph(self, node_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get a subgraph centered around a specific node"""
        if not self.neo4j_service:
            return {}
        
        try:
            with self.neo4j_service.driver.session() as session:
                # Get nodes and relationships up to a certain depth
                query = """
                MATCH (center:Node {id: $node_id})
                CALL apoc.path.subgraphAll(center, {
                    maxLevel: $depth,
                    relationshipFilter: null,
                    labelFilter: '+Node'
                })
                YIELD nodes, relationships
                RETURN nodes, [r IN relationships | {start: id(startNode(r)), end: id(endNode(r)), type: type(r)}] as rels
                """
                
                # Fallback query if APOC is not available
                fallback_query = """
                MATCH (center:Node {id: $node_id})
                MATCH (center)-[r*1..$depth]-(related:Node)
                RETURN collect(DISTINCT center) + collect(DISTINCT related) as nodes,
                       collect(DISTINCT {start: id(startNode(r[-1])), end: id(endNode(r[-1])), type: type(r[-1])}) as rels
                """
                
                try:
                    result = session.run(query, {"node_id": node_id, "depth": depth})
                except Exception:
                    # Fallback if APOC is not available
                    result = session.run(fallback_query, {"node_id": node_id, "depth": depth})
                
                record = result.single()
                if record:
                    nodes = [dict(node) for node in record["nodes"]]
                    relationships = record["rels"]
                    
                    return {
                        "nodes": nodes,
                        "relationships": relationships,
                        "center_node": node_id
                    }
                
                return {}
        except Exception as e:
            logger.error(f"Error getting subgraph for node {node_id}: {e}")
            return {}
    
    def update_node_relevance(self, node_id: str, relevance_score: float) -> bool:
        """Update node relevance score in Neo4j"""
        if not self.neo4j_service:
            return False
        
        try:
            with self.neo4j_service.driver.session() as session:
                query = """
                MATCH (n:Node {id: $node_id})
                SET n.relevance_score = $relevance_score,
                    n.last_updated = datetime()
                """
                session.run(query, {
                    "node_id": node_id,
                    "relevance_score": relevance_score
                })
                return True
        except Exception as e:
            logger.error(f"Error updating relevance for node {node_id}: {e}")
            return False

# Initialize router agent
router_agent = RouterAgent()
