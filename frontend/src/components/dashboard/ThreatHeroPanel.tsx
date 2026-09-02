import { useNavigate } from 'react-router-dom'
import { Map, Network, AlertCircle } from 'lucide-react'
import { cx } from '../../utils/format'

interface EvidenceStream {
  label: string
  value: number
  detail: string
  icon: React.ReactNode
}

interface ThreatHeroPanelProps {
  title: string
  corridor: string
  riskScore: number
  confidence: number
  signalCount: number
  explanation: string
  evidenceStreams: EvidenceStream[]
  investigationId?: string
  priority: 'IMMEDIATE' | 'HIGH' | 'CRITICAL'
}

const priorityStyles = {
  IMMEDIATE: { bg: 'bg-red-600', text: 'text-red-600', light: 'bg-red-50 border-red-200', label: 'IMMEDIATE PRIORITY' },
  CRITICAL:  { bg: 'bg-red-600', text: 'text-red-600', light: 'bg-red-50 border-red-200', label: 'CRITICAL PRIORITY' },
  HIGH:      { bg: 'bg-amber-500', text: 'text-amber-600', light: 'bg-amber-50 border-amber-200', label: 'HIGH PRIORITY' },
}

export function ThreatHeroPanel({
  title, corridor, riskScore, confidence, signalCount, explanation,
  evidenceStreams, investigationId, priority,
}: ThreatHeroPanelProps) {
  const navigate = useNavigate()
  const ps = priorityStyles[priority]

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      {/* Priority banner */}
      <div className={cx('flex items-center gap-2 px-5 py-2.5 border-b', ps.light)}>
        <span className={cx('flex h-1.5 w-1.5 rounded-full relative', ps.bg)}>
          <span className={cx('absolute inset-0 rounded-full animate-ping opacity-60', ps.bg)} />
        </span>
      <span className={cx('font-mono-intel text-[10px] font-bold tracking-widest', ps.text)}>
          {ps.label} INTELLIGENCE
        </span>
      </div>

      <div className="p-5">
        <div className="flex items-start justify-between gap-4">
          {/* Left: Threat description */}
          <div className="min-w-0 flex-1">
            <h2 className="font-display text-[22px] font-bold leading-tight text-slate-900">{title}</h2>
            <div className="mt-1 flex items-center gap-2">
              <span className="font-ui text-[12px] font-semibold uppercase tracking-wider text-emerald-700">{corridor}</span>
            </div>
            <p className="mt-3 text-[13px] leading-relaxed text-slate-500">{explanation}</p>
          </div>

          {/* Right: Score cluster */}
          <div className="flex shrink-0 flex-col items-center gap-1 rounded-xl border border-slate-100 bg-slate-50 px-5 py-4">
            <span className="label-meta text-slate-400">RISK</span>
            <span className={cx('font-display text-[3rem] font-extrabold leading-none tabular-nums', ps.text)}>
              {riskScore.toFixed(1)}
            </span>
            <div className="mt-2 flex flex-col items-center gap-1">
              <span className="label-meta text-slate-400">CONFIDENCE</span>
              <span className="font-display text-lg font-bold text-slate-700">{confidence.toFixed(1)}</span>
            </div>
            <div className="mt-2 flex flex-col items-center gap-1">
              <span className="label-meta text-slate-400">SIGNALS</span>
              <span className="font-display text-lg font-bold text-slate-700">{signalCount}</span>
            </div>
          </div>
        </div>

        {/* Evidence streams */}
        <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {evidenceStreams.map((es) => (
            <div key={es.label} className="flex flex-col gap-1 rounded-lg border border-slate-100 bg-slate-50/80 px-3 py-2.5">
              <div className="flex items-center gap-1.5">
                <span className="text-emerald-600">{es.icon}</span>
                <span className="font-ui label-meta text-slate-500">{es.label}</span>
              </div>
              <div className="mt-1 flex items-end justify-between">
                <span className="font-display text-[18px] font-bold text-slate-800">{es.value}</span>
                <span className="font-ui text-[10px] font-semibold text-slate-400">{es.detail}</span>
              </div>
              {/* mini score bar */}
              <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-slate-200">
                <div
                  className="h-full rounded-full bg-emerald-500 transition-all duration-700"
                  style={{ width: `${Math.min(100, es.value)}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button
            onClick={() => navigate(investigationId ? `/investigations/${investigationId}` : '/network')}
            className="focus-ring flex items-center gap-2 rounded-lg bg-emerald-700 px-4 py-2 text-[13px] font-semibold text-white transition-colors hover:bg-emerald-800 font-ui"
          >
            <Network className="h-3.5 w-3.5" />
            INVESTIGATE NETWORK
          </button>
          <button
            onClick={() => navigate('/map')}
            className="focus-ring flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-[13px] font-semibold text-slate-700 transition-colors hover:bg-slate-50 font-ui"
          >
            <Map className="h-3.5 w-3.5" />
            VIEW ON MAP
          </button>
          <button
            onClick={() => navigate('/alerts')}
            className="focus-ring flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-[13px] font-semibold text-slate-700 transition-colors hover:bg-slate-50 font-ui"
          >
            <AlertCircle className="h-3.5 w-3.5" />
            VIEW ALERTS
          </button>
        </div>
      </div>
    </div>
  )
}
