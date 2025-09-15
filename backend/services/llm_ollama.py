import httpx
import asyncio
import json
from config.config import settings

async def stream_ollama_response(model: str, prompt: str):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", f"{settings.OLLAMA_URL}/api/generate", 
                json={"model": model, "prompt": prompt, "stream": True}) as r:
                # Check if the response status is successful
                if r.status_code != 200:
                    raise Exception(f"Ollama API error: {r.status_code} - {r.text}")
                
                async for line in r.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            continue
                    await asyncio.sleep(0)  # yield control
    except httpx.ConnectError:
        raise Exception("Cannot connect to Ollama. Please ensure Ollama is running.")
    except httpx.TimeoutException:
        raise Exception("Ollama request timed out. Please try again.")
    except Exception as e:
        raise Exception(f"Error communicating with Ollama: {str(e)}")

async def list_ollama_models():
    try:
        url = f"{settings.OLLAMA_URL}/api/tags"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
    except httpx.ConnectError:
        raise Exception("Cannot connect to Ollama. Please ensure Ollama is running.")
    except httpx.TimeoutException:
        raise Exception("Ollama model list request timed out.")
    except Exception as e:
        raise Exception(f"Error fetching Ollama models: {str(e)}")
