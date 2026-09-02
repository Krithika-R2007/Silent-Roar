import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cx } from '../../utils/format'

interface SnapshotItem {
  label: string
  value: number | string
  change: string
  changeDirection: 'up' | 'down' | 'neutral'
  interpretation: string
  accent: 'crimson' | 'amber' | 'emerald' | 'teal'
}

const accentStyles: Record<string, { border: string; value: string; badge: string }> = {
  crimson: { border: 'border-l-red-400', value: 'text-red-600', badge: 'bg-red-50 text-red-600' },
  amber:   { border: 'border-l-amber-400', value: 'text-amber-600', badge: 'bg-amber-50 text-amber-600' },
  emerald: { border: 'border-l-emerald-400', value: 'text-emerald-700', badge: 'bg-emerald-50 text-emerald-700' },
  teal:    { border: 'border-l-teal-400', value: 'text-teal-700', badge: 'bg-teal-50 text-teal-700' },
}

function SnapshotCard({ item }: { item: SnapshotItem }) {
  const s = accentStyles[item.accent]
  const TrendIcon = item.changeDirection === 'up' ? TrendingUp : item.changeDirection === 'down' ? TrendingDown : Minus
  return (
    <div className={cx('flex flex-col justify-between rounded-xl border border-slate-200 bg-white px-4 py-3.5 border-l-[3px]', s.border)}>
      <div className="label-meta mb-2 text-slate-500">{item.label}</div>
      <div className={cx('font-display text-[2rem] font-bold leading-none tabular-nums', s.value)}>
        {item.value}
      </div>
      <div className="mt-2 flex items-center justify-between gap-2">
        <p className="font-ui text-[11px] font-medium leading-snug text-slate-500">{item.interpretation}</p>
        <span className={cx('font-ui flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold', s.badge)}>
          <TrendIcon className="h-2.5 w-2.5" />
          {item.change}
        </span>
      </div>
    </div>
  )
}

export function IntelligenceSnapshot({ data }: {
  data: Partial<{
    totalAlerts: number
    emergingHubs: number
    totalIncidents: number
    criticalAlerts: number
  }>
}) {
  const items: SnapshotItem[] = [
    {
      label: 'High-Priority Signals',
      value: data.totalAlerts ?? 27,
      change: '↑ 4',
      changeDirection: 'up',
      interpretation: 'Active CRITICAL + HIGH alerts requiring attention',
      accent: 'crimson',
    },
    {
      label: 'Emerging Corridors',
      value: data.emergingHubs ?? 4,
      change: '↑ 1',
      changeDirection: 'up',
      interpretation: 'New or escalating trafficking hub activity',
      accent: 'amber',
    },
    {
      label: 'Connected Incidents',
      value: data.totalIncidents ?? 165,
      change: '+12',
      changeDirection: 'up',
      interpretation: 'Cross-referenced incident records in the network',
      accent: 'teal',
    },
    {
      label: 'Multi-Signal Events',
      value: data.criticalAlerts ?? 12,
      change: '↑ 2',
      changeDirection: 'up',
      interpretation: 'Events with 3+ converging evidence streams',
      accent: 'emerald',
    },
  ]

  return (
    <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
      {items.map((item) => <SnapshotCard key={item.label} item={item} />)}
    </div>
  )
}
