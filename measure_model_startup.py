#!/usr/bin/env python3
"""
Script to measure model startup times for different LLM providers
"""

import asyncio
import time
import statistics
from typing import List, Dict
from backend.services.llm_abstraction import stream_response
from backend.services.ollama_warmup import ollama_warmup_service

async def measure_cold_start(provider: str, model: str, prompt: str = "Hello, world!") -> float:
    """Measure cold start time for a model"""
    print(f"Measuring cold start for {provider} ({model})...")
    
    start_time = time.time()
    
    try:
        # For Ollama, we can check if it's already warmed up
        if provider == "ollama":
            if not ollama_warmup_service.is_ready:
                print("  Ollama model not ready, this will include warmup time")
        
        # Send a small request to trigger model loading
        async for token in stream_response(model, prompt, provider):
            # Just consume the first token to trigger the model
            break
    except Exception as e:
        print(f"  Error: {e}")
        return -1
    
    end_time = time.time()
    cold_start_time = end_time - start_time
    
    print(f"  Cold start time: {cold_start_time:.2f}s")
    return cold_start_time

async def run_startup_benchmarks():
    """Run startup time benchmarks for different models"""
    print("Model Startup Time Benchmark")
    print("=" * 40)
    
    # Test models
    models_to_test = [
        {"provider": "qwen", "model": "qwen-turbo", "prompt": "Hi"},
        {"provider": "ollama", "model": "llama2", "prompt": "Hi"},
        {"provider": "ollama", "model": "mistral", "prompt": "Hi"},
    ]
    
    results = []
    
    for model_info in models_to_test:
        provider = model_info["provider"]
        model = model_info["model"]
        prompt = model_info["prompt"]
        
        # Run multiple iterations for statistical significance
        iterations = 3
        times = []
        
        for i in range(iterations):
            print(f"\nTesting {provider} ({model}) - Iteration {i+1}/{iterations}")
            start_time = await measure_cold_start(provider, model, prompt)
            if start_time > 0:
                times.append(start_time)
            
            # Wait between iterations
            await asyncio.sleep(2)
        
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            
            result = {
                "provider": provider,
                "model": model,
                "avg_startup_time": avg_time,
                "min_startup_time": min_time,
                "max_startup_time": max_time,
                "iterations": len(times)
            }
            results.append(result)
            
            print(f"\n{provider} ({model}) Summary:")
            print(f"  Average startup time: {avg_time:.2f}s")
            print(f"  Min startup time: {min_time:.2f}s")
            print(f"  Max startup time: {max_time:.2f}s")
        else:
            results.append({
                "provider": provider,
                "model": model,
                "error": "All iterations failed"
            })
    
    # Print final summary
    print("\n" + "=" * 50)
    print("FINAL STARTUP TIME SUMMARY")
    print("=" * 50)
    
    for result in results:
        if "error" in result:
            print(f"{result['provider']} ({result['model']}): ERROR - {result['error']}")
        else:
            print(f"{result['provider']} ({result['model']}): {result['avg_startup_time']:.2f}s avg startup time")
    
    return results

if __name__ == "__main__":
    # Run the benchmarks
    results = asyncio.run(run_startup_benchmarks())
    print("\nStartup time benchmark completed.")
