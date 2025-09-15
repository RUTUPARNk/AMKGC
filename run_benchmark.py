#!/usr/bin/env python3
"""
Comprehensive benchmark script for Ollama models
This script will:
1. Verify Ollama installation
2. Run cold start benchmarks
3. Trigger backend warm-up
4. Run warmed benchmarks
5. Test health checks
6. Generate performance comparison table
"""

import subprocess
import time
import json
import sys
import requests
import re
from typing import Dict, List, Tuple

# Configuration
OLLAMA_URL = "http://localhost:11434"
BACKEND_URL = "http://localhost:8000"
TEST_PROMPT = "Hello, world!"
WARMUP_PROMPT = "Hello again"


def check_ollama_installed() -> bool:
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, text=True, timeout=10)
        print(f"✅ Ollama version: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ Ollama is not installed or not in PATH")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False


def get_available_models() -> List[str]:
    """Get list of available models"""
    try:
        result = subprocess.run(['ollama', 'list'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            models = []
            for line in lines:
                if line.strip():
                    model_name = line.split()[0]
                    models.append(model_name)
            return models
        else:
            print(f"❌ Error listing models: {result.stderr}")
            return []
    except Exception as e:
        print(f"❌ Error getting model list: {e}")
        return []


def run_cold_start_benchmark(model: str) -> Tuple[float, float, float]:
    """Run cold start benchmark for a model"""
    print(f"\nRunning cold start benchmark for {model}...")
    
    try:
        start_time = time.time()
        result = subprocess.run([
            'ollama', 'run', model, TEST_PROMPT
        ], capture_output=True, text=True, timeout=60)
        end_time = time.time()
        
        if result.returncode == 0:
            total_time = end_time - start_time
            response = result.stdout.strip()
            
            # Estimate tokens (rough approximation)
            # Assuming average of 4 characters per token
            token_count = len(response) / 4
            throughput = token_count / total_time if total_time > 0 else 0
            
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Response length: {len(response)} characters")
            print(f"  Estimated tokens: {token_count:.0f}")
            print(f"  Throughput: {throughput:.2f} tokens/sec")
            
            return total_time, 0, throughput  # First token time not directly measurable via CLI
        else:
            print(f"  ❌ Error: {result.stderr}")
            return 0, 0, 0
    except Exception as e:
        print(f"  ❌ Error running benchmark: {e}")
        return 0, 0, 0


def trigger_backend_warmup() -> bool:
    """Trigger backend warm-up by restarting the backend"""
    print("\nTriggering backend warm-up...")
    
    # In a real scenario, we would restart the backend service
    # For now, we'll simulate by calling the warmup service directly
    try:
        # This would normally be done by restarting the backend
        # which would trigger the warmup in main.py
        print("  Backend warm-up triggered (simulated)")
        return True
    except Exception as e:
        print(f"  ❌ Error triggering warm-up: {e}")
        return False


def run_api_benchmark(model: str) -> Tuple[float, float, float]:
    """Run benchmark using Ollama API for more precise measurements"""
    print(f"\nRunning API benchmark for {model}...")
    
    try:
        start_time = time.time()
        first_token_time = None
        response_text = ""
        
        # Using streaming to measure first token latency
        with requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": TEST_PROMPT,
                "stream": True
            },
            stream=True,
            timeout=60
        ) as response:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if first_token_time is None:
                        first_token_time = time.time() - start_time
                    response_text += data.get("response", "")
                    if data.get("done", False):
                        break
        
        total_time = time.time() - start_time
        
        # Estimate tokens
        token_count = len(response_text) / 4
        throughput = token_count / total_time if total_time > 0 else 0
        
        print(f"  First token latency: {first_token_time*1000:.0f}ms")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Response length: {len(response_text)} characters")
        print(f"  Estimated tokens: {token_count:.0f}")
        print(f"  Throughput: {throughput:.2f} tokens/sec")
        
        return total_time, first_token_time, throughput
    except Exception as e:
        print(f"  ❌ Error running API benchmark: {e}")
        return 0, 0, 0


def check_health_status() -> bool:
    """Check backend health status"""
    print("\nChecking health status...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"  ✅ Backend health check successful")
            for service in health_data:
                print(f"    {service['name']}: {service['status']}")
            return True
        else:
            print(f"  ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Error checking health: {e}")
        return False


def main():
    """Main benchmark function"""
    print("=" * 60)
    print("Ollama Model Performance Benchmark")
    print("=" * 60)
    
    # 1. Verify Ollama installation
    if not check_ollama_installed():
        print("Cannot proceed without Ollama installed.")
        sys.exit(1)
    
    # 2. Get available models
    models = get_available_models()
    if not models:
        print("No models available for benchmarking.")
        sys.exit(1)
    
    print(f"\nFound {len(models)} models: {', '.join(models)}")
    
    # 3. Run cold start benchmarks
    print("\n" + "=" * 40)
    print("COLD START BENCHMARKS")
    print("=" * 40)
    
    results = {}
    for model in models:
        if model in ["llama3:latest", "qwen3:latest"]:  # Focus on key models
            print(f"\nTesting {model}...")
            total_time, first_token, throughput = run_api_benchmark(model)
            results[model] = {
                "cold_total": total_time,
                "cold_first_token": first_token,
                "cold_throughput": throughput
            }
    
    # 4. Trigger backend warm-up
    print("\n" + "=" * 40)
    print("WARM-UP PHASE")
    print("=" * 40)
    
    trigger_backend_warmup()
    
    # Wait a bit for warm-up to complete
    print("Waiting for warm-up to complete...")
    time.sleep(5)
    
    # 5. Run warmed benchmarks
    print("\n" + "=" * 40)
    print("WARMED BENCHMARKS")
    print("=" * 40)
    
    for model in models:
        if model in ["llama3:latest", "qwen3:latest"]:  # Focus on key models
            print(f"\nTesting warmed {model}...")
            total_time, first_token, throughput = run_api_benchmark(model)
            if model in results:
                results[model].update({
                    "warm_total": total_time,
                    "warm_first_token": first_token,
                    "warm_throughput": throughput
                })
    
    # 6. Check health status
    print("\n" + "=" * 40)
    print("HEALTH CHECK")
    print("=" * 40)
    
    check_health_status()
    
    # 7. Generate results table
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS")
    print("=" * 80)
    
    print(f"{'Model':<20} {'Cold 1st Token (ms)':<20} {'Warm 1st Token (ms)':<20} {'Throughput (tok/s)':<20}")
    print("-" * 80)
    
    for model, data in results.items():
        cold_first = data.get('cold_first_token', 0) * 1000 if data.get('cold_first_token', 0) > 0 else "N/A"
        warm_first = data.get('warm_first_token', 0) * 1000 if data.get('warm_first_token', 0) > 0 else "N/A"
        throughput = data.get('cold_throughput', 0)
        
        print(f"{model:<20} {cold_first:<20.0f} {warm_first:<20.0f} {throughput:<20.2f}")
    
    print("\nBenchmark completed.")

if __name__ == "__main__":
    main()
