import { cx } from '../../utils/format'
import { RiskDial } from '../ui/RiskIndicators'

interface EvidenceScore {
  label: string
  score: number
  color: string
  barColor: string
}

interface CrossEvidencePanelProps {
  riskScore: number
  crossAlignment: number
  tradeScore: number
  routeScore: number
  entityScore: number
  linguisticScore: number
  animalScore: number
}

export function CrossEvidencePanel({
  riskScore, crossAlignment,
  tradeScore, routeScore, entityScore, linguisticScore, animalScore,
}: CrossEvidencePanelProps) {
  const streams: EvidenceScore[] = [
    { label: 'TRADE',      score: tradeScore,     color: 'text-amber-700',  barColor: 'bg-amber-500' },
    { label: 'ROUTE',      score: routeScore,      color: 'text-red-700',    barColor: 'bg-red-500' },
    { label: 'ENTITY',     score: entityScore,     color: 'text-violet-700', barColor: 'bg-violet-500' },
    { label: 'LINGUISTIC', score: linguisticScore, color: 'text-blue-700',   barColor: 'bg-blue-500' },
    { label: 'ANIMAL',     score: animalScore,     color: 'text-emerald-700',barColor: 'bg-emerald-500' },
  ]

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-4 py-3">
        <span className="label-meta text-slate-500">WHY THIS MATTERS</span>
      </div>
      <div className="p-4">
        <div className="flex items-center gap-4">
          <RiskDial score={Math.round(riskScore)} size={72} />
          <div>
            <div className="font-display text-[13px] font-semibold text-slate-700">Risk Score</div>
            <div className="mt-0.5 text-[12px] text-slate-500">
              {riskScore >= 80
                ? 'Multiple independent evidence streams converge on the same trafficking corridor.'
                : 'Evidence streams indicate elevated trafficking activity on this corridor.'}
            </div>
          </div>
        </div>

        {/* Evidence stream bars */}
        <div className="mt-4 space-y-2.5">
          {streams.map((s) => (
            <div key={s.label} className="flex items-center gap-3">
              <span className={cx('font-mono-intel w-[68px] shrink-0 text-[9px] font-bold uppercase tracking-wider', s.color)}>
                {s.label}
              </span>
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
                <div
                  className={cx('h-full rounded-full transition-all duration-700', s.barColor)}
                  style={{ width: `${Math.min(100, s.score)}%` }}
                />
              </div>
              <span className="w-8 shrink-0 text-right font-mono-intel text-[10px] font-semibold text-slate-600">
                {Math.round(s.score)}
              </span>
            </div>
          ))}
        </div>

        {/* Cross-evidence alignment */}
        <div className="mt-4 rounded-lg border border-emerald-100 bg-emerald-50 px-3 py-2.5">
          <div className="flex items-center justify-between">
            <span className="label-meta text-emerald-700">CROSS-EVIDENCE ALIGNMENT</span>
            <span className="font-display text-lg font-bold text-emerald-700">{crossAlignment}</span>
          </div>
          <div className="mt-1.5 flex items-center gap-1.5">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className={cx(
                  'h-1.5 flex-1 rounded-full transition-all',
                  i < Math.round(crossAlignment / 20) ? 'bg-emerald-500' : 'bg-emerald-100'
                )}
              />
            ))}
          </div>
          <p className="mt-1.5 text-[10px] text-emerald-700 opacity-80">
            5 evidence streams converge on the same target
          </p>
        </div>
      </div>
    </div>
  )
}
