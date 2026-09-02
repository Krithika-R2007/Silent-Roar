import { useNavigate } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { cx, riskTone } from '../../utils/format'

interface PriorityItem {
  rank: number
  title: string
  priority: 'IMMEDIATE' | 'HIGH' | 'WATCH'
  riskScore: number
  confidence: number
  evidenceStreams: number
  reason: string
  id?: string
}

const priorityBadge: Record<string, string> = {
  IMMEDIATE: 'bg-red-100 text-red-700 border-red-200',
  HIGH:      'bg-amber-100 text-amber-700 border-amber-200',
  WATCH:     'bg-slate-100 text-slate-600 border-slate-200',
}

export function InvestigationPriorityQueue({ items }: { items: PriorityItem[] }) {
  const navigate = useNavigate()

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-4 py-3">
        <span className="label-meta text-slate-500">WHERE SHOULD WE LOOK NEXT?</span>
      </div>
      <div className="divide-y divide-slate-100">
        {items.map((item) => (
          <button
            key={item.rank}
            onClick={() => navigate(item.id ? `/investigations/${item.id}` : '/investigations')}
            className="focus-ring group flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-slate-50"
          >
            <span className="font-mono-intel w-5 shrink-0 text-[13px] font-bold text-slate-300">
              {String(item.rank).padStart(2, '0')}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-display text-[13px] font-semibold text-slate-800 group-hover:text-emerald-800">{item.title}</span>
                <span className={cx('rounded border px-1.5 py-0.5 text-[9px] font-bold tracking-wide', priorityBadge[item.priority])}>
                  {item.priority}
                </span>
              </div>
              <p className="mt-0.5 font-ui text-[11px] text-slate-500">{item.reason}</p>
              <div className="mt-1 flex items-center gap-3 font-ui text-[10px] text-slate-400">
                <span>Risk <span className={cx('font-semibold', riskTone(item.riskScore))}>{item.riskScore.toFixed(1)}</span></span>
                <span>Confidence {item.confidence.toFixed(0)}</span>
                <span>{item.evidenceStreams} evidence streams</span>
              </div>
            </div>
            <ChevronRight className="h-4 w-4 shrink-0 text-slate-300 transition-colors group-hover:text-emerald-500" />
          </button>
        ))}
      </div>
    </div>
  )
}
