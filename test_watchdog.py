"""
Test script for watchdog/heartbeat recovery mechanism
"""

import sys
import os
import time
import json
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_watchdog_mechanism():
    try:
        # Import the distributed components
        from distributed.coordinator import DistributedCoordinator
        
        print("✅ Successfully imported distributed components")
        
        # Test coordinator instantiation
        coordinator = DistributedCoordinator()
        print("✅ Successfully instantiated DistributedCoordinator")
        
        # Check if required methods exist
        required_methods = [
            '__init__',
            'check_agent_health',
            'requeue_failed_tasks',
            'run_watchdog',
            '_initialize_task_monitoring',
            '_update_node_assignment',
            '_update_node_status'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(DistributedCoordinator, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing coordinator methods: {missing_methods}")
        else:
            print("✅ All watchdog methods are present")
        
        # Test agent health checking
        print("\nTesting agent health checking...")
        health = coordinator.check_agent_health()
        print(f"Health check results: {health}")
        
        # Test watchdog run
        print("\nTesting watchdog...")
        watchdog_results = coordinator.run_watchdog()
        print(f"Watchdog results: {watchdog_results}")
        
        print("✅ Watchdog mechanism verification completed")
        
    except ImportError as e:
        print(f"❌ Failed to import distributed components: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_watchdog_mechanism()
