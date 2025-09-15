import { create } from 'zustand'
import { nanoid } from 'nanoid'

export type GNode = {
  id: string
  label: string
  text: string
  type: 'main' | 'component' | 'child' | 'continuation' | 'atomic'
  status: 'active' | 'stale' | 'merge_pending' | 'completed' | 'failed'
  sessionId: string
  messageId?: string
  createdAt: number
  embedding?: number[] // optional later
  meta?: Record<string, any>
}

export type GEdge = {
  id: string
  source: string
  target: string
  label?: 'sequence' | 'supports' | 'contradicts' | 'refines' | 'depends_on' | 'example_of' | 'causes'
  createdAt: number
}

type GraphState = {
  nodes: Record<string, GNode>
  edges: Record<string, GEdge>
  lastNodeIdBySession: Record<string, string | undefined>
  upsertNode: (n: Partial<GNode> & { text: string; sessionId: string }) => string
  link: (sourceId: string, targetId: string, label?: GEdge['label']) => string
  resetSession: (sessionId: string) => void
}

export const useGraphStore = create<GraphState>((set, get) => ({
  nodes: {},
  edges: {},
  lastNodeIdBySession: {},

  upsertNode: ({ text, sessionId, type = 'atomic', status = 'active', label }) => {
    const id = `node:${nanoid()}`
    const n: GNode = {
      id,
      label: label ?? (text.length > 48 ? text.slice(0, 45) + '…' : text),
      text,
      type,
      status,
      sessionId,
      createdAt: Date.now(),
    }
    set(s => ({ nodes: { ...s.nodes, [id]: n }, lastNodeIdBySession: { ...s.lastNodeIdBySession, [sessionId]: id } }))
    return id
  },

  link: (source, target, label = 'sequence') => {
    const id = `edge:${source}->${target}:${nanoid(6)}`
    const e: GEdge = { id, source, target, label, createdAt: Date.now() }
    set(s => ({ edges: { ...s.edges, [id]: e } }))
    return id
  },

  resetSession: (sessionId) => {
    const s = get()
    const nodes = { ...s.nodes }
    const edges = { ...s.edges }
    Object.values(nodes).forEach(n => { if (n.sessionId === sessionId) delete nodes[n.id] })
    Object.values(edges).forEach(e => {
      if (!nodes[e.source] || !nodes[e.target]) delete edges[e.id]
    })
    set({ nodes, edges, lastNodeIdBySession: { ...s.lastNodeIdBySession, [sessionId]: undefined } })
  },
}))
