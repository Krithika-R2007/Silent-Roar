import { useState } from 'react'
import { Check, Loader2, Radar } from 'lucide-react'
import { apiClient } from '../../services/apiClient'
import { cx } from '../../utils/format'

const steps = [
  'Scanning known relationships…',
  'Comparing entities…',
  'Analyzing temporal patterns…',
  'Checking route overlaps…',
  'Correlating evidence…',
]

export function FindHiddenLinksButton({
  investigationId,
  onComplete,
}: {
  investigationId: string
  onComplete: () => void
}) {
  const [status, setStatus] = useState<'idle' | 'running' | 'done'>('idle')
  const [stepIndex, setStepIndex] = useState(0)
  const [result, setResult] = useState<{ relatedIncidents: number; recurringEntities: number; sharedCorridors: number; emergingNetworks: number } | null>(null)

  async function run() {
    setStatus('running')
    setStepIndex(0)
    const stepDuration = 420
    for (let i = 0; i < steps.length; i++) {
      setStepIndex(i)
      // eslint-disable-next-line no-await-in-loop
      await new Promise((r) => setTimeout(r, stepDuration))
    }
    const res = await apiClient.getHiddenLinks('INVESTIGATION', investigationId)
    setResult(res as any)
    setStatus('done')
  }

  if (status === 'idle') {
    return (
      <button
        onClick={run}
        className="focus-ring group flex w-full items-center justify-center gap-2.5 rounded-md border border-emerald-500/40 bg-emerald-500/10 py-3.5 text-[16px] font-bold text-emerald-700 transition-colors hover:bg-emerald-500/15"
      >
        <Radar className="h-4 w-4 transition-transform group-hover:rotate-45" />
        FIND HIDDEN LINKS
      </button>
    )
  }

  if (status === 'running') {
    return (
      <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
        <div className="mb-4 flex items-center gap-2.5 text-[14px] font-semibold text-emerald-700">
          <Loader2 className="h-4 w-4 animate-spin" />
          Running correlation analysis
        </div>
        <div className="space-y-2.5">
          {steps.map((s, i) => (
            <div key={s} className="flex items-center gap-2.5">
              <span
                className={cx(
                  'flex h-4 w-4 shrink-0 items-center justify-center rounded-full border text-[11px]',
                  i < stepIndex
                    ? 'border-emerald-500 bg-emerald-500 text-white'
                    : i === stepIndex
                    ? 'border-emerald-400 text-emerald-600'
                    : 'border-slate-300 text-transparent'
                )}
              >
                {i < stepIndex && <Check className="h-2.5 w-2.5" />}
              </span>
              <span
                className={cx(
                  'text-[13px] transition-colors',
                  i <= stepIndex ? 'text-slate-800' : 'text-slate-400'
                )}
              >
                {s}
              </span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="animate-fadeUp rounded-xl border border-emerald-200 bg-emerald-50 p-5">
      <div className="mb-3 flex items-center gap-2 text-[14px] font-bold text-emerald-700">
        <Check className="h-4 w-4" />
        Analysis complete
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <ResultStat label="Related incidents" value={result?.relatedIncidents ?? 0} />
        <ResultStat label="Recurring entities" value={result?.recurringEntities ?? 0} />
        <ResultStat label="Shared corridors" value={result?.sharedCorridors ?? 0} />
        <ResultStat label="Emerging networks" value={result?.emergingNetworks ?? 0} />
      </div>
      <button
        onClick={onComplete}
        className="focus-ring mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-700 py-2.5 text-[14px] font-bold text-white hover:bg-emerald-800"
      >
        View Network Graph
      </button>
    </div>
  )
}

function ResultStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-emerald-200 bg-white px-3 py-2.5 text-center shadow-sm">
      <div className="text-xl font-bold text-slate-800">{value}</div>
      <div className="mt-0.5 text-[11px] text-slate-500">{label}</div>
    </div>
  )
}
