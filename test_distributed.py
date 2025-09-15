"""
Test script for distributed execution components
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_distributed_components():
    try:
        # Import the distributed components
        from distributed.coordinator import DistributedCoordinator
        from distributed.agent import DistributedAgent
        
        print("✅ Successfully imported distributed components")
        
        # Test coordinator instantiation
        coordinator = DistributedCoordinator()
        print("✅ Successfully instantiated DistributedCoordinator")
        
        # Test agent instantiation
        agent = DistributedAgent("test-agent-1")
        print("✅ Successfully instantiated DistributedAgent")
        
        # Check if required methods exist
        required_coordinator_methods = [
            '__init__',
            'submit_pipeline_task',
            'monitor_task_progress',
            'collect_task_results',
            'register_agent',
            'get_active_agents',
            'distribute_execution_levels',
            'run_distributed_pipeline'
        ]
        
        missing_coordinator_methods = []
        for method in required_coordinator_methods:
            if not hasattr(DistributedCoordinator, method):
                missing_coordinator_methods.append(method)
        
        if missing_coordinator_methods:
            print(f"❌ Missing coordinator methods: {missing_coordinator_methods}")
        else:
            print("✅ All coordinator methods are present")
        
        required_agent_methods = [
            '__init__',
            'start',
            'stop',
            '_register_with_coordinator',
            '_listen_for_tasks',
            '_execute_task',
            '_report_result',
            '_send_heartbeat',
            'execute_node'
        ]
        
        missing_agent_methods = []
        for method in required_agent_methods:
            if not hasattr(DistributedAgent, method):
                missing_agent_methods.append(method)
        
        if missing_agent_methods:
            print(f"❌ Missing agent methods: {missing_agent_methods}")
        else:
            print("✅ All agent methods are present")
        
        print("✅ Distributed execution components verification completed")
        
    except ImportError as e:
        print(f"❌ Failed to import distributed components: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_distributed_components()
