import { useEffect, useState } from 'react'
import { FileText, Sparkles, Loader2, Download, ExternalLink } from 'lucide-react'
import { Report, Investigation } from '../types'
import { apiClient } from '../services/apiClient'
import { LoadingState } from '../components/ui/States'
import { SeverityBadge } from '../components/ui/Badge'
import { ReportPreview } from '../components/reports/ReportPreview'
import { formatDate, cx } from '../utils/format'

const threatColors: Record<string, string> = {
  CRITICAL: 'border-l-red-500',
  HIGH:     'border-l-amber-500',
  MEDIUM:   'border-l-blue-500',
  WATCH:    'border-l-slate-400',
}

export default function Reports() {
  const [reports, setReports] = useState<Report[] | null>(null)
  const [investigations, setInvestigations] = useState<Investigation[] | null>(null)
  const [generating, setGenerating] = useState(false)
  const [generated, setGenerated] = useState<Investigation | null>(null)

  useEffect(() => {
    apiClient.getReports().then(setReports)
    apiClient.getInvestigations().then(setInvestigations)
  }, [])

  async function handleGenerate() {
    setGenerating(true)
    setGenerated(null)
    const topInvestigation = investigations?.[0]
    const result = topInvestigation
      ? await apiClient.getInvestigationBrief(
          (topInvestigation as any).target_type ?? 'ROUTE',
          topInvestigation.id
        )
      : null
    setGenerating(false)
    setGenerated(result as unknown as Investigation)
  }

  if (!reports) return <LoadingState />

  return (
    <div className="mx-auto max-w-[1400px] space-y-6 p-6">

      {/* Generate Brief Button */}
      <button
        onClick={handleGenerate}
        disabled={generating}
        className="focus-ring flex w-full items-center justify-center gap-2.5 rounded-2xl border border-emerald-500/40 bg-emerald-500/10 py-4 text-[15px] font-bold text-emerald-700 transition-colors hover:bg-emerald-500/15 disabled:opacity-70"
      >
        {generating ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            GENERATING INVESTIGATION BRIEF…
          </>
        ) : (
          <>
            <Sparkles className="h-4 w-4" />
            GENERATE INVESTIGATION BRIEF
          </>
        )}
      </button>

      {/* Generated Preview */}
      {generated && <ReportPreview investigation={generated} />}

      {/* Existing Reports */}
      <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-5 py-4">
          <h2 className="font-display text-[15px] font-bold text-slate-800">
            Intelligence Reports
          </h2>
          <p className="mt-0.5 text-[12px] text-slate-500">
            {reports.length} report{reports.length !== 1 ? 's' : ''} on record
          </p>
        </div>

        {reports.length === 0 ? (
          <div className="flex flex-col items-center gap-3 px-5 py-12 text-center">
            <FileText className="h-8 w-8 text-slate-300" />
            <p className="text-[14px] text-slate-400">No reports yet. Generate an investigation brief above.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {reports.map((r) => (
              <div
                key={r.id}
                className={cx(
                  'flex items-center justify-between gap-4 border-l-4 px-5 py-4 transition-colors hover:bg-slate-50',
                  threatColors[r.threatLevel] ?? 'border-l-slate-300'
                )}
              >
                <div className="flex items-center gap-4">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-500">
                    <FileText className="h-5 w-5" />
                  </span>
                  <div>
                    <div className="font-display text-[14px] font-semibold text-slate-800">{r.title}</div>
                    <div className="mt-0.5 flex items-center gap-2 text-[12px] text-slate-500">
                      <span className="font-mono-intel font-medium text-slate-600">{r.caseId}</span>
                      <span className="text-slate-300">·</span>
                      <span>{formatDate(r.generatedAt)}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <SeverityBadge severity={r.threatLevel} />
                  <button className="focus-ring flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-[12px] font-semibold text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-800">
                    <Download className="h-3.5 w-3.5" />
                    Export
                  </button>
                  <button className="focus-ring flex items-center gap-1.5 rounded-lg bg-emerald-700 px-3 py-1.5 text-[12px] font-semibold text-white transition-colors hover:bg-emerald-800">
                    <ExternalLink className="h-3.5 w-3.5" />
                    View
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
