#!/usr/bin/env python3
"""
Benchmark script to compare Ollama vs Qwen throughput
"""

import asyncio
import time
import statistics
from typing import List, Tuple
from backend.services.llm_abstraction import stream_response

async def benchmark_provider(provider: str, model: str, prompt: str, iterations: int = 3) -> dict:
    """Benchmark a specific provider and model"""
    print(f"Benchmarking {provider} ({model})...")
    
    times = []
    first_token_latencies = []
    token_counts = []
    
    for i in range(iterations):
        print(f"  Iteration {i+1}/{iterations}")
        start_time = time.time()
        first_token_time = None
        token_count = 0
        
        try:
            async for token in stream_response(model, prompt, provider):
                if token_count == 0:
                    first_token_time = time.time()
                token_count += 1
                # Small delay to prevent overwhelming the system
                if token_count % 10 == 0:
                    await asyncio.sleep(0.001)
        except Exception as e:
            print(f"    Error in iteration {i+1}: {e}")
            continue
            
        end_time = time.time()
        total_time = end_time - start_time
        
        if first_token_time is not None:
            first_token_latency = first_token_time - start_time
            first_token_latencies.append(first_token_latency)
        
        times.append(total_time)
        token_counts.append(token_count)
        
        if first_token_time is not None:
            print(f"    Time: {total_time:.2f}s, First token: {first_token_latency*1000:.0f}ms, Tokens: {token_count}, Rate: {token_count/total_time:.2f} tokens/sec")
        else:
            print(f"    Time: {total_time:.2f}s, Tokens: {token_count}, Rate: {token_count/total_time:.2f} tokens/sec")
        
        # Wait between iterations
        await asyncio.sleep(1)
    
    if times:
        avg_time = statistics.mean(times)
        avg_first_token_latency = statistics.mean(first_token_latencies) if first_token_latencies else 0
        avg_tokens = statistics.mean(token_counts)
        avg_rate = statistics.mean([t/c if c > 0 else 0 for t, c in zip(times, token_counts)])
        
        return {
            "provider": provider,
            "model": model,
            "avg_time": avg_time,
            "avg_first_token_latency": avg_first_token_latency,
            "avg_tokens": avg_tokens,
            "avg_rate": avg_rate,
            "min_time": min(times),
            "max_time": max(times),
            "token_counts": token_counts
        }
    else:
        return {
            "provider": provider,
            "model": model,
            "error": "No successful iterations"
        }

async def run_benchmarks():
    """Run benchmarks for both providers"""
    print("Starting LLM Throughput Benchmark")
    print("=" * 50)
    
    # Test prompts of different lengths
    short_prompt = "What is the capital of France?"
    medium_prompt = """Explain the process of photosynthesis in detail. 
    Include the chemical reactions involved, the role of chlorophyll, 
    and how plants convert light energy into chemical energy."""
    
    long_prompt = """Write a comprehensive analysis of the impact of artificial intelligence 
    on modern society. Discuss both positive and negative effects across various sectors 
    including healthcare, education, employment, and privacy. Consider ethical implications 
    and potential future developments. Provide specific examples and statistics where relevant. 
    Also address the role of government regulation and the responsibility of technology companies. 
    Finally, offer recommendations for maximizing benefits while minimizing risks.""" * 3
    
    results = []
    
    # Benchmark Qwen
    try:
        qwen_result = await benchmark_provider("qwen", "qwen-72b-chat", short_prompt, 3)
        results.append(qwen_result)
    except Exception as e:
        print(f"Error benchmarking Qwen: {e}")
        results.append({"provider": "qwen", "error": str(e)})
    
    # Benchmark Ollama (if available)
    try:
        ollama_result = await benchmark_provider("ollama", "llama2", short_prompt, 3)
        results.append(ollama_result)
    except Exception as e:
        print(f"Error benchmarking Ollama: {e}")
        results.append({"provider": "ollama", "error": str(e)})
    
    # Print summary
    print("\nBenchmark Summary")
    print("=" * 50)
    
    for result in results:
        if "error" in result:
            print(f"{result['provider']}: ERROR - {result['error']}")
        else:
            print(f"{result['provider']} ({result['model']}):")
            print(f"  Average time: {result['avg_time']:.2f}s")
            if result.get('avg_first_token_latency', 0) > 0:
                print(f"  Average first-token latency: {result['avg_first_token_latency']*1000:.0f}ms")
            print(f"  Average tokens: {result['avg_tokens']:.0f}")
            print(f"  Average rate: {result['avg_rate']:.2f} tokens/sec")
            print(f"  Min time: {result['min_time']:.2f}s")
            print(f"  Max time: {result['max_time']:.2f}s")
            print()
    
    return results

if __name__ == "__main__":
    # Run the benchmarks
    results = asyncio.run(run_benchmarks())
    print("\nBenchmark completed.")
