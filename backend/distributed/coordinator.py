"""
Distributed Pipeline Execution Coordinator
Manages DAG execution across multiple agent workers
"""

import asyncio
import json
import redis
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class DistributedCoordinator:
    """Coordinates pipeline execution across distributed agents"""
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        """Initialize the coordinator with Redis connection"""
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.task_queue = 'pipeline_tasks'
        self.result_queue = 'pipeline_results'
        self.agent_registry = 'active_agents'
        self.node_task_queue = 'node_tasks'
        self.node_results_queue = 'node_results'
        self.task_monitoring = 'task_monitoring'
        
    async def submit_pipeline_task(self, pipeline_id: str, input_data: Dict[str, Any], 
                                 execution_plan: List[List[str]]) -> str:
        """Submit a pipeline task for distributed execution"""
        task_id = str(uuid.uuid4())
        
        task = {
            'task_id': task_id,
            'pipeline_id': pipeline_id,
            'input_data': input_data,
            'execution_plan': execution_plan,
            'status': 'submitted',
            'created_at': datetime.now().isoformat()
        }
        
        # Push task to Redis queue
        self.redis_client.lpush(self.task_queue, json.dumps(task))
        
        # Initialize task monitoring
        self._initialize_task_monitoring(task_id)
        
        return task_id
    
    def _initialize_task_monitoring(self, task_id: str):
        """Initialize monitoring for a task"""
        task_monitor = {
            'task_id': task_id,
            'status': 'submitted',
            'node_assignments': {},  # node_id -> assigned_agent
            'node_statuses': {},     # node_id -> status
            'last_updated': datetime.now().isoformat()
        }
        
        self.redis_client.hset(self.task_monitoring, task_id, json.dumps(task_monitor))
    
    def _update_node_assignment(self, task_id: str, node_id: str, agent_id: str):
        """Update node assignment for monitoring"""
        task_monitor_json = self.redis_client.hget(self.task_monitoring, task_id)
        if task_monitor_json:
            task_monitor = json.loads(task_monitor_json)
            task_monitor['node_assignments'][node_id] = agent_id
            task_monitor['node_statuses'][node_id] = 'assigned'
            task_monitor['last_updated'] = datetime.now().isoformat()
            self.redis_client.hset(self.task_monitoring, task_id, json.dumps(task_monitor))
    
    def _update_node_status(self, task_id: str, node_id: str, status: str):
        """Update node status for monitoring"""
        task_monitor_json = self.redis_client.hget(self.task_monitoring, task_id)
        if task_monitor_json:
            task_monitor = json.loads(task_monitor_json)
            task_monitor['node_statuses'][node_id] = status
            task_monitor['last_updated'] = datetime.now().isoformat()
            self.redis_client.hset(self.task_monitoring, task_id, json.dumps(task_monitor))
    
    async def monitor_task_progress(self, task_id: str) -> Dict[str, Any]:
        """Monitor the progress of a distributed task"""
        # Check task status in Redis
        task_status = self.redis_client.hgetall(f"task:{task_id}")
        return task_status
    
    async def collect_task_results(self, task_id: str) -> Dict[str, Any]:
        """Collect results for a completed task"""
        # Get results from Redis
        results = self.redis_client.hgetall(f"results:{task_id}")
        return results
    
    def register_agent(self, agent_id: str, capabilities: List[str]):
        """Register an agent with its capabilities"""
        agent_info = {
            'agent_id': agent_id,
            'capabilities': json.dumps(capabilities),
            'last_heartbeat': datetime.now().isoformat(),
            'status': 'active'
        }
        
        self.redis_client.hset(self.agent_registry, agent_id, json.dumps(agent_info))
        self.redis_client.expire(self.agent_registry, 300)  # 5-minute expiration
    
    def get_active_agents(self) -> List[Dict[str, Any]]:
        """Get list of active agents"""
        agents = []
        agent_data = self.redis_client.hgetall(self.agent_registry)
        
        for agent_id, agent_info in agent_data.items():
            agents.append(json.loads(agent_info))
            
        return agents
    
    def check_agent_health(self) -> Dict[str, Any]:
        """Check health of all agents and identify failed ones"""
        now = datetime.now()
        failed_agents = []
        active_agents = []
        
        agent_data = self.redis_client.hgetall(self.agent_registry)
        
        for agent_id, agent_info_json in agent_data.items():
            try:
                agent_info = json.loads(agent_info_json)
                last_heartbeat = datetime.fromisoformat(agent_info['last_heartbeat'])
                
                # Check if agent is stale (no heartbeat for more than 30 seconds)
                if (now - last_heartbeat).total_seconds() > 30:
                    failed_agents.append(agent_id)
                    # Mark agent as failed
                    agent_info['status'] = 'failed'
                    self.redis_client.hset(self.agent_registry, agent_id, json.dumps(agent_info))
                else:
                    active_agents.append(agent_id)
            except Exception as e:
                print(f"Error checking agent {agent_id}: {e}")
                failed_agents.append(agent_id)
        
        return {
            'active_agents': active_agents,
            'failed_agents': failed_agents
        }
    
    def requeue_failed_tasks(self, failed_agent_id: str) -> int:
        """Requeue tasks that were assigned to a failed agent"""
        requeued_count = 0
        
        # Get all monitored tasks
        task_monitors = self.redis_client.hgetall(self.task_monitoring)
        
        for task_id, task_monitor_json in task_monitors.items():
            try:
                task_monitor = json.loads(task_monitor_json)
                
                # Check if any nodes were assigned to the failed agent
                for node_id, assigned_agent in task_monitor.get('node_assignments', {}).items():
                    if assigned_agent == failed_agent_id:
                        # Check if the node is still in progress
                        node_status = task_monitor.get('node_statuses', {}).get(node_id, 'unknown')
                        if node_status in ['assigned', 'in_progress']:
                            # Requeue the node task
                            node_task = {
                                'task_id': task_id,
                                'node_id': node_id,
                                'input_data': {},  # Would need to store actual input
                                'requeued': True,
                                'original_agent': failed_agent_id
                            }
                            
                            self.redis_client.lpush(self.node_task_queue, json.dumps(node_task))
                            requeued_count += 1
                            
                            # Update node status to requeued
                            self._update_node_status(task_id, node_id, 'requeued')
            except Exception as e:
                print(f"Error requeueing tasks for agent {failed_agent_id}: {e}")
        
        return requeued_count
    
    def run_watchdog(self) -> Dict[str, Any]:
        """Run watchdog to check for failed agents and requeue their tasks"""
        health_check = self.check_agent_health()
        failed_agents = health_check['failed_agents']
        
        requeued_summary = {}
        for agent_id in failed_agents:
            requeued_count = self.requeue_failed_tasks(agent_id)
            requeued_summary[agent_id] = requeued_count
            print(f"Requeued {requeued_count} tasks from failed agent {agent_id}")
        
        return {
            'health_check': health_check,
            'requeued_tasks': requeued_summary
        }
    
    async def distribute_execution_levels(self, task_id: str, execution_plan: List[List[str]]) -> Dict[str, Any]:
        """Distribute execution levels to available agents"""
        results = {}
        node_outputs = {"input": None}  # Will be populated with actual input
        
        for level, node_ids in enumerate(execution_plan):
            level_results = await self._execute_level_distributed(task_id, level, node_ids, node_outputs)
            results[f"level_{level}"] = level_results
            
            # Update node outputs for next level
            node_outputs.update(level_results)
            
        return results
    
    async def _execute_level_distributed(self, task_id: str, level: int, node_ids: List[str], 
                                       node_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single level of nodes across distributed agents"""
        level_tasks = []
        
        # For each node in this level, create a task
        for node_id in node_ids:
            node_task = {
                'task_id': task_id,
                'level': level,
                'node_id': node_id,
                'input_data': node_outputs.get('input', {}),  # Simplified input passing
                'assigned_agent': None
            }
            
            # Push node task to Redis queue
            self.redis_client.lpush('node_tasks', json.dumps(node_task))
            level_tasks.append(node_task)
        
        # Wait for results (in a real implementation, this would have timeouts and error handling)
        level_results = {}
        for task in level_tasks:
            # In a real implementation, we would wait for actual results from agents
            # For now, we'll simulate completion
            level_results[task['node_id']] = {
                'status': 'completed',
                'output': f"Output from {task['node_id']}"
            }
            
        return level_results
    
    async def run_distributed_pipeline(self, pipeline_id: str, input_data: Dict[str, Any], 
                                     execution_plan: List[List[str]]) -> Dict[str, Any]:
        """Run a pipeline in distributed mode"""
        task_id = await self.submit_pipeline_task(pipeline_id, input_data, execution_plan)
        
        # Distribute execution levels
        results = await self.distribute_execution_levels(task_id, execution_plan)
        
        # Collect final results
        final_output = None
        if execution_plan and execution_plan[-1]:
            # Get output from last node in last level
            last_level = f"level_{len(execution_plan) - 1}"
            if last_level in results:
                last_node_id = execution_plan[-1][-1]
                if last_node_id in results[last_level]:
                    final_output = results[last_level][last_node_id]
        
        return {
            'task_id': task_id,
            'pipeline_id': pipeline_id,
            'results': results,
            'final_output': final_output,
            'status': 'completed'
        }
