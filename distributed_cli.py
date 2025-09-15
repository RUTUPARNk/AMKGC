#!/usr/bin/env python3
"""
Distributed Pipeline Execution CLI
A command-line interface for managing distributed pipeline execution
"""

import argparse
import asyncio
import json
import sys
import os
from typing import Dict, Any, List

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from distributed.coordinator import DistributedCoordinator
    from distributed.agent import DistributedAgent
    DISTRIBUTED_AVAILABLE = True
except ImportError as e:
    print(f"Error importing distributed components: {e}")
    DISTRIBUTED_AVAILABLE = False

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"{title:^60}")
    print(f"{'='*60}")

def print_status(message: str, status: str = "info"):
    """Print a formatted status message"""
    status_symbols = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️"
    }
    symbol = status_symbols.get(status, "ℹ️")
    print(f"{symbol} {message}")

def start_coordinator(args):
    """Start the distributed coordinator"""
    if not DISTRIBUTED_AVAILABLE:
        print_status("Distributed components not available", "error")
        return
    
    print_header("Distributed Coordinator")
    print_status("Starting coordinator...", "info")
    
    try:
        coordinator = DistributedCoordinator(
            redis_host=args.redis_host,
            redis_port=args.redis_port
        )
        print_status("Coordinator started successfully", "success")
        print(f"Redis: {args.redis_host}:{args.redis_port}")
        
        # Keep running
        print_status("Coordinator is running. Press Ctrl+C to stop.", "info")
        try:
            while True:
                # Run watchdog periodically
                results = coordinator.run_watchdog()
                if results['health_check']['failed_agents']:
                    print_status(f"Detected failed agents: {results['health_check']['failed_agents']}", "warning")
                asyncio.sleep(10)
        except KeyboardInterrupt:
            print_status("Coordinator stopped", "info")
            
    except Exception as e:
        print_status(f"Failed to start coordinator: {e}", "error")

def start_agent(args):
    """Start a distributed agent"""
    if not DISTRIBUTED_AVAILABLE:
        print_status("Distributed components not available", "error")
        return
    
    print_header("Distributed Agent")
    print_status("Starting agent...", "info")
    
    try:
        # Parse capabilities
        capabilities = args.capabilities.split(',') if args.capabilities else ['ollama', 'function']
        
        agent = DistributedAgent(
            agent_id=args.agent_id,
            redis_host=args.redis_host,
            redis_port=args.redis_port,
            capabilities=capabilities
        )
        
        print_status(f"Agent {args.agent_id} started successfully", "success")
        print(f"Redis: {args.redis_host}:{args.redis_port}")
        print(f"Capabilities: {capabilities}")
        
        # Start the agent
        print_status("Agent is running. Press Ctrl+C to stop.", "info")
        agent.start()
        
    except Exception as e:
        print_status(f"Failed to start agent: {e}", "error")

def list_agents(args):
    """List active agents"""
    if not DISTRIBUTED_AVAILABLE:
        print_status("Distributed components not available", "error")
        return
    
    print_header("Active Agents")
    
    try:
        coordinator = DistributedCoordinator(
            redis_host=args.redis_host,
            redis_port=args.redis_port
        )
        
        agents = coordinator.get_active_agents()
        if agents:
            for agent in agents:
                print(f"- {agent['agent_id']} ({agent['status']})")
                print(f"  Capabilities: {agent['capabilities']}")
                print(f"  Last heartbeat: {agent['last_heartbeat']}")
                print()
        else:
            print_status("No active agents found", "info")
            
    except Exception as e:
        print_status(f"Failed to list agents: {e}", "error")

def run_watchdog(args):
    """Run the watchdog mechanism"""
    if not DISTRIBUTED_AVAILABLE:
        print_status("Distributed components not available", "error")
        return
    
    print_header("Watchdog Check")
    
    try:
        coordinator = DistributedCoordinator(
            redis_host=args.redis_host,
            redis_port=args.redis_port
        )
        
        results = coordinator.run_watchdog()
        
        print(f"Active agents: {results['health_check']['active_agents']}")
        print(f"Failed agents: {results['health_check']['failed_agents']}")
        
        if results['requeued_tasks']:
            print("\nRequeued tasks:")
            for agent_id, count in results['requeued_tasks'].items():
                print(f"- {agent_id}: {count} tasks")
        else:
            print("\nNo tasks were requeued")
            
        print_status("Watchdog check completed", "success")
        
    except Exception as e:
        print_status(f"Watchdog check failed: {e}", "error")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Distributed Pipeline Execution CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  distributed_cli.py coordinator --redis-host localhost --redis-port 6379
  distributed_cli.py agent --agent-id agent-1 --capabilities ollama,function
  distributed_cli.py agents --redis-host localhost --redis-port 6379
  distributed_cli.py watchdog --redis-host localhost --redis-port 6379
        """
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Common arguments
    common_args = argparse.ArgumentParser(add_help=False)
    common_args.add_argument('--redis-host', default='localhost', help='Redis host (default: localhost)')
    common_args.add_argument('--redis-port', type=int, default=6379, help='Redis port (default: 6379)')
    
    # Coordinator command
    coordinator_parser = subparsers.add_parser('coordinator', help='Start distributed coordinator', 
                                             parents=[common_args])
    
    # Agent command
    agent_parser = subparsers.add_parser('agent', help='Start distributed agent', 
                                       parents=[common_args])
    agent_parser.add_argument('--agent-id', required=True, help='Agent ID')
    agent_parser.add_argument('--capabilities', help='Agent capabilities (comma-separated)')
    
    # Agents command
    agents_parser = subparsers.add_parser('agents', help='List active agents', 
                                        parents=[common_args])
    
    # Watchdog command
    watchdog_parser = subparsers.add_parser('watchdog', help='Run watchdog check', 
                                          parents=[common_args])
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == 'coordinator':
        start_coordinator(args)
    elif args.command == 'agent':
        start_agent(args)
    elif args.command == 'agents':
        list_agents(args)
    elif args.command == 'watchdog':
        run_watchdog(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
