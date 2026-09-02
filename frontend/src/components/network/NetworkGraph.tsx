import { useRef, useState } from 'react'
import { GraphEdge, GraphNode } from '../../types'
import { cx } from '../../utils/format'
import { Users, FileWarning, MapPin, Waypoints, FileStack, MessageSquareText } from 'lucide-react'

const nodeStyle: Record<GraphNode['type'], { color: string; label: string }> = {
  ACTOR:    { color: '#C4433D', label: 'Actor' },
  INCIDENT: { color: '#D19A3E', label: 'Incident' },
  LOCATION: { color: '#3E9AB0', label: 'Location' },
  ROUTE:    { color: '#149447', label: 'Route' },
  EVIDENCE: { color: '#8E9895', label: 'Evidence' },
  SHIPMENT: { color: '#3E9AB0', label: 'Shipment' },
  MESSAGE:  { color: '#5FC886', label: 'Message' },
}

// Icon components mapped by type — rendered as foreignObject inside SVG
const typeIconMap: Record<GraphNode['type'], typeof Users> = {
  ACTOR:    Users,
  INCIDENT: FileWarning,
  LOCATION: MapPin,
  ROUTE:    Waypoints,
  EVIDENCE: FileStack,
  SHIPMENT: FileStack,
  MESSAGE:  MessageSquareText,
}

export function NetworkGraph({
  nodes,
  edges,
  onNodeClick,
  selectedNodeId,
  height = 480,
}: {
  nodes: GraphNode[]
  edges: GraphEdge[]
  onNodeClick?: (node: GraphNode) => void
  selectedNodeId?: string | null
  height?: number
}) {
  const [hoveredId, setHoveredId] = useState<string | null>(null)
  const svgRef = useRef<SVGSVGElement>(null)

  const nodeById = (id: string) => nodes.find((n) => n.id === id)

  const visibleNodes = nodes.filter((n) => n.x !== undefined && n.y !== undefined)
  const visibleEdges = edges.filter((e) => {
    const s = nodeById(e.source)
    const t = nodeById(e.target)
    return s?.x !== undefined && t?.x !== undefined
  })

  if (visibleNodes.length === 0) {
    return (
      <div
        className="flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-[14px] text-slate-400"
        style={{ height }}
      >
        No network data to display.
      </div>
    )
  }

  return (
    <div
      className="relative w-full overflow-hidden rounded-xl border border-slate-200 bg-[#F8FAF9] shadow-sm"
      style={{ height }}
    >
      <svg
        ref={svgRef}
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        className="absolute inset-0 h-full w-full"
        style={{ pointerEvents: 'none' }}
      >
        <defs>
          <pattern id="netgrid" width="4" height="4" patternUnits="userSpaceOnUse">
            <path d="M4 0H0V4" fill="none" stroke="#E8EDE9" strokeWidth="0.15" />
          </pattern>
        </defs>
        <rect width="100" height="100" fill="url(#netgrid)" />

        {/* Edges */}
        {visibleEdges.map((edge) => {
          const s = nodeById(edge.source)!
          const t = nodeById(edge.target)!
          const isHighlighted =
            hoveredId === s.id || hoveredId === t.id ||
            selectedNodeId === s.id || selectedNodeId === t.id
          return (
            <line
              key={edge.id}
              x1={s.x} y1={s.y}
              x2={t.x} y2={t.y}
              stroke={isHighlighted ? '#0F7A3A' : '#C7D1CD'}
              strokeWidth={isHighlighted ? 0.4 : 0.25}
              opacity={isHighlighted ? 1 : 0.55}
            />
          )
        })}
      </svg>

      {/* Nodes — positioned absolutely over the SVG using the same % coordinates */}
      {visibleNodes.map((node) => {
        const style = nodeStyle[node.type]
        const Icon = typeIconMap[node.type]
        const isSelected = selectedNodeId === node.id
        const isHovered = hoveredId === node.id
        const active = isSelected || isHovered

        return (
          <button
            key={node.id}
            onMouseEnter={() => setHoveredId(node.id)}
            onMouseLeave={() => setHoveredId(null)}
            onClick={() => onNodeClick?.(node)}
            className="focus-ring group absolute -translate-x-1/2 -translate-y-1/2 outline-none"
            style={{ left: `${node.x}%`, top: `${node.y}%` }}
          >
            {/* Node circle */}
            <span
              className={cx(
                'flex items-center justify-center rounded-full border-2 border-white shadow-sm transition-all duration-150',
                active ? 'h-7 w-7 scale-110' : 'h-4 w-4'
              )}
              style={{ backgroundColor: `${style.color}${active ? 'FF' : 'D9'}` }}
            >
              {active && <Icon className="h-3.5 w-3.5 text-white" strokeWidth={2} />}
            </span>

            {/* Tooltip label */}
            {active && (
              <span className="pointer-events-none absolute left-1/2 top-[calc(100%+4px)] z-10 -translate-x-1/2 whitespace-nowrap rounded-md bg-slate-900/90 px-2 py-1 text-[11px] font-medium text-white shadow-lg backdrop-blur-sm">
                {node.label}
                {node.confidence !== undefined && (
                  <span className="ml-1.5 text-emerald-400">{node.confidence}%</span>
                )}
              </span>
            )}
          </button>
        )
      })}

      {/* Legend */}
      <div className="pointer-events-none absolute bottom-3 left-3 flex flex-wrap gap-x-3 gap-y-1 rounded-lg bg-white/80 px-3 py-2 shadow-sm backdrop-blur-sm">
        {(Object.keys(nodeStyle) as GraphNode['type'][])
          .filter((t) => visibleNodes.some((n) => n.type === t))
          .map((type) => (
            <span key={type} className="flex items-center gap-1.5 text-[11px] text-slate-500">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: nodeStyle[type].color }} />
              {nodeStyle[type].label}
            </span>
          ))}
      </div>

      {/* Node count badge */}
      <div className="pointer-events-none absolute right-3 top-3 rounded-md bg-white/80 px-2 py-1 text-[10px] font-semibold text-slate-500 backdrop-blur-sm shadow-sm">
        {visibleNodes.length} nodes · {visibleEdges.length} links
      </div>
    </div>
  )
}
