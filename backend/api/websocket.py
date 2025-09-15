import time
import logging
import json
import redis
import asyncio
from fastapi import APIRouter, WebSocket
from services.llm_abstraction import stream_response, set_provider
from services.ollama_warmup import ollama_warmup_service
from distributed.router import router_agent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/api/v1/ws/sessions/{session_id}")
async def session_ws(ws: WebSocket, session_id: str):
    await ws.accept()
    
    while True:
        data = await ws.receive_json()

        if data["type"] == "PROMPT":
            prompt = data["payload"]["prompt"]
            
            # Check if provider is specified in the message
            provider = data["payload"].get("provider", "qwen")
            model = data["payload"].get("model", "llama2")  # Default model for Ollama

            # Validate provider
            if provider not in ["qwen", "ollama"]:
                await ws.send_json({"type": "ERROR", "payload": {"message": "Invalid provider specified"}})
                continue

            # Validate model for Ollama provider
            if provider == "ollama" and not model:
                await ws.send_json({"type": "ERROR", "payload": {"message": "Model must be specified for Ollama provider"}})
                continue
            
            # Check if Ollama is ready for Ollama provider
            if provider == "ollama" and not ollama_warmup_service.is_ready:
                # Try to check readiness
                if not ollama_warmup_service.check_readiness():
                    await ws.send_json({"type": "ERROR", "payload": {"message": "Ollama service is not ready. Please try again later."}})
                    continue

            # Notify typing started
            await ws.send_json({"type": "TYPING_START"})

            # Set the provider for this request
            set_provider(provider)
            
            # Metrics tracking
            start_time = time.time()
            token_count = 0
            
            try:
                # For Qwen, model parameter is ignored, for Ollama, it's used
                async for token in stream_response(model, prompt):
                    await ws.send_json({"type": "TOKEN", "payload": {"token": token}})
                    token_count += 1
                    
                    # Log metrics every 50 tokens
                    if token_count % 50 == 0:
                        elapsed = time.time() - start_time
                        tokens_per_sec = token_count / elapsed if elapsed > 0 else 0
                        logger.info(f"Session {session_id}: {token_count} tokens sent, {tokens_per_sec:.2f} tokens/sec")
                        
            except Exception as e:
                await ws.send_json({"type": "ERROR", "payload": {"message": f"Error generating response: {str(e)}"}})
                continue

            # Final metrics
            end_time = time.time()
            total_time = end_time - start_time
            tokens_per_sec = token_count / total_time if total_time > 0 else 0
            
            logger.info(f"Session {session_id} completed: {token_count} tokens in {total_time:.2f}s, {tokens_per_sec:.2f} tokens/sec")
            
            # Notify typing completed
            await ws.send_json({"type": "TYPING_END"})

@router.websocket("/api/v1/ws/router/{session_id}")
async def router_ws(ws: WebSocket, session_id: str):
    await ws.accept()
    
    # Subscribe to Redis channel for router updates
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    pubsub = redis_client.pubsub()
    pubsub.subscribe(f"router_updates:{session_id}")
    
    try:
        while True:
            # Check for WebSocket messages
            try:
                data = await ws.receive_json()
                if data["type"] == "SUBSCRIBE_ROUTER_UPDATES":
                    # Client wants to subscribe to router updates
                    await ws.send_json({
                        "type": "ROUTER_SUBSCRIPTION_CONFIRMED",
                        "payload": {"message": "Subscribed to router updates"}
                    })
            except:
                # No message received, continue
                pass
            
            # Check for router updates from Redis
            message = pubsub.get_message()
            if message and message['type'] == 'message':
                try:
                    update_data = json.loads(message['data'])
                    await ws.send_json({
                        "type": "ROUTER_UPDATE",
                        "payload": update_data
                    })
                except Exception as e:
                    logger.error(f"Error processing router update: {e}")
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)
            
    except Exception as e:
        logger.error(f"Router WebSocket error: {e}")
    finally:
        pubsub.unsubscribe(f"router_updates:{session_id}")
        await ws.close()
