import { useNavigate } from 'react-router-dom'
import { ChevronRight, MapPin, AlertTriangle } from 'lucide-react'
import { Alert } from '../../types'
import { SeverityBadge } from '../ui/Badge'
import { locationById } from '../../data/locations'
import { cx, severityColor } from '../../utils/format'

export function PriorityIntelligencePanel({ alerts }: { alerts: Alert[] }) {
  const navigate = useNavigate()

  return (
    <div className="panel flex flex-col">
      <div className="flex items-center justify-between border-b border-base-700 px-5 py-4">
        <div>
          <h2 className="font-heading text-base font-bold uppercase tracking-wide text-ink-100">Priority Intelligence</h2>
          <p className="mt-0.5 font-ui text-[14px] text-ink-500">Ranked by risk score and evidence weight</p>
        </div>
        <button
          onClick={() => navigate('/alerts')}
          className="focus-ring flex items-center gap-1 text-micro font-semibold text-emerald-600 hover:text-emerald-700"
        >
          VIEW ALL
          <ChevronRight className="h-3 w-3" />
        </button>
      </div>

      <div className="divide-y divide-base-700">
        {alerts.map((alert) => {
          const loc = alert.locationId ? locationById(alert.locationId) : undefined
          const c = severityColor[alert.severity]
          const score = Number(alert.riskScore)
          const isMaxScore = score >= 100
          return (
            <button
              key={alert.id}
              onClick={() => navigate(alert.investigationId ? `/investigations/${alert.investigationId}` : '/alerts')}
              className="focus-ring group flex w-full items-start gap-4 px-5 py-3.5 text-left transition-colors hover:bg-base-800/60"
            >
              <div className={cx('mt-1 h-1.5 w-1.5 shrink-0 rounded-full', c.dot)} />
              <div className="min-w-0 flex-1 pr-2">
                <div className="flex items-center gap-2">
                  <SeverityBadge severity={alert.severity} />
                  <span className="text-micro text-ink-500">{alert.time}</span>
                </div>
                <div className="mt-1.5 line-clamp-2 text-[12px] font-bold leading-snug text-ink-100">{alert.title}</div>
                <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-ink-500">
                  <span>{alert.linkedIncidents} linked incident{alert.linkedIncidents === 1 ? '' : 's'}</span>
                  {alert.linkedCountries && <span>{alert.linkedCountries} countries</span>}
                  {loc && (
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {loc.name}
                    </span>
                  )}
                </div>
                <p className="mt-1 line-clamp-2 text-[11.5px] leading-relaxed text-ink-400">{alert.description}</p>
              </div>
              <div className="ml-2 flex shrink-0 flex-col items-end gap-0.5">
                <span className={cx(
                  'text-lg font-bold tabular-nums',
                  isMaxScore ? 'text-crimson-500' : 'text-ink-100'
                )}>
                  {score.toFixed(0)}
                </span>
                <span className="text-micro text-ink-500">RISK</span>
                {isMaxScore && (
                  <AlertTriangle className="mt-0.5 h-3 w-3 text-crimson-500" />
                )}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
