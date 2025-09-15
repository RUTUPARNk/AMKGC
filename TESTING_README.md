# LLM System Testing Guide

This document provides instructions for running various tests on the Node-LLM system.

## Performance Tests

Run the performance test script to evaluate system performance with multiple sessions and long prompts:

```bash
python performance_test.py
```

This script tests:
1. Single session with long prompt (>10k tokens)
2. Multiple concurrent sessions

## Benchmark Tests

Run the benchmark script to compare throughput between Ollama and Qwen:

```bash
python benchmark_llm_throughput.py
```

This script benchmarks both providers with various prompt lengths.

## Failure Simulation Tests

The system now includes improved error handling for various failure scenarios:

1. **Ollama killed mid-stream**: The frontend will display a connection error message
2. **Backend internet cut**: The frontend will display a network error message
3. **Invalid provider/model**: The backend validates requests and sends error messages to the frontend

## UX Edge Cases

The system handles these edge cases gracefully:

1. **Provider switching mid-session**: Works seamlessly
2. **Ollama with no models**: Shows appropriate error message and disables send button

## Metrics Logging

The system logs performance metrics:

1. **Backend**: Tokens per second during streaming
2. **Frontend**: Chunks per second and graph nodes per second

These metrics are logged to the console and can be used for performance analysis.

## Running the Tests

1. Ensure the backend server is running:
   ```bash
   python start_backend.py
   ```

2. Run the performance tests:
   ```bash
   python performance_test.py
   ```

3. Run the benchmark tests:
   ```bash
   python benchmark_llm_throughput.py
   ```

4. For manual testing of failure scenarios:
   - Kill Ollama during a streaming response to test connection error handling
   - Disconnect internet during a Qwen request to test network error handling
   - Send invalid provider/model combinations to test validation

## Test Results

Test results are displayed in the console. For detailed analysis, you can redirect output to a file:

```bash
python performance_test.py > performance_results.log
python benchmark_llm_throughput.py > benchmark_results.log
```
