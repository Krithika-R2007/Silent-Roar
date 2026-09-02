import { useState } from 'react'
import { ChevronDown, Info } from 'lucide-react'
import { RiskFactor } from '../../types'
import { RiskDial } from '../ui/RiskIndicators'
import { cx } from '../../utils/format'

export function ExplainableAIPanel({ riskScore, factors }: { riskScore: number; factors: RiskFactor[] }) {
  const [expanded, setExpanded] = useState(true)
  const maxPoints = factors.length > 0 ? Math.max(...factors.map((f) => f.points)) : 1

  return (
    <div className="panel overflow-hidden">
      <button
        onClick={() => setExpanded((e) => !e)}
        className="focus-ring flex w-full items-center justify-between px-5 py-4"
      >
        <div className="flex items-center gap-3">
          <RiskDial score={riskScore} size={48} />
          <div className="text-left">
            <h2 className="font-heading text-base font-bold uppercase tracking-wide text-ink-100">Why This Risk Score?</h2>
            <p className="mt-0.5 font-ui text-[14px] text-ink-500">AI-generated contribution breakdown</p>
          </div>
        </div>
        <ChevronDown className={cx('h-4 w-4 text-ink-500 transition-transform', expanded && 'rotate-180')} />
      </button>

      {expanded && (
        <div className="animate-fadeUp space-y-3 border-t border-base-700 px-5 py-4">
          {factors.length === 0 ? (
            <p className="text-[13px] text-ink-500">No risk factors available for this investigation.</p>
          ) : (
            factors.map((f) => (
              <div key={f.label}>
                <div className="mb-1 flex items-center justify-between text-[12.5px]">
                  <span className="text-ink-300">{f.label}</span>
                  <span className="font-semibold text-emerald-600">+{f.points}</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-base-700">
                  <div
                    className="h-full rounded-full bg-emerald-500 transition-all duration-700"
                    style={{ width: `${(f.points / maxPoints) * 100}%` }}
                  />
                </div>
              </div>
            ))
          )}

          <div className="mt-2 flex items-start gap-2 rounded-md border border-base-600 bg-base-800/60 px-3 py-2.5 text-[14px] leading-relaxed text-ink-500">
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ink-500" />
            AI-generated intelligence assessment. Not proof of criminal activity.
          </div>
        </div>
      )}
    </div>
  )
}
