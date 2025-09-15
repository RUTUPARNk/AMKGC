import { useEffect, useRef, useCallback } from 'react'
import { useGraphStore } from '../store/graph'
import { GEdge } from '../store/graph'

const isTerminal = (s: string) => /[.?!]$/.test(s)
const MIN_LEN = 12
const MAX_LEN = 400
const IDLE_MS = 900

export function useChunker(sessionId: string) {
  const upsertNode = useGraphStore(s => s.upsertNode)
  const link = useGraphStore(s => s.link)
  // const lastNodeId = useGraphStore(s => s.lastNodeIdBySession[sessionId]) // Not used directly but accessed via state

  const bufRef = useRef<string>('')
  const timerRef = useRef<any>(null)
  const chunkCountRef = useRef<number>(0)
  const nodeCountRef = useRef<number>(0)
  const startTimeRef = useRef<number>(Date.now())

  const flush = useCallback(() => {
    const text = bufRef.current.trim()
    if (!text) return
    if (text.length < MIN_LEN && text.split(/\s+/).length < 3) { bufRef.current = ''; return }

    // dedupe: compare with last node (cheap heuristic)
    const state = useGraphStore.getState()
    const prevId = state.lastNodeIdBySession[sessionId]
    if (prevId) {
      const prev = state.nodes[prevId]
      const sim = similarity(prev.text, text)
      if (sim >= 0.92) {
        // merge into previous node
        const merged = prev.text + (prev.text.endsWith('\n') ? '' : ' ') + text
        state.nodes[prevId] = { ...prev, text: merged, label: merged.length > 48 ? merged.slice(0, 45) + '…' : merged }
        useGraphStore.setState({ nodes: { ...state.nodes } })
        bufRef.current = ''
        return
      }
    }

    // new node
    const newId = upsertNode({ text, sessionId })
    nodeCountRef.current += 1
    if (prevId) link(prevId, newId, 'sequence')
    runHeuristicRelations(sessionId, newId)
    bufRef.current = ''

    // Log metrics every 5 chunks
    chunkCountRef.current += 1
    if (chunkCountRef.current % 5 === 0) {
      const elapsed = (Date.now() - startTimeRef.current) / 1000; // seconds
      const chunksPerSec = chunkCountRef.current / elapsed;
      const nodesPerSec = nodeCountRef.current / elapsed;
      console.log(`Session ${sessionId}: ${chunkCountRef.current} chunks, ${chunksPerSec.toFixed(2)} chunks/sec, ${nodeCountRef.current} nodes, ${nodesPerSec.toFixed(2)} nodes/sec`);
    }
  }, [sessionId, upsertNode, link])

  const pushToken = useCallback((tok: string) => {
    bufRef.current += tok
    if (bufRef.current.length >= MAX_LEN || isTerminal(tok)) {
      clearTimeout(timerRef.current)
      flush()
    } else {
      clearTimeout(timerRef.current)
      timerRef.current = setTimeout(flush, IDLE_MS)
    }
  }, [flush])

  useEffect(() => () => clearTimeout(timerRef.current), [])

  // Reset metrics when session changes
  useEffect(() => {
    chunkCountRef.current = 0;
    nodeCountRef.current = 0;
    startTimeRef.current = Date.now();
  }, [sessionId]);

  return { pushToken, flush }
}

// Very cheap similarity (char trigram cosine-like)
function similarity(a: string, b: string): number {
  const grams = (s: string) => {
    const g = new Map<string, number>()
    const t = s.toLowerCase()
    for (let i = 0; i < t.length - 2; i++) {
      const k = t.slice(i, i + 3)
      g.set(k, (g.get(k) || 0) + 1)
    }
    return g
  }
  const A = grams(a), B = grams(b)
  let dot = 0, na = 0, nb = 0
  A.forEach((v, k) => { na += v * v; if (B.has(k)) dot += v * (B.get(k) || 0) })
  B.forEach(v => nb += v * v)
  return dot / (Math.sqrt(na) * Math.sqrt(nb) + 1e-9)
}

// Heuristic relation detector
function runHeuristicRelations(sessionId: string, nodeId: string) {
  const s = useGraphStore.getState()
  const n = s.nodes[nodeId]
  const prevId = s.lastNodeIdBySession[sessionId]
  if (!prevId || prevId === nodeId) return
  // const prev = s.nodes[prevId] // Not used directly
  const text = n.text.trim()

  // simple cue words
  const cues: Array<{ re: RegExp; label: GEdge['label'] }> = [
    { re: /\b(because|due to|since)\b/i, label: 'causes' },
    { re: /\btherefore|so\b/i, label: 'supports' },
    { re: /\bhowever|but|although\b/i, label: 'contradicts' },
    { re: /\bdepends on|requires\b/i, label: 'depends_on' },
    { re: /\bfor example|e\.g\.\b/i, label: 'example_of' },
    { re: /\brefine|revise|improve\b/i, label: 'refines' },
  ]
  for (const c of cues) {
    if (c.re.test(text)) { s.link(prevId, nodeId, c.label); break }
  }
}
