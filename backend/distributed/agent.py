"""
Distributed Pipeline Execution Agent
Worker that executes pipeline nodes assigned by the coordinator
"""

import asyncio
import json
import redis
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import the PipelineExecutor for node execution
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from pipeline.executor import PipelineExecutor
    PIPELINE_EXECUTOR_AVAILABLE = True
except ImportError:
    PIPELINE_EXECUTOR_AVAILABLE = False
    PipelineExecutor = None


class DistributedAgent:
    """Agent worker that executes pipeline nodes"""
    
    def __init__(self, agent_id: str, redis_host: str = 'localhost', redis_port: int = 6379,
                 capabilities: List[str] = None):
        """Initialize the agent with Redis connection and capabilities"""
        self.agent_id = agent_id
        self.capabilities = capabilities or ['ollama', 'function']
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.node_task_queue = 'node_tasks'
        self.executor = PipelineExecutor() if PIPELINE_EXECUTOR_AVAILABLE else None
        self.running = False
        
    def start(self):
        """Start the agent to listen for tasks"""
        self.running = True
        print(f"Agent {self.agent_id} started, listening for tasks...")
        
        # Register with coordinator
        self._register_with_coordinator()
        
        # Start listening for tasks
        self._listen_for_tasks()
    
    def stop(self):
        """Stop the agent"""
        self.running = False
        print(f"Agent {self.agent_id} stopped")
    
    def _register_with_coordinator(self):
        """Register this agent with the coordinator"""
        try:
            # In a real implementation, we would use the coordinator's register method
            # For now, we'll directly update Redis
            agent_info = {
                'agent_id': self.agent_id,
                'capabilities': json.dumps(self.capabilities),
                'last_heartbeat': datetime.now().isoformat(),
                'status': 'active'
            }
            
            self.redis_client.hset('active_agents', self.agent_id, json.dumps(agent_info))
            print(f"Agent {self.agent_id} registered with coordinator")
        except Exception as e:
            print(f"Failed to register agent: {e}")
    
    def _listen_for_tasks(self):
        """Listen for node execution tasks from the coordinator"""
        while self.running:
            try:
                # Check for tasks with a timeout
                task_data = self.redis_client.brpop(self.node_task_queue, timeout=5)
                
                if task_data:
                    # Process the task
                    _, task_json = task_data
                    task = json.loads(task_json)
                    
                    print(f"Agent {self.agent_id} received task: {task['node_id']}")
                    
                    # Send heartbeat before processing
                    self._send_heartbeat()
                    
                    # Execute the task
                    result = self._execute_task(task)
                    
                    # Report result back
                    self._report_result(task, result)
                    
                # Send heartbeat
                self._send_heartbeat()
                
            except Exception as e:
                print(f"Error processing task: {e}")
                # Send heartbeat even on error to show we're still alive
                self._send_heartbeat()
                time.sleep(1)
    
    def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a node task"""
        try:
            node_id = task['node_id']
            input_data = task.get('input_data', {})
            
            # In a real implementation, we would:
            # 1. Load the specific node configuration
            # 2. Execute it using the appropriate backend
            # 3. Return the result
            
            # For now, simulate execution
            print(f"Executing node {node_id} with input: {input_data}")
            
            # Simulate some work
            time.sleep(2)
            
            result = {
                'node_id': node_id,
                'status': 'completed',
                'output': f"Processed by agent {self.agent_id}",
                'execution_time': 2.0,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            return {
                'node_id': task.get('node_id'),
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _report_result(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Report task result back to coordinator"""
        try:
            result_data = {
                'task_id': task['task_id'],
                'node_id': task['node_id'],
                'result': result,
                'agent_id': self.agent_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Push result to results queue
            self.redis_client.lpush('node_results', json.dumps(result_data))
            print(f"Agent {self.agent_id} reported result for {task['node_id']}")
            
        except Exception as e:
            print(f"Failed to report result: {e}")
    
    def _send_heartbeat(self):
        """Send heartbeat to coordinator"""
        try:
            agent_info = {
                'agent_id': self.agent_id,
                'capabilities': json.dumps(self.capabilities),
                'last_heartbeat': datetime.now().isoformat(),
                'status': 'active'
            }
            
            self.redis_client.hset('active_agents', self.agent_id, json.dumps(agent_info))
        except Exception as e:
            print(f"Failed to send heartbeat: {e}")
    
    async def execute_node(self, node_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single node (using PipelineExecutor if available)"""
        if not PIPELINE_EXECUTOR_AVAILABLE or not self.executor:
            # Fallback execution
            return {
                'status': 'completed',
                'output': f"Executed {node_config.get('id', 'unknown')} on {self.agent_id}",
                'backend': 'simulated',
                'model': node_config.get('model', 'unknown'),
                'execution_time': 0.1
            }
        
        # Use PipelineExecutor for actual execution
        try:
            result = await self.executor._execute_node(node_config, input_data)
            return result
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
