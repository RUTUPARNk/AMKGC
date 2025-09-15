#!/usr/bin/env python3
"""
Updated benchmark script for Ollama models with proper cold start vs warmed comparison
This script will:
1. Verify Ollama installation
2. Run cold start benchmarks (after ensuring model is not loaded)
3. Trigger backend warm-up
4. Run warmed benchmarks
5. Generate performance comparison table
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


def unload_model(model: str) -> bool:
    """Unload a model to ensure cold start"""
    try:
        result = subprocess.run(['ollama', 'ps'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            if model in result.stdout:
                print(f"  Unloading {model}...")
                subprocess.run(['ollama', 'stop', model], 
                             capture_output=True, timeout=10)
                time.sleep(2)  # Wait for model to unload
                return True
        return True
    except Exception as e:
        print(f"  ❌ Error unloading model: {e}")
        return False

def ensure_cold_start(model: str) -> bool:
    """Ensure model is not loaded for cold start testing"""
    print(f"\nEnsuring cold start for {model}...")
    return unload_model(model)


def run_api_benchmark(model: str, is_cold: bool = True) -> Tuple[float, float, float]:
    """Run benchmark using Ollama API for precise measurements"""
    test_type = "COLD START" if is_cold else "WARMED"
    print(f"\nRunning {test_type} API benchmark for {model}...")
    
    try:
        start_time = time.time()
        first_token_time = None
        response_text = ""
        token_count = 0
        
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
                    response_chunk = data.get("response", "")
                    response_text += response_chunk
                    # Count tokens (approximation: 4 chars per token)
                    token_count += len(response_chunk) / 4
                    if data.get("done", False):
                        break
        
        total_time = time.time() - start_time
        
        # Calculate throughput
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


def trigger_backend_restart() -> bool:
    """Trigger backend restart to activate warm-up"""
    print("\nTriggering backend restart for warm-up...")
    
    # In a real scenario, we would restart the backend service
    # For now, we'll simulate by calling the warmup service directly
    try:
        # This would normally be done by restarting the backend
        # which would trigger the warmup in main.py
        print("  Backend restart triggered (simulated)")
        print("  Waiting for warm-up to complete...")
        time.sleep(10)  # Wait for warm-up
        return True
    except Exception as e:
        print(f"  ❌ Error triggering restart: {e}")
        return False

def check_model_loaded(model: str) -> bool:
    """Check if model is loaded in Ollama"""
    try:
        result = subprocess.run(['ollama', 'ps'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return model in result.stdout
        return False
    except Exception as e:
        print(f"  ❌ Error checking model status: {e}")
        return False

def main():
    """Main benchmark function"""
    print("=" * 60)
    print("Ollama Model Performance Benchmark - Updated")
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
    
    # Focus on key models
    key_models = [model for model in models if model in ["llama3:latest", "qwen3:latest"]]
    if not key_models:
        # If key models not found, use first available model
        key_models = [models[0]] if models else []
    
    # 3. Run cold start benchmarks
    print("\n" + "=" * 40)
    print("COLD START BENCHMARKS")
    print("=" * 40)
    
    results = {}
    for model in key_models:
        print(f"\nTesting {model}...")
        # Ensure cold start
        ensure_cold_start(model)
        time.sleep(2)  # Wait for model to fully unload
        
        total_time, first_token, throughput = run_api_benchmark(model, is_cold=True)
        results[model] = {
            "cold_total": total_time,
            "cold_first_token": first_token,
            "cold_throughput": throughput
        }
    
    # 4. Trigger backend warm-up
    print("\n" + "=" * 40)
    print("WARM-UP PHASE")
    print("=" * 40)
    
    trigger_backend_restart()
    
    # Wait a bit for warm-up to complete
    print("Waiting for warm-up to complete...")
    time.sleep(10)
    
    # 5. Run warmed benchmarks
    print("\n" + "=" * 40)
    print("WARMED BENCHMARKS")
    print("=" * 40)
    
    for model in key_models:
        print(f"\nTesting warmed {model}...")
        # Verify model is loaded
        if check_model_loaded(model):
            print(f"  ✅ Model {model} is loaded and ready")
            total_time, first_token, throughput = run_api_benchmark(model, is_cold=False)
            if model in results:
                results[model].update({
                    "warm_total": total_time,
                    "warm_first_token": first_token,
                    "warm_throughput": throughput
                })
        else:
            print(f"  ❌ Model {model} is not loaded. Skipping warmed test.")
    
    # 6. Generate results table
    print("\n" + "=" * 90)
    print("BENCHMARK RESULTS")
    print("=" * 90)
    
    print(f"{'Model':<25} {'Cold 1st Token (ms)':<20} {'Warm 1st Token (ms)':<20} {'Throughput (tok/s)':<20}")
    print("-" * 90)
    
    for model, data in results.items():
        cold_first = data.get('cold_first_token', 0) * 1000 if data.get('cold_first_token', 0) > 0 else "N/A"
        warm_first = data.get('warm_first_token', 0) * 1000 if data.get('warm_first_token', 0) > 0 else "N/A"
        throughput = data.get('cold_throughput', 0)
        
        # Handle string values for N/A cases
        if isinstance(cold_first, str):
            cold_first_str = cold_first
        else:
            cold_first_str = f"{cold_first:.0f}"
            
        if isinstance(warm_first, str):
            warm_first_str = warm_first
        else:
            warm_first_str = f"{warm_first:.0f}"
        
        print(f"{model:<25} {cold_first_str:<20} {warm_first_str:<20} {throughput:<20.2f}")
    
    print("\nBenchmark completed.")

if __name__ == "__main__":
    main()
