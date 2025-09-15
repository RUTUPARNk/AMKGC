"""
Pipeline Executor for Graph-Based AI Workflow Engine
"""

import json
import asyncio
import httpx
import time
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import deque, defaultdict
import os
import sys

# Add the parent directory to the path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Try to import supervisor configuration
try:
    from config.supervisor_config import SupervisorConfig
except ImportError:
    # Fallback configuration
    class SupervisorConfig:
        CHECK_INTERVAL = 30

# Try to import supervisor service
try:
    from services.ollama_supervisor import OllamaSupervisorService
    SUPERVISOR_AVAILABLE = True
except ImportError:
    SUPERVISOR_AVAILABLE = False
    OllamaSupervisorService = None


class PipelineExecutor:
    """Executes pipeline graphs with DAG-based workflow"""
    
    def __init__(self, config_path: str = "pipelines/graph_config.json", subpipelines_path: str = "pipelines/subpipelines"):
        """Initialize the pipeline executor with graph configuration"""
        self.config_path = config_path
        self.subpipelines_path = subpipelines_path
        self.graphs = self._load_graphs()
        self.subpipelines = self._load_subpipelines()
        
        # Initialize supervisor service if available
        if SUPERVISOR_AVAILABLE:
            try:
                self.supervisor = OllamaSupervisorService()
            except Exception:
                self.supervisor = None
        else:
            self.supervisor = None
        
    def _get_resource_status(self) -> Dict[str, Any]:
        """Get current resource status from supervisor"""
        if not self.supervisor:
            return {"memory_ok": True, "cpu_ok": True}
            
        try:
            # Check memory status
            memory_ok = self.supervisor.memory_ok()
            
            # In a more sophisticated implementation, we would also check CPU usage
            # For now, we'll assume CPU is OK if we have the supervisor
            cpu_ok = True
            
            return {"memory_ok": memory_ok, "cpu_ok": cpu_ok}
        except Exception:
            # If we can't get resource status, assume resources are OK
            return {"memory_ok": True, "cpu_ok": True}
        
    def _select_optimal_backend(self, node: Dict[str, Any]) -> str:
        """Select the optimal backend based on resource status and node requirements"""
        backend = node.get("backend", "ollama")
        
        # If we don't have resource information, use the default backend
        if not self.supervisor:
            return backend
            
        # Get current resource status
        resource_status = self._get_resource_status()
        
        # If memory is low and this is a local model, consider using cloud backend
        if not resource_status["memory_ok"] and backend == "ollama":
            # Check if cloud backend is available for this node
            if node.get("cloud_alternative"):
                return node.get("cloud_alternative")
            
            # If no specific cloud alternative, try a generic cloud backend
            # This is a simplified approach - in a real system, this would be more sophisticated
            if any(b in node.get("model", "") for b in ["gpt", "claude", "gemini"]):
                return backend  # Already a cloud model
            else:
                # Prefer cloud for resource-intensive tasks when local resources are low
                return "openai"  # Default to OpenAI as cloud alternative
        
        return backend
        
    def _load_graphs(self) -> List[Dict[str, Any]]:
        """Load graph configurations from JSON file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    return json.load(f)
            else:
                # Return empty list if config file doesn't exist
                return []
        except Exception as e:
            print(f"Warning: Could not load pipeline config: {e}")
            return []
    
    def _load_subpipelines(self) -> Dict[str, Dict[str, Any]]:
        """Load sub-pipeline configurations from JSON files"""
        subpipelines = {}
        try:
            if os.path.exists(self.subpipelines_path):
                for filename in os.listdir(self.subpipelines_path):
                    if filename.endswith('.json'):
                        filepath = os.path.join(self.subpipelines_path, filename)
                        with open(filepath, "r") as f:
                            subpipeline = json.load(f)
                            subpipeline_id = subpipeline.get("id")
                            if subpipeline_id:
                                subpipelines[subpipeline_id] = subpipeline
            return subpipelines
        except Exception as e:
            print(f"Warning: Could not load subpipelines: {e}")
            return subpipelines
    
    def _get_node_by_id(self, graph: Dict[str, Any], node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node by its ID from a graph"""
        for node in graph.get("nodes", []):
            if node.get("id") == node_id:
                return node
        return None
    
    async def run_subpipeline(self, subpipeline_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a sub-pipeline by ID with input data"""
        if subpipeline_id not in self.subpipelines:
            raise ValueError(f"Sub-pipeline {subpipeline_id} not found")
            
        subpipeline = self.subpipelines[subpipeline_id]
        
        # Get conditional edges
        conditional_edges = self._get_conditional_edges(subpipeline)
        
        # Build execution levels for parallel execution
        execution_levels = self._build_execution_levels(subpipeline)
        
        # Execute nodes level by level (parallel within each level)
        execution_trace = {}
        node_outputs = {"input": input_data}
        
        try:
            for level, node_ids in enumerate(execution_levels):
                # Execute all nodes in this level concurrently
                level_tasks = []
                level_nodes = []
                
                for node_id in node_ids:
                    node = self._get_node_by_id(subpipeline, node_id)
                    if not node:
                        continue
                        
                    # Get input for this node
                    node_input = self._prepare_node_input(node, node_outputs)
                    
                    # Create task for this node
                    task = self._execute_node(node, node_input)
                    level_tasks.append(task)
                    level_nodes.append(node_id)
                
                # Execute all nodes in this level concurrently
                if level_tasks:
                    results = await asyncio.gather(*level_tasks, return_exceptions=True)
                    
                    # Process results
                    for i, result in enumerate(results):
                        node_id = level_nodes[i]
                        if isinstance(result, Exception):
                            execution_trace[node_id] = {
                                "status": "error",
                                "error": str(result)
                            }
                        else:
                            execution_trace[node_id] = result
                            node_outputs[node_id] = result
                            
                            # Handle conditional routing
                            if node_id in conditional_edges:
                                # Evaluate conditions and determine which nodes to execute next
                                for edge in conditional_edges[node_id]:
                                    condition = edge.get("condition")
                                    to_node = edge.get("to")
                                    
                                    if condition and to_node:
                                        if self._evaluate_condition(condition, result):
                                            # Mark this node for execution in the next level
                                            # In a more sophisticated implementation, we would dynamically
                                            # adjust the execution plan
                                            pass
                
            # Get the final output (from nodes in the last level)
            final_output = input_data
            if execution_levels:
                # Use output from the last node in the last level
                last_level_nodes = execution_levels[-1]
                if last_level_nodes:
                    # Try to get output from the last node executed
                    for node_id in reversed(last_level_nodes):
                        if node_id in node_outputs:
                            final_output = node_outputs[node_id]
                            break
            
            return {
                "pipeline": subpipeline_id,
                "output": final_output,
                "trace": execution_trace,
                "status": "success"
            }
        except Exception as e:
            return {
                "pipeline": subpipeline_id,
                "output": None,
                "trace": execution_trace,
                "status": "error",
                "error": str(e)
            }
    
    async def run_pipeline(self, pipeline_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a pipeline by ID with input data"""
        graph = self._get_graph(pipeline_id)
        if not graph:
            raise ValueError(f"Pipeline {pipeline_id} not found")
            
        # Get conditional edges
        conditional_edges = self._get_conditional_edges(graph)
        
        # Build execution levels for parallel execution
        execution_levels = self._build_execution_levels(graph)
        
        # Execute nodes level by level (parallel within each level)
        execution_trace = {}
        node_outputs = {"input": input_data}
        
        try:
            for level, node_ids in enumerate(execution_levels):
                # Execute all nodes in this level concurrently
                level_tasks = []
                level_nodes = []
                
                for node_id in node_ids:
                    node = self._get_node_by_id(graph, node_id)
                    if not node:
                        continue
                        
                    # Get input for this node
                    node_input = self._prepare_node_input(node, node_outputs)
                    
                    # Create task for this node
                    task = self._execute_node(node, node_input)
                    level_tasks.append(task)
                    level_nodes.append(node_id)
                
                # Execute all nodes in this level concurrently
                if level_tasks:
                    results = await asyncio.gather(*level_tasks, return_exceptions=True)
                    
                    # Process results
                    for i, result in enumerate(results):
                        node_id = level_nodes[i]
                        if isinstance(result, Exception):
                            execution_trace[node_id] = {
                                "status": "error",
                                "error": str(result)
                            }
                        else:
                            execution_trace[node_id] = result
                            node_outputs[node_id] = result
                            
                            # Handle conditional routing
                            if node_id in conditional_edges:
                                # Evaluate conditions and determine which nodes to execute next
                                for edge in conditional_edges[node_id]:
                                    condition = edge.get("condition")
                                    to_node = edge.get("to")
                                    
                                    if condition and to_node:
                                        if self._evaluate_condition(condition, result):
                                            # Mark this node for execution in the next level
                                            # In a more sophisticated implementation, we would dynamically
                                            # adjust the execution plan
                                            pass
                
            # Get the final output (from nodes in the last level)
            final_output = input_data
            if execution_levels:
                # Use output from the last node in the last level
                last_level_nodes = execution_levels[-1]
                if last_level_nodes:
                    # Try to get output from the last node executed
                    for node_id in reversed(last_level_nodes):
                        if node_id in node_outputs:
                            final_output = node_outputs[node_id]
                            break
            
            return {
                "pipeline": pipeline_id,
                "output": final_output,
                "trace": execution_trace,
                "status": "success"
            }
        except Exception as e:
            return {
                "pipeline": pipeline_id,
                "output": None,
                "trace": execution_trace,
                "status": "error",
                "error": str(e)
            }
    
    def _get_graph(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Find a graph by ID"""
        for graph in self.graphs:
            if graph.get("id") == pipeline_id:
                return graph
        return None
        
    def _get_node_by_id(self, graph: Dict[str, Any], node_id: str) -> Optional[Dict[str, Any]]:
        """Find a node by ID in a graph"""
        for node in graph.get("nodes", []):
            if node.get("id") == node_id:
                return node
        return None
        
    def _topological_sort(self, graph: Dict[str, Any]) -> List[str]:
        """Topologically sort nodes based on edges (DAG)"""
        # Build adjacency list and in-degree count
        nodes = {node["id"]: node for node in graph.get("nodes", [])}
        in_degree = {node_id: 0 for node_id in nodes}
        adj_list = {node_id: [] for node_id in nodes}
        
        # Process edges
        for edge in graph.get("edges", []):
            from_node = edge.get("from")
            to_node = edge.get("to")
            
            if from_node in nodes and to_node in nodes:
                adj_list[from_node].append(to_node)
                in_degree[to_node] = in_degree.get(to_node, 0) + 1
        
        # Kahn's algorithm for topological sort
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            node_id = queue.popleft()
            result.append(node_id)
            
            for neighbor in adj_list.get(node_id, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
        
    def _build_execution_levels(self, graph: Dict[str, Any]) -> List[List[str]]:
        """Build execution levels for parallel execution"""
        # Build adjacency list and in-degree count
        nodes = {node["id"]: node for node in graph.get("nodes", [])}
        in_degree = {node_id: 0 for node_id in nodes}
        adj_list = {node_id: [] for node_id in nodes}
        
        # Process edges
        for edge in graph.get("edges", []):
            from_node = edge.get("from")
            to_node = edge.get("to")
            
            if from_node in nodes and to_node in nodes:
                adj_list[from_node].append(to_node)
                in_degree[to_node] = in_degree.get(to_node, 0) + 1
        
        # Kahn's algorithm to build levels
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        levels = []
        
        while queue:
            level_size = len(queue)
            current_level = []
            
            # Process all nodes at current level
            for _ in range(level_size):
                node_id = queue.popleft()
                current_level.append(node_id)
                
                # Update neighbors
                for neighbor in adj_list.get(node_id, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            
            levels.append(current_level)
        
        return levels
        
    def _get_conditional_edges(self, graph: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Get conditional edges from the graph"""
        conditional_edges = defaultdict(list)
        
        for edge in graph.get("edges", []):
            if "condition" in edge:
                from_node = edge.get("from")
                conditional_edges[from_node].append(edge)
                
        return conditional_edges
        
    def _evaluate_condition(self, condition: str, node_output: Dict[str, Any]) -> bool:
        """Evaluate a condition based on node output"""
        try:
            # Simple condition evaluation (in a real system, this would be more sophisticated)
            # Extract sentiment from output for our example
            if "sentiment" in condition:
                # Extract sentiment from output
                output_text = str(node_output.get("output", ""))
                
                # Simple sentiment detection (in a real system, this would use NLP)
                if "positive" in condition.lower() and ("positive" in output_text.lower() or "good" in output_text.lower() or "great" in output_text.lower()):
                    return True
                elif "negative" in condition.lower() and ("negative" in output_text.lower() or "bad" in output_text.lower() or "terrible" in output_text.lower()):
                    return True
                elif "neutral" in condition.lower() and ("neutral" in output_text.lower() or ("not" not in output_text.lower() and "good" not in output_text.lower() and "bad" not in output_text.lower())):
                    return True
            
            return False
        except Exception:
            # If we can't evaluate the condition, default to False
            return False
        
    def _prepare_node_input(self, node: Dict[str, Any], node_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare input data for a node based on its dependencies"""
        # For now, pass the output of the previous node or the initial input
        # In a more complex system, this would handle mapping specific fields
        node_id = node.get("id")
        if not node_id:
            return {}
            
        # Simple case: pass the most recent output
        if len(node_outputs) > 1:  # Has previous outputs
            # Get the last output (not counting the initial input)
            output_keys = [k for k in node_outputs.keys() if k != "input"]
            if output_keys:
                return node_outputs[output_keys[-1]]
        
        return node_outputs.get("input", {})
        
    async def _execute_node(self, node: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single node with input data"""
        node_id = node.get("id")
        node_type = node.get("type")
        # Select optimal backend based on resource status
        backend = self._select_optimal_backend(node)
        model = node.get("model")
        
        start_time = time.time()
        
        try:
            if node_type == "model":
                if backend == "ollama":
                    result = await self._execute_ollama_model(node, input_data)
                elif backend == "openai":
                    result = await self._execute_openai_model(node, input_data)
                elif backend == "anthropic":
                    result = await self._execute_anthropic_model(node, input_data)
                else:
                    raise ValueError(f"Unsupported backend: {backend}")
            elif node_type == "function":
                result = await self._execute_function(node, input_data)
            else:
                raise ValueError(f"Unsupported node type: {node_type}")
                
            execution_time = time.time() - start_time
            
            return {
                "status": "success",
                "output": result,
                "execution_time": execution_time,
                "backend": backend,
                "model": model
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "status": "error",
                "error": str(e),
                "execution_time": execution_time,
                "backend": backend,
                "model": model
            }

    async def _execute_ollama_model(self, node: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Ollama model node"""
        model = node.get("model", "llama3:latest")
        prompt = input_data.get("text", "") if isinstance(input_data, dict) else str(input_data)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()

                return {
                    "status": "success",
                    "output": result.get("response", ""),
                    "model": model,
                    "backend": "ollama"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "model": model,
                "backend": "ollama"
            }
            
    async def _execute_openai_model(self, node: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an OpenAI model node (stub implementation)"""
        model = node.get("model", "gpt-3.5-turbo")
        prompt = input_data.get("text", "") if isinstance(input_data, dict) else str(input_data)
        
        # This is a stub - would need actual OpenAI API key and implementation
        return {
            "status": "stub",
            "output": f"[OpenAI {model} would process: {prompt[:50]}...]",
            "model": model,
            "backend": "openai"
        }
        
    async def _execute_anthropic_model(self, node: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Anthropic model node (stub implementation)"""
        model = node.get("model", "claude-3-haiku-20240307")
        prompt = input_data.get("text", "") if isinstance(input_data, dict) else str(input_data)
        
        # This is a stub - would need actual Anthropic API key and implementation
        return {
            "status": "stub",
            "output": f"[Anthropic {model} would process: {prompt[:50]}...]",
            "model": model,
            "backend": "anthropic"
        }
        
    async def _execute_function(self, node: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a function node (stub implementation)"""
        function_name = node.get("function", "unknown")
        
        # This is a stub - would need actual function implementation
        return {
            "status": "stub",
            "output": f"[Function {function_name} executed with input: {input_data}]",
            "function": function_name,
            "backend": "function"
        }
