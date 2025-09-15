#!/usr/bin/env python3
"""
Setup and run script for Node LLM System
This script will help you get the system running quickly.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def print_step(step, message):
    print(f"\n{'='*50}")
    print(f"STEP {step}: {message}")
    print(f"{'='*50}")

def check_command(command):
    """Check if a command is available"""
    try:
        subprocess.run([command, '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        print(f"Error: {e.stderr}")
        return False

def check_service(url, service_name, timeout=5):
    """Check if a service is running"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"✅ {service_name} is running")
            return True
        else:
            print(f"⚠️  {service_name} responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print(f"❌ {service_name} is not running")
        return False

def main():
    print("🚀 Node LLM System Setup and Run Script")
    print("This script will help you get the system running quickly.")
    
    # Step 1: Check prerequisites
    print_step(1, "Checking Prerequisites")
    
    prerequisites = {
        'python': 'Python 3.8+',
        'pip': 'pip',
        'ollama': 'Ollama',
        'redis-server': 'Redis Server',
        'psql': 'PostgreSQL Client'
    }
    
    missing_prereqs = []
    for cmd, name in prerequisites.items():
        if check_command(cmd):
            print(f"✅ {name} is installed")
        else:
            print(f"❌ {name} is not installed")
            missing_prereqs.append(name)
    
    if missing_prereqs:
        print(f"\n⚠️  Missing prerequisites: {', '.join(missing_prereqs)}")
        print("Please install the missing prerequisites before continuing.")
        print("\nInstallation commands:")
        print("- Python: https://python.org/downloads/")
        print("- Ollama: https://ollama.ai/download")
        print("- Redis: https://redis.io/download")
        print("- PostgreSQL: https://postgresql.org/download/")
        return
    
    # Step 2: Install Python dependencies
    print_step(2, "Installing Python Dependencies")
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return
    
    # Step 3: Check if Ollama is running
    print_step(3, "Checking Ollama")
    if not check_service("http://localhost:11434/api/tags", "Ollama"):
        print("\n🔄 Starting Ollama...")
        print("Please make sure Ollama is running. You can start it with:")
        print("ollama serve")
        print("\nThen in another terminal, pull a model:")
        print("ollama pull llama3")
        input("\nPress Enter when Ollama is running...")
    
    # Step 4: Check if Redis is running
    print_step(4, "Checking Redis")
    if not check_service("http://localhost:6379", "Redis", timeout=1):
        print("\n🔄 Starting Redis...")
        print("Please start Redis server. You can start it with:")
        print("redis-server")
        input("\nPress Enter when Redis is running...")
    
    # Step 5: Check if PostgreSQL is running
    print_step(5, "Checking PostgreSQL")
    try:
        result = subprocess.run(["psql", "-h", "localhost", "-U", "postgres", "-c", "SELECT 1"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ PostgreSQL is running")
        else:
            print("❌ PostgreSQL is not accessible")
            print("Please make sure PostgreSQL is running and accessible")
            input("\nPress Enter when PostgreSQL is running...")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ PostgreSQL is not accessible")
        print("Please make sure PostgreSQL is running and accessible")
        input("\nPress Enter when PostgreSQL is running...")
    
    # Step 6: Create database
    print_step(6, "Setting up Database")
    print("Creating database 'node_llm_system'...")
    try:
        subprocess.run(["createdb", "node_llm_system"], check=True, capture_output=True)
        print("✅ Database created successfully")
    except subprocess.CalledProcessError:
        print("⚠️  Database might already exist or creation failed")
    
    # Step 7: Run database migrations
    print_step(7, "Running Database Migrations")
    migration_file = Path("database/migrations/001_initial_schema.sql")
    if migration_file.exists():
        try:
            subprocess.run([
                "psql", "-h", "localhost", "-U", "postgres", "-d", "node_llm_system", 
                "-f", str(migration_file)
            ], check=True, capture_output=True)
            print("✅ Database migrations applied successfully")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Migration failed: {e}")
    else:
        print("⚠️  Migration file not found")
    
    # Step 8: Start the backend
    print_step(8, "Starting Backend Server")
    print("Starting the Node LLM System backend...")
    print("The API will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server")
    print("="*50)
    
    # Start the backend
    try:
        subprocess.run([sys.executable, "start_backend.py"])
    except KeyboardInterrupt:
        print("\n\n🛑 Backend server stopped")
        print("Thank you for using Node LLM System!")

if __name__ == "__main__":
    main() 