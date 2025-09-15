import { useEffect, useRef, useCallback, useState } from 'react'
import { useChunker } from './useChunker'

export async function fetchOllamaModels() {
  try {
    const resp = await fetch('/api/ollama/models')
    const data = await resp.json()
    return data.models
  } catch (error) {
    console.error('Error fetching Ollama models:', error)
    return []
  }
}

export function useSessionWS(
  sessionId: string, 
  provider: 'qwen' | 'ollama' = 'qwen',
  model: string = 'llama2'
) {
  const { pushToken, flush } = useChunker(sessionId)
  const wsRef = useRef<WebSocket | null>(null)

  // Error state that can be used by components
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/sessions/${sessionId}`)
    wsRef.current = ws
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.type === 'TOKEN' && msg.payload?.token) {
        // Clear any previous error when we receive tokens
        setError(null);
        pushToken(msg.payload.token)
      } else if (msg.type === 'TYPING_END') {
        flush()
      } else if (msg.type === 'ERROR') {
        console.error('WebSocket error:', msg.payload?.message)
        setError(msg.payload?.message || 'An unknown error occurred');
        flush()
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket connection error:', error);
      setError('Connection error. Please check your network and try again.');
    };
    
    ws.onclose = (event) => {
      if (!event.wasClean) {
        setError('Connection closed unexpectedly. Please refresh the page.');
      }
    };
    
    return () => { ws.close(); wsRef.current = null }
  }, [sessionId, pushToken, flush])

  const sendPrompt = useCallback((prompt: string) => {
    // Clear previous error when sending a new prompt
    setError(null);
    flush()
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'PROMPT', payload: { prompt, provider, model } }))
    } else {
      setError('Connection is not open. Please refresh the page.');
    }
  }, [flush, provider, model])

  return { sendPrompt, error }
}
