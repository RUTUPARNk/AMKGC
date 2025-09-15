import asyncio
from backend.services.llm_abstraction import stream_response, set_provider

async def test_llm_abstraction():
    # Test with Ollama provider
    print("Testing with Ollama provider...")
    set_provider("ollama")
    
    try:
        async for token in stream_response("Hello, how are you?"):
            print(token, end='', flush=True)
        print("\nOllama test completed successfully")
    except Exception as e:
        print(f"Error with Ollama: {e}")
    
    # Test with Qwen provider
    print("\nTesting with Qwen provider...")
    set_provider("qwen")
    
    try:
        async for token in stream_response("Hello, how are you?"):
            print(token, end='', flush=True)
        print("\nQwen test completed successfully")
    except Exception as e:
        print(f"Error with Qwen: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_abstraction())
