import { cx } from '../../utils/format'

interface SpeciesData {
  key: string
  name: string
  signals: number
  risk: 'HIGH' | 'WATCH' | 'CRITICAL'
  trend: 'up' | 'stable' | 'down'
}

const species: SpeciesData[] = [
  { key: 'Pangolin', name: 'PANGOLIN', signals: 12, risk: 'HIGH', trend: 'up' },
  { key: 'Elephant', name: 'ELEPHANT', signals: 8, risk: 'HIGH', trend: 'up' },
  { key: 'Rhino', name: 'RHINO', signals: 4, risk: 'WATCH', trend: 'stable' },
  { key: 'Leopard', name: 'LEOPARD', signals: 3, risk: 'WATCH', trend: 'down' },
]

const riskStyles = {
  CRITICAL: { badge: 'bg-red-100 text-red-700 border-red-200', ring: 'ring-red-300' },
  HIGH:     { badge: 'bg-amber-100 text-amber-700 border-amber-200', ring: 'ring-amber-200' },
  WATCH:    { badge: 'bg-slate-100 text-slate-600 border-slate-200', ring: 'ring-slate-200' },
}

// Realistic wildlife SVG silhouettes
const SpeciesIcon = ({ speciesKey, className }: { speciesKey: string; className?: string }) => {
  if (speciesKey === 'Pangolin') {
    return (
      <svg viewBox="0 0 64 64" fill="currentColor" className={className ?? 'h-8 w-8'}>
        {/* Pangolin — distinctive curled scaly body */}
        <path d="M44 30c0-6-4-10-10-10-2 0-4 .5-5.5 1.5C26 20 24 19 22 19c-4 0-7 3-7 7 0 2.5 1.2 4.7 3 6l-2 4h3l1.5-3c1 .3 2 .5 3 .5h1l-1 2.5h3l1-2.5c4-.5 7-3 8-6.5H38c3 0 6-1.5 6-3zM22 30c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm6 4c-3.3 0-6-2.7-6-6s2.7-6 6-6 6 2.7 6 6-2.7 6-6 6z"/>
        <path d="M34 28c-.5-1.5-2-2.5-4-2.5s-3.5 1-4 2.5h8z" opacity=".5"/>
      </svg>
    )
  }
  if (speciesKey === 'Elephant') {
    return (
      <svg viewBox="0 0 64 64" fill="currentColor" className={className ?? 'h-8 w-8'}>
        {/* Elephant — large head, trunk, ear, tusks */}
        <path d="M46 20c0-4-3-7-7-7h-2c-2 0-4 .5-5.5 1.5-1-.5-2-.5-3-.5-5 0-9 4-9 9 0 2 .7 4 1.8 5.5L18 44h5l3-8c1 .7 2.2 1 3.5 1H32v7h5v-7h2c4 0 7-3 7-7v-4c0-2.5-1.2-4.7-3-6zM24 32c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm14 4h-2v-4h-8v4h-2c-3.3 0-6-2.7-6-6s2.7-6 6-6h12c3.3 0 6 2.7 6 6s-2.7 6-6 6z"/>
        <path d="M20 46c0 1.1-.9 2-2 2s-2-.9-2-2v-4h4v4z" opacity=".6"/>
      </svg>
    )
  }
  if (speciesKey === 'Rhino') {
    return (
      <svg viewBox="0 0 64 64" fill="currentColor" className={className ?? 'h-8 w-8'}>
        {/* Rhino — stocky body, distinctive nose horn */}
        <path d="M50 28c0-5-4-9-9-9h-1c-1-2-3-3-5-3H26c-5 0-9 4-9 9v4c0 3 1.5 5.5 3.8 7L18 48h5l2-6h14l2 6h5l-2.8-9c2.3-1.5 3.8-4 3.8-7v-4z"/>
        <path d="M30 13c0-2-1-5-3-5s-2 2-1.5 4L30 13z" opacity=".7"/>
        <circle cx="26" cy="27" r="2"/>
      </svg>
    )
  }
  if (speciesKey === 'Leopard') {
    return (
      <svg viewBox="0 0 64 64" fill="currentColor" className={className ?? 'h-8 w-8'}>
        {/* Leopard — lithe cat body, spots, long tail */}
        <path d="M46 26c0-5-3.5-9-8-10.5V14c0-2-1.5-3.5-3.5-3.5S31 12 31 14v1.5C26.5 17 23 21 23 26c0 3 1.3 5.7 3.3 7.5L24 44h4l2-8h4l2 8h4l-2.3-10.5C39.7 31.7 41 29 41 26h5z"/>
        <path d="M48 30l-2-1v4l2 1v-4zM16 30l2-1v4l-2 1v-4z" opacity=".5"/>
        <circle cx="32" cy="24" r="2"/>
        <circle cx="27" cy="28" r="1.5" opacity=".6"/>
        <circle cx="37" cy="28" r="1.5" opacity=".6"/>
        <circle cx="30" cy="31" r="1.5" opacity=".5"/>
        <circle cx="34" cy="31" r="1.5" opacity=".5"/>
      </svg>
    )
  }
  return null
}

export function SpeciesIntelStrip({
  activeFilter,
  onFilterChange,
}: {
  activeFilter: string | null
  onFilterChange: (species: string | null) => void
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <span className="label-meta text-slate-500">SPECIES INTELLIGENCE</span>
        {activeFilter && (
          <button
            onClick={() => onFilterChange(null)}
            className="focus-ring text-[11px] font-semibold text-emerald-700 hover:underline"
          >
            Clear filter
          </button>
        )}
      </div>
      <div className="grid grid-cols-4 divide-x divide-slate-100">
        {species.map((sp) => {
          const rs = riskStyles[sp.risk]
          const isActive = activeFilter === sp.key
          return (
            <button
              key={sp.key}
              onClick={() => onFilterChange(isActive ? null : sp.key)}
              className={cx(
                'focus-ring flex flex-col items-center gap-2 px-4 py-4 transition-colors',
                isActive ? 'bg-emerald-50' : 'hover:bg-slate-50'
              )}
            >
              <div className={cx(
                'flex h-12 w-12 items-center justify-center rounded-full border-2 transition-all',
                isActive
                  ? 'border-emerald-500 bg-emerald-100 text-emerald-700'
                  : sp.risk === 'HIGH' || sp.risk === 'CRITICAL'
                  ? 'border-amber-200 bg-amber-50 text-amber-600'
                  : 'border-slate-200 bg-slate-50 text-slate-500'
              )}>
                <SpeciesIcon speciesKey={sp.key} className="h-7 w-7" />
              </div>
              <div className="text-center">
                <div className="font-mono-intel text-[10px] font-bold tracking-widest text-slate-700">{sp.name}</div>
                <div className="mt-0.5 text-[11px] text-slate-500">{sp.signals} signals</div>
              </div>
              <span className={cx('rounded-full border px-2 py-0.5 text-[9px] font-bold tracking-wide', rs.badge)}>
                {sp.risk}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
