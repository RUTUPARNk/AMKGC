#!/usr/bin/env python3
"""
Distributed Pipeline Execution Worker
Standalone worker that executes pipeline nodes assigned by the coordinator
"""

import asyncio
import json
import redis
import time
import uuid
import os
from typing import Dict, Any, List
from datetime import datetime

# Add the backend directory to the path to import pipeline executor
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from pipeline.executor import PipelineExecutor
    PIPELINE_EXECUTOR_AVAILABLE = True
except ImportError:
    PIPELINE_EXECUTOR_AVAILABLE = False
    PipelineExecutor = None
    print("Warning: PipelineExecutor not available")


class DistributedWorker:
    """Worker that executes pipeline nodes"""
    
    def __init__(self):
        """Initialize the worker with Redis connection"""
        # Get configuration from environment variables
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.agent_id = os.getenv('AGENT_ID', f"worker-{uuid.uuid4().hex[:8]}")
        
        # Connect to Redis
        self.redis_client = redis.Redis(
            host=self.redis_host, 
            port=self.redis_port, 
            decode_responses=True
        )
        
        # Task queue names
        self.node_task_queue = 'node_tasks'
        self.node_results_queue = 'node_results'
        self.agent_registry = 'active_agents'
        
        # Initialize pipeline executor
        self.executor = PipelineExecutor() if PIPELINE_EXECUTOR_AVAILABLE else None
        self.running = False
        
    def start(self):
        """Start the worker to listen for tasks"""
        self.running = True
        print(f"Worker {self.agent_id} started, listening for tasks...")
        
        # Register with coordinator
        self._register_with_coordinator()
        
        # Start listening for tasks
        self._listen_for_tasks()
    
    def stop(self):
        """Stop the worker"""
        self.running = False
        print(f"Worker {self.agent_id} stopped")
        
        # Remove from registry
        try:
            self.redis_client.hdel(self.agent_registry, self.agent_id)
        except Exception as e:
            print(f"Failed to remove worker from registry: {e}")
    
    def _register_with_coordinator(self):
        """Register this worker with the coordinator"""
        try:
            agent_info = {
                'agent_id': self.agent_id,
                'capabilities': json.dumps(['ollama', 'openai', 'anthropic', 'function']),
                'last_heartbeat': datetime.now().isoformat(),
                'status': 'active'
            }
            
            self.redis_client.hset(self.agent_registry, self.agent_id, json.dumps(agent_info))
            print(f"Worker {self.agent_id} registered with coordinator")
        except Exception as e:
            print(f"Failed to register worker: {e}")
    
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
                    
                    print(f"Worker {self.agent_id} received task: {task['node_id']}")
                    
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
            node_config = task.get('node_config', {})
            
            print(f"Executing node {node_id} with input: {input_data}")
            
            # If we have a pipeline executor and node config, use it
            if PIPELINE_EXECUTOR_AVAILABLE and self.executor and node_config:
                # Execute the node using the pipeline executor
                result = asyncio.run(self.executor._execute_node(node_config, input_data))
                result['worker_id'] = self.agent_id
                return result
            else:
                # Fallback execution
                time.sleep(2)  # Simulate work
                result = {
                    'node_id': node_id,
                    'status': 'completed',
                    'output': f"Processed by worker {self.agent_id}",
                    'execution_time': 2.0,
                    'timestamp': datetime.now().isoformat(),
                    'worker_id': self.agent_id
                }
                return result
                
        except Exception as e:
            return {
                'node_id': task.get('node_id'),
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'worker_id': self.agent_id
            }
    
    def _report_result(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Report task result back to coordinator"""
        try:
            result_data = {
                'task_id': task['task_id'],
                'node_id': task['node_id'],
                'result': result,
                'worker_id': self.agent_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Push result to results queue
            self.redis_client.lpush(self.node_results_queue, json.dumps(result_data))
            print(f"Worker {self.agent_id} reported result for {task['node_id']}")
            
        except Exception as e:
            print(f"Failed to report result: {e}")
    
    def _send_heartbeat(self):
        """Send heartbeat to coordinator"""
        try:
            agent_info = {
                'agent_id': self.agent_id,
                'capabilities': json.dumps(['ollama', 'openai', 'anthropic', 'function']),
                'last_heartbeat': datetime.now().isoformat(),
                'status': 'active'
            }
            
            self.redis_client.hset(self.agent_registry, self.agent_id, json.dumps(agent_info))
        except Exception as e:
            print(f"Failed to send heartbeat: {e}")


def main():
    """Main entry point"""
    worker = DistributedWorker()
    
    try:
        worker.start()
    except KeyboardInterrupt:
        print("\nShutting down worker...")
        worker.stop()
    except Exception as e:
        print(f"Worker error: {e}")
        worker.stop()


if __name__ == "__main__":
    main()
