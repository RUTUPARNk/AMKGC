"""
Test script for Ollama Supervisor Service
"""

import sys
import os
import time

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import the supervisor service
try:
    from services.ollama_supervisor import ollama_supervisor_service
except ImportError:
    # If running from the root directory
    sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
    from backend.services.ollama_supervisor import ollama_supervisor_service

def test_supervisor():
    """Test the Ollama supervisor service"""
    print("Testing Ollama Supervisor Service...")
    
    # Start the supervisor
    print("Starting supervisor...")
    ollama_supervisor_service.start_supervisor()
    
    # Let it run for a bit
    print("Supervisor running for 10 seconds...")
    time.sleep(10)
    
    # Check if it's running
    if ollama_supervisor_service.supervisor_thread and ollama_supervisor_service.supervisor_thread.is_alive():
        print("✅ Supervisor is running correctly")
    else:
        print("❌ Supervisor is not running")
    
    # Stop the supervisor
    print("Stopping supervisor...")
    ollama_supervisor_service.stop_supervisor()
    
    print("Test completed.")

if __name__ == "__main__":
    test_supervisor()
