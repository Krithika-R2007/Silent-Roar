import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronRight, Clock } from 'lucide-react'
import { Investigation } from '../types'
import { apiClient } from '../services/apiClient'
import { LoadingState } from '../components/ui/States'
import { RiskDial } from '../components/ui/RiskIndicators'
import { Badge } from '../components/ui/Badge'
import { cx } from '../utils/format'

export default function Investigations() {
  const [investigations, setInvestigations] = useState<Investigation[] | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    apiClient.getInvestigations().then(setInvestigations)
  }, [])

  if (!investigations) return <LoadingState />

  return (
    <div className="mx-auto max-w-[1400px] space-y-4 p-6">
      <div className="flex items-center justify-between">
        <p className="text-[15px] text-ink-500">{investigations.length} investigations · sorted by risk score</p>
      </div>

      <div className="space-y-3">
        {[...investigations]
          .sort((a, b) => b.riskScore - a.riskScore)
          .map((inv) => (
            <button
              key={inv.id}
              onClick={() => navigate(`/investigations/${inv.id}`)}
              className="focus-ring panel flex w-full items-center gap-5 p-5 text-left transition-colors hover:border-emerald-500/30"
            >
              <RiskDial score={inv.riskScore} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <Badge tone={inv.status === 'ACTIVE' ? 'emerald' : 'default'}>{inv.status}</Badge>
                  <span className="flex items-center gap-1 font-ui text-micro text-ink-500">
                    <Clock className="h-3 w-3" />
                    {inv.lastUpdated}
                  </span>
                </div>
                <div className="mt-1.5 truncate font-display text-[15px] font-bold text-ink-100">{inv.codename}</div>
                <p className="mt-1 truncate text-[13.5px] text-ink-400">{inv.threatSummary}</p>
                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 font-ui text-[12.5px] text-ink-500">
                  <span>{inv.incidentIds.length} incidents</span>
                  <span>{inv.entityIds.length} entities</span>
                  <span>{inv.primaryCommodity}</span>
                  <span>Origin: {inv.originCountry}</span>
                </div>
              </div>
              <ChevronRight className={cx('h-4 w-4 shrink-0 text-ink-500')} />
            </button>
          ))}
      </div>
    </div>
  )
}
