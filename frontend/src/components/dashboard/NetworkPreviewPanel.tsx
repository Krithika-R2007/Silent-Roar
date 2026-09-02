import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'

interface NetworkStats {
  relatedIncidents: number
  recurringEntities: number
  sharedCorridors: number
  emergingNetworks: number
}

export function NetworkPreviewPanel({ stats }: { stats: NetworkStats; targetId?: string }) {
  const navigate = useNavigate()

  const nodes = [
    { id: 'n1', label: 'ACTOR',    x: 50, y: 10, color: '#7C3AED' },
    { id: 'n2', label: 'ROUTE',    x: 20, y: 45, color: '#D97706' },
    { id: 'n3', label: 'SHIPMENT', x: 80, y: 45, color: '#0F766E' },
    { id: 'n4', label: 'INCIDENT', x: 35, y: 80, color: '#DC2626' },
    { id: 'n5', label: 'ACTOR',    x: 65, y: 80, color: '#7C3AED' },
    { id: 'n6', label: 'HUB',      x: 50, y: 50, color: '#059669' },
  ]

  const edges = [
    { s: 'n1', t: 'n2' }, { s: 'n1', t: 'n3' }, { s: 'n1', t: 'n6' },
    { s: 'n2', t: 'n4' }, { s: 'n3', t: 'n5' }, { s: 'n6', t: 'n4' },
    { s: 'n6', t: 'n5' },
  ]

  const getNode = (id: string) => nodes.find((n) => n.id === id)!

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-4 py-3">
        <span className="label-meta text-slate-500">HIDDEN NETWORK DETECTED</span>
      </div>
      <div className="p-4">
        {/* Mini SVG graph */}
        <div className="relative h-[140px] w-full overflow-hidden rounded-lg bg-slate-50">
          <svg viewBox="0 0 100 100" className="h-full w-full" preserveAspectRatio="xMidYMid meet">
            {edges.map((e, i) => {
              const s = getNode(e.s)
              const t = getNode(e.t)
              return (
                <line
                  key={i}
                  x1={s.x} y1={s.y} x2={t.x} y2={t.y}
                  stroke="#CBD5E1" strokeWidth="0.8" strokeDasharray="2 2"
                />
              )
            })}
            {nodes.map((n) => (
              <g key={n.id}>
                <circle cx={n.x} cy={n.y} r="4.5" fill={n.color} opacity={0.85} />
                <text
                  x={n.x} y={n.y + 8}
                  textAnchor="middle"
                  fontSize="4"
                  fill="#64748B"
                  fontFamily="monospace"
                >
                  {n.label}
                </text>
              </g>
            ))}
          </svg>
        </div>

        {/* Stats */}
        <div className="mt-3 grid grid-cols-2 gap-2">
          {[
            { label: 'Related incidents',  value: stats.relatedIncidents },
            { label: 'Recurring entities', value: stats.recurringEntities },
            { label: 'Shared corridors',   value: stats.sharedCorridors },
            { label: 'Emerging hubs',      value: stats.emergingNetworks },
          ].map(({ label, value }) => (
            <div key={label} className="rounded-lg bg-slate-50 px-3 py-2">
              <div className="font-display text-lg font-bold text-slate-800">{value}</div>
              <div className="font-ui text-[10px] text-slate-500">{label}</div>
            </div>
          ))}
        </div>

        <button
          onClick={() => navigate('/network')}
          className="focus-ring mt-3 flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-700 px-4 py-2.5 text-[13px] font-semibold text-white transition-colors hover:bg-emerald-800"
        >
          <Search className="h-3.5 w-3.5" />
          FIND HIDDEN LINK
        </button>
      </div>
    </div>
  )
}
