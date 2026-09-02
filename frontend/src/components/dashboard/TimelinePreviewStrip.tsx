import { useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { cx } from '../../utils/format'

interface TimelinePoint {
  month: string
  label: string
  type: 'INCIDENT' | 'ROUTE' | 'ENTITY' | 'SIGNAL' | 'ALERT' | 'EXPANSION'
}

const defaultPoints: TimelinePoint[] = [
  { month: 'JAN', label: 'Seizure',       type: 'INCIDENT' },
  { month: 'FEB', label: 'Route overlap', type: 'ROUTE' },
  { month: 'MAR', label: 'Entity link',   type: 'ENTITY' },
  { month: 'APR', label: 'New signal',    type: 'SIGNAL' },
  { month: 'MAY', label: 'Alert raised',  type: 'ALERT' },
  { month: 'JUN', label: 'Network grows', type: 'EXPANSION' },
]

const typeColor: Record<string, string> = {
  INCIDENT:  'bg-red-500',
  ROUTE:     'bg-amber-500',
  ENTITY:    'bg-violet-500',
  SIGNAL:    'bg-teal-500',
  ALERT:     'bg-red-400',
  EXPANSION: 'bg-emerald-500',
}

const typeBg: Record<string, string> = {
  INCIDENT:  'bg-red-50 border-red-200 text-red-700',
  ROUTE:     'bg-amber-50 border-amber-200 text-amber-700',
  ENTITY:    'bg-violet-50 border-violet-200 text-violet-700',
  SIGNAL:    'bg-teal-50 border-teal-200 text-teal-700',
  ALERT:     'bg-red-50 border-red-200 text-red-700',
  EXPANSION: 'bg-emerald-50 border-emerald-200 text-emerald-700',
}

export function TimelinePreviewStrip({ points = defaultPoints }: { points?: TimelinePoint[] }) {
  const navigate = useNavigate()

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <span className="label-meta text-slate-500">NETWORK EVOLUTION</span>
        <button
          onClick={() => navigate('/investigations')}
          className="focus-ring flex items-center gap-1 text-[11px] font-semibold text-emerald-700 hover:underline"
        >
          OPEN FULL TIMELINE <ArrowRight className="h-3 w-3" />
        </button>
      </div>
      <div className="px-4 py-4">
        {/* Timeline track */}
        <div className="relative flex items-start gap-0">
          {/* connecting line */}
          <div className="absolute left-[18px] right-[18px] top-[9px] h-[2px] bg-slate-100" />
          {points.map((pt, i) => (
            <div key={i} className="relative flex flex-1 flex-col items-center gap-2">
              <div className={cx('relative z-10 h-[18px] w-[18px] rounded-full border-2 border-white shadow-sm', typeColor[pt.type])} />
              <span className="font-mono-intel text-[9px] font-bold text-slate-400">{pt.month}</span>
              <span className={cx('rounded border px-1.5 py-0.5 text-center text-[9px] font-semibold leading-snug', typeBg[pt.type])}>
                {pt.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
