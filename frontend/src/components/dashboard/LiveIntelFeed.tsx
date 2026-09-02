import { useNavigate } from 'react-router-dom'
import { TrendingUp, MapPin, Network, MessageSquare, AlertTriangle, Activity } from 'lucide-react'
import { cx } from '../../utils/format'
import { Alert } from '../../types'

const iconMap: Record<string, React.ReactNode> = {
  ROUTE:      <TrendingUp className="h-3.5 w-3.5" />,
  LOCATION:   <MapPin className="h-3.5 w-3.5" />,
  NETWORK:    <Network className="h-3.5 w-3.5" />,
  LINGUISTIC: <MessageSquare className="h-3.5 w-3.5" />,
  ALERT:      <AlertTriangle className="h-3.5 w-3.5" />,
  SIGNAL:     <Activity className="h-3.5 w-3.5" />,
}

const priorityDot: Record<string, string> = {
  CRITICAL: 'bg-red-500',
  HIGH:     'bg-amber-500',
  MEDIUM:   'bg-teal-500',
  WATCH:    'bg-slate-400',
}

function narrativeTitle(alert: Alert): string {
  const t = alert.title.toLowerCase()
  if (t.includes('corridor') || t.includes('route')) return `Route activity elevated — ${alert.title}`
  if (t.includes('linguistic') || t.includes('signal')) return `Coded terminology detected — ${alert.title}`
  if (t.includes('entity') || t.includes('network')) return `Entity relationship strengthened — ${alert.title}`
  if (t.includes('behaviour') || t.includes('anomaly')) return `Behavioural anomaly detected — ${alert.title}`
  if (t.includes('environmental') || t.includes('satellite')) return `Environmental signal — ${alert.title}`
  return alert.title
}

function itemType(alert: Alert): string {
  const t = alert.title.toLowerCase()
  if (t.includes('route') || t.includes('corridor')) return 'ROUTE'
  if (t.includes('entity') || t.includes('network')) return 'NETWORK'
  if (t.includes('linguistic') || t.includes('signal')) return 'LINGUISTIC'
  if (t.includes('location') || t.includes('hub')) return 'LOCATION'
  return 'ALERT'
}

export function LiveIntelFeed({ alerts }: { alerts: Alert[] }) {
  const navigate = useNavigate()

  return (
    <div className="flex h-full flex-col rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          <span className="label-meta text-slate-600">LIVE INTELLIGENCE</span>
        </div>
        <button
          onClick={() => navigate('/alerts')}
          className="focus-ring text-[11px] font-semibold text-emerald-700 hover:underline"
        >
          View all →
        </button>
      </div>

      <div className="flex-1 divide-y divide-slate-100 overflow-y-auto">
        {alerts.map((alert) => {
          const type = itemType(alert)
          const dot = priorityDot[alert.severity] ?? priorityDot.WATCH
          return (
            <button
              key={alert.id}
              onClick={() => navigate(alert.investigationId ? `/investigations/${alert.investigationId}` : '/alerts')}
              className="focus-ring group flex w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-slate-50"
            >
              <div className="mt-0.5 flex shrink-0 flex-col items-center gap-1.5">
                <span className={cx('h-1.5 w-1.5 rounded-full', dot)} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-emerald-600">{iconMap[type]}</span>
                  <span className="font-mono-intel text-[9px] font-bold uppercase tracking-wider text-slate-400">{type}</span>
                </div>
                <p className="mt-0.5 text-[12px] font-semibold leading-snug text-slate-800 group-hover:text-emerald-800">
                  {narrativeTitle(alert)}
                </p>
                <p className="mt-0.5 line-clamp-2 font-ui text-[11px] leading-relaxed text-slate-500">
                  {alert.description}
                </p>
                <div className="mt-1.5 flex items-center gap-3 font-ui text-[10px] text-slate-400">
                  <span>{alert.time}</span>
                  {alert.linkedIncidents > 0 && (
                    <span>{alert.linkedIncidents} linked incident{alert.linkedIncidents !== 1 ? 's' : ''}</span>
                  )}
                  <span className="font-semibold text-slate-500">Risk {alert.riskScore}</span>
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
