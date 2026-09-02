import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapPin, Check, FolderOpen } from 'lucide-react'
import { Alert, Severity } from '../types'
import { apiClient } from '../services/apiClient'
import { LoadingState, EmptyState } from '../components/ui/States'
import { SeverityBadge } from '../components/ui/Badge'
import { locationById } from '../data/locations'
import { cx } from '../utils/format'

type FilterKey = Severity | 'ALL'
const filters: FilterKey[] = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'WATCH']

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[] | null>(null)
  const [filter, setFilter] = useState<FilterKey>('ALL')
  const [reviewed, setReviewed] = useState<Set<string>>(new Set())
  const navigate = useNavigate()

  useEffect(() => {
    apiClient.getAlerts().then((res) => setAlerts(res.alerts as unknown as Alert[]))
  }, [])

  if (!alerts) return <LoadingState />

  const filtered = alerts.filter((a) => filter === 'ALL' || a.severity === filter)

  return (
    <div className="mx-auto max-w-[1400px] space-y-4 p-6">
      <div className="flex flex-wrap gap-2">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cx(
              'focus-ring rounded-md border px-3.5 py-1.5 text-[12.5px] font-semibold uppercase tracking-wide transition-colors',
              filter === f
                ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-700'
                : 'border-base-700 text-ink-400 hover:border-base-600 hover:text-ink-200'
            )}
          >
            {f}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyState title="No alerts found" description="Try a different severity filter." />
      ) : (
        <div className="space-y-3">
          {filtered.map((alert) => {
            const loc = alert.locationId ? locationById(alert.locationId) : undefined
            const isReviewed = reviewed.has(alert.id) || alert.status === 'REVIEWED'
            return (
              <div key={alert.id} className="panel p-4">
                <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <SeverityBadge severity={alert.severity} />
                      <span className="text-micro text-ink-500">{alert.time}</span>
                      {isReviewed && (
                        <span className="flex items-center gap-1 text-micro font-semibold text-emerald-600">
                          <Check className="h-3 w-3" /> REVIEWED
                        </span>
                      )}
                    </div>
                    <div className="mt-1.5 line-clamp-2 font-display text-[14px] font-bold leading-snug text-ink-100">{alert.title}</div>
                    <p className="mt-1 line-clamp-2 text-[12.5px] leading-relaxed text-ink-400">{alert.description}</p>
                    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 font-ui text-[12.5px] text-ink-500">
                      <span>Risk {Number(alert.riskScore).toFixed(0)}</span>
                      <span>{alert.evidenceCount} evidence item{alert.evidenceCount === 1 ? '' : 's'}</span>
                      <span>{alert.linkedIncidents} linked incident{alert.linkedIncidents === 1 ? '' : 's'}</span>
                      {loc && (
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {loc.name}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex shrink-0 gap-2">
                    <button
                      onClick={() => setReviewed((prev) => new Set(prev).add(alert.id))}
                      disabled={isReviewed}
                      className="focus-ring flex items-center gap-1.5 rounded-md border border-base-600 px-3 py-1.5 text-[12.5px] font-medium text-ink-300 transition-colors hover:border-base-500 hover:text-ink-100 disabled:opacity-40"
                    >
                      <Check className="h-3.5 w-3.5" />
                      Mark reviewed
                    </button>
                    <button
                      onClick={() => navigate(alert.investigationId ? `/investigations/${alert.investigationId}` : '/investigations')}
                      className="focus-ring flex items-center gap-1.5 rounded-md bg-emerald-500/10 px-3 py-1.5 text-[12.5px] font-medium text-emerald-700 transition-colors hover:bg-emerald-500/15"
                    >
                      <FolderOpen className="h-3.5 w-3.5" />
                      Open investigation
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
