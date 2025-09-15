# Ollama Supervisor Service

The Ollama Supervisor Service provides automatic failure detection and recovery for your Ollama LLM system. It monitors the Ollama process and API, automatically recovers from failures, and logs incidents with timestamps and restart reasons.

## Features

- **Process Monitoring**: Detects when the Ollama process crashes or stops running
- **API Health Checks**: Monitors the Ollama API for responsiveness
- **Automatic Recovery**: Restarts Ollama service and reloads models when failures occur
- **Adaptive Memory Management**: Unloads lower priority models when memory usage is high
- **Incident Logging**: Records all incidents with timestamps and reasons
- **Webhook Alerts**: Sends notifications for incidents via webhook (Slack, Discord, etc.)

## How It Works

The supervisor service runs as a background daemon that performs the following checks at regular intervals:

1. **Process Check**: Verifies that the Ollama process is running
2. **API Check**: Ensures the Ollama API is responsive
3. **Memory Check**: Monitors system memory usage and unloads models if needed

If any check fails, the supervisor will automatically recover by:

1. Restarting the Ollama service
2. Reloading all configured models
3. Logging the incident with timestamp and reason
4. Sending webhook alerts if configured

## Configuration

The supervisor service can be configured through environment variables or the configuration file at `backend/config/supervisor_config.py`:

- `SUPERVISOR_CHECK_INTERVAL`: Interval between checks in seconds (default: 30)
- `SUPERVISOR_MEMORY_THRESHOLD`: Memory usage threshold percentage (default: 75.0)
- `SUPERVISOR_WEBHOOK_URL`: Webhook URL for alerts (default: "")
- `SUPERVISOR_ALERTS_ENABLED`: Enable/disable alerts (default: false)

The models and their priorities are configured in the same file:

```python
MODELS = [
    {"name": "llama3:latest", "priority": 2},
    {"name": "qwen3:latest", "priority": 1}
]
```

## Webhook Alerts

To enable webhook alerts for incidents:

```python
from services.ollama_supervisor import ollama_supervisor_service

# Enable webhook alerts
ollama_supervisor_service.enable_webhook_alerts("https://your-webhook-url.com")
```

The service supports any webhook endpoint that accepts JSON payloads, including:

- Slack incoming webhooks
- Discord webhooks
- Custom webhook endpoints

## Log Files

All incidents are logged to `ollama_supervisor.log` in the root directory. Each log entry includes:

- Timestamp of the incident
- Type of incident (process_down, api_unresponsive, etc.)
- Reason for the incident
- Actions taken to recover

## Manual Testing

To test the supervisor service manually:

```bash
python test_supervisor.py
```

This will start the supervisor, let it run for 10 seconds, and then stop it.

## Integration

The supervisor service is automatically integrated with the main FastAPI application and starts when the application starts. It gracefully shuts down when the application stops.
