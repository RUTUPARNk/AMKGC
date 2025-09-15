# Ollama Model Fetcher

This directory contains utilities for fetching and managing Ollama models in the Node LLM System.

## Files Overview

### 1. `fetch_ollama_models.py` - Comprehensive Model Fetcher
A full-featured script that provides detailed information about available Ollama models.

**Features:**
- Lists all available models with size and modification date
- Validates model availability
- Interactive mode for detailed model inspection
- API and CLI fallback methods
- Human-readable size formatting

**Usage:**
```bash
# Basic usage - list all models
python fetch_ollama_models.py

# Interactive mode - get detailed info about specific models
python fetch_ollama_models.py --interactive
```

**Example Output:**
```
🤖 Ollama Model Fetcher
==================================================
Checking Ollama status...
✅ Ollama is running and accessible!

Fetching available models...

📋 Found 2 Ollama model(s):
================================================================================

1. Model: llama3
   Size: 4.7GB
   Modified: 2024-01-15 14:30:22
----------------------------------------

2. Model: mistral
   Size: 4.1GB
   Modified: 2024-01-10 09:15:45
----------------------------------------

📝 Model names (for use in .env file):
Available models:
  - llama3
  - mistral
```

### 2. `get_ollama_model.py` - Simple Model Getter
A lightweight utility that returns just the first available model name.

**Features:**
- Returns only the model name (no formatting)
- Designed for automation and scripting
- Fast and minimal output
- Exit codes for error handling

**Usage:**
```bash
# Get first available model name
python get_ollama_model.py

# Use in scripts
MODEL_NAME=$(python get_ollama_model.py)
echo "Using model: $MODEL_NAME"
```

**Example Output:**
```
llama3
```

### 3. `test_model_fetcher.py` - Integration Test
A comprehensive test script that demonstrates the model fetching capabilities.

**Features:**
- Tests both standalone and integrated model fetching
- Validates model switching
- Tests generation with fetched models
- Comprehensive error handling

**Usage:**
```bash
python test_model_fetcher.py
```

## Integration with Node LLM System

### Automatic Model Detection
The Node LLM System now automatically detects and uses available Ollama models:

1. **Quick Start**: The `quick_start.py` script automatically detects the first available model
2. **LLM Service**: The `LLMService` class includes methods for model management
3. **Environment Setup**: Models are automatically configured in the `.env` file

### LLMService Integration
The `LLMService` class now includes these new methods:

```python
# Get all available models
available_models = llm_service.get_available_ollama_models()

# Validate a specific model
is_valid = llm_service.validate_ollama_model("llama3")

# Get first available model
first_model = llm_service.get_first_available_model()

# Update the model being used
success = llm_service.update_ollama_model("mistral")

# Check Ollama status
is_running = llm_service.check_ollama_status()
```

### Environment Configuration
The system automatically configures the `OLLAMA_MODEL` environment variable:

```bash
# Automatic detection in quick_start.py
OLLAMA_MODEL=llama3  # Automatically detected

# Manual override in .env file
OLLAMA_MODEL=mistral
```

## Usage Examples

### 1. Check Available Models
```bash
python fetch_ollama_models.py
```

### 2. Get Model for Scripting
```bash
MODEL=$(python get_ollama_model.py)
echo "Using model: $MODEL"
```

### 3. Test Integration
```bash
python test_model_fetcher.py
```

### 4. Quick Start with Auto-Detection
```bash
python quick_start.py
```

## Error Handling

### Common Issues and Solutions

1. **Ollama Not Running**
   ```
   ❌ Ollama is not running or not accessible!
   Solution: Start Ollama with `ollama serve`
   ```

2. **No Models Available**
   ```
   ❌ No models found!
   Solution: Pull models with `ollama pull llama3`
   ```

3. **Model Not Found**
   ```
   ❌ Model 'llama3' is not available!
   Solution: Check available models and update .env file
   ```

## API Reference

### OllamaModelFetcher Class
```python
class OllamaModelFetcher:
    def check_ollama_status(self) -> bool
    def get_available_models(self) -> List[OllamaModel]
    def get_model_info(self, model_name: str) -> Optional[Dict]
    def validate_model(self, model_name: str) -> bool
    def get_model_names(self) -> List[str]
```

### LLMService Integration
```python
class LLMService:
    def get_available_ollama_models(self) -> List[str]
    def validate_ollama_model(self, model_name: str) -> bool
    def get_first_available_model(self) -> Optional[str]
    def update_ollama_model(self, model_name: str) -> bool
    def check_ollama_status(self) -> bool
```

## Best Practices

1. **Always check Ollama status** before attempting to fetch models
2. **Use the API first**, fallback to CLI if needed
3. **Validate models** before using them in the LLM service
4. **Handle errors gracefully** with appropriate fallbacks
5. **Cache model information** for better performance in production

## Next Steps

1. **Test the model fetcher** with your Ollama installation
2. **Run the integration test** to verify everything works
3. **Use the quick start script** to get the system running
4. **Customize the model selection** based on your needs 