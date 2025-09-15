import { useMemo } from 'react'
import ReactFlow, { Background, Controls, MiniMap, Edge } from 'reactflow'
import 'reactflow/dist/style.css'
import { useGraphStore } from '../store/graph'
import { useSessionWS } from '../hooks/useSessionWS'

export function GraphView({ sessionId }: { sessionId: string }) {
  // Initialize WebSocket connection
  useSessionWS(sessionId)
  
  const nodesObj = useGraphStore(s => s.nodes)
  const edgesObj = useGraphStore(s => s.edges)

  const rfNodes = useMemo(() => Object.values(nodesObj)
    .filter(n => n.sessionId === sessionId)
    .map(n => ({
      id: n.id,
      position: { x: 0, y: 0 }, // will be auto-laid out by layout hook if you add one
      data: { label: n.label, status: n.status, type: n.type },
      style: {
        borderRadius: 12,
        padding: 8,
        border: `2px solid ${statusColor(n.status)}`,
        background: '#0b1220',
        color: '#e2e8f0',
        width: 260,
      },
    })), [nodesObj, sessionId])

  const rfEdges = useMemo(() => Object.values(edgesObj)
    .map(e => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.label,
      animated: e.label === 'supports',
      style: edgeStyle(e.label),
      labelBgPadding: [4, 2] as [number, number],
      labelStyle: { fontSize: 10, fill: '#cbd5e1' },
    })), [edgesObj]) as Edge[]

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <MiniMap pannable zoomable />
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  )
}

function statusColor(s: string) {
  switch (s) {
    case 'active': return '#22c55e'
    case 'stale': return '#64748b'
    case 'merge_pending': return '#eab308'
    case 'failed': return '#ef4444'
    default: return '#334155'
  }
}
function edgeStyle(label?: string) {
  switch (label) {
    case 'supports': return { stroke: '#22c55e', strokeWidth: 2 }
    case 'contradicts': return { stroke: '#ef4444', strokeDasharray: '6 6' }
    case 'depends_on': return { stroke: '#3b82f6', strokeWidth: 2 }
    case 'example_of': return { stroke: '#a855f7', strokeDasharray: '2 4' }
    case 'causes': return { stroke: '#f59e0b', strokeWidth: 2 }
    default: return { stroke: '#475569', strokeWidth: 1.5 }
  }
}
