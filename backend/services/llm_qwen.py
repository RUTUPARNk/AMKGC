import httpx
from typing import AsyncGenerator
from config.config import settings

async def stream_qwen_response(model: str, prompt: str) -> AsyncGenerator[str, None]:
    """Stream response from Qwen API. Model parameter is ignored as Qwen uses a fixed model."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                "https://api.qwen.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.QWEN_API_KEY}"},
                json={
                    "model": "qwen-72b-chat",  # Fixed model for Qwen
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True
                },
            ) as response:
                # Check if the response status is successful
                if response.status_code != 200:
                    raise Exception(f"Qwen API error: {response.status_code} - {response.text}")
                
                async for line in response.aiter_lines():
                    if line.strip() and line.startswith("data: "):
                        chunk = line.replace("data: ", "")
                        if chunk != "[DONE]":
                            yield chunk
    except httpx.ConnectError:
        raise Exception("Cannot connect to Qwen API. Please check your internet connection.")
    except httpx.TimeoutException:
        raise Exception("Qwen API request timed out. Please try again.")
    except Exception as e:
        raise Exception(f"Error communicating with Qwen API: {str(e)}")
