import { Download, Copy } from 'lucide-react'
import { Investigation } from '../../types'
import { entityById } from '../../data/entities'
import { evidenceById } from '../../data/evidence'
import { SeverityBadge } from '../ui/Badge'
import { Severity } from '../../types'

function threatLevelFor(score: number): Severity {
  if (score >= 80) return 'CRITICAL'
  if (score >= 60) return 'HIGH'
  if (score >= 40) return 'MEDIUM'
  return 'WATCH'
}

export function ReportPreview({ investigation }: { investigation: Investigation }) {
  const entities = investigation.entityIds.map((id) => entityById(id)).filter(Boolean)
  const evidenceItems = investigation.evidenceIds.map((id) => evidenceById(id)).filter(Boolean)

  return (
    <div className="animate-fadeUp overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
            CASE-2026-{investigation.id.slice(-4).toUpperCase()}
          </div>
          <h2 className="mt-1 font-display text-[17px] font-bold text-slate-800">
            {investigation.codename} — Investigation Brief
          </h2>
        </div>
        <div className="flex gap-2">
          <button className="focus-ring flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-[12px] font-semibold text-slate-600 hover:bg-slate-50">
            <Copy className="h-3.5 w-3.5" />
            Copy Brief
          </button>
          <button className="focus-ring flex items-center gap-1.5 rounded-lg bg-emerald-700 px-3 py-1.5 text-[12px] font-semibold text-white hover:bg-emerald-800">
            <Download className="h-3.5 w-3.5" />
            Download PDF
          </button>
        </div>
      </div>

      <div className="space-y-5 px-5 py-5">
        <div className="flex flex-wrap items-center gap-4">
          <SeverityBadge severity={threatLevelFor(investigation.riskScore)} />
          <Field label="Primary Species / Commodity" value={investigation.primaryCommodity} />
          <Field label="Origin" value={investigation.originCountry} />
        </div>

        <Section title="Potential Transit Corridors">
          <p className="text-[14px] leading-relaxed text-slate-600">
            {investigation.routeIds.length} corridor{investigation.routeIds.length === 1 ? '' : 's'} associated with this
            investigation, spanning the incident locations recorded below. Route relationships are AI-generated
            hypotheses based on repeated identifier and timing overlap.
          </p>
        </Section>

        <Section title={`Related Incidents (${investigation.incidentIds.length})`}>
          <p className="text-[14px] leading-relaxed text-slate-600">
            Incidents span from the earliest recorded seizure through the most recent corridor activity, with
            recurring entity and route relationships documented in the evidence log.
          </p>
        </Section>

        <Section title={`Possible Entities (${entities.length})`}>
          <div className="flex flex-wrap gap-2">
            {entities.length === 0 ? (
              <p className="text-[13px] text-slate-400">No entity data available.</p>
            ) : (
              entities.map((e) => (
                <span key={e!.id} className="rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1 text-[13px] font-medium text-amber-700">
                  {e!.name} · {e!.confidence}%
                </span>
              ))
            )}
          </div>
        </Section>

        <Section title={`Supporting Evidence (${evidenceItems.length})`}>
          {evidenceItems.length === 0 ? (
            <p className="text-[13px] text-slate-400">No evidence records linked.</p>
          ) : (
            <ul className="space-y-1.5">
              {evidenceItems.slice(0, 6).map((ev) => (
                <li key={ev!.id} className="flex items-start gap-2 text-[12.5px]">
                  <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                  <span>
                    <span className="font-medium text-slate-700">{ev!.title}</span>
                    <span className="text-slate-400"> — {ev!.type.toLowerCase()}, {ev!.confidence}% confidence</span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="AI Assessment">
          <p className="text-[14px] leading-relaxed text-slate-600">{investigation.threatSummary || 'No AI assessment available for this investigation.'}</p>
          <p className="mt-2 text-[11px] italic text-slate-400">
            AI-generated intelligence assessment. Not proof of criminal activity.
          </p>
        </Section>

        <Section title="Investigative Priorities">
          <ul className="space-y-2">
            {[
              'Confirm identity of highest-confidence possible entity matches through corroborating field intelligence.',
              'Monitor corridor displacement patterns for continued route relocation.',
              'Cross-reference linguistic signals against future SignalWatch monitoring cycles.',
            ].map((p, i) => (
              <li key={i} className="flex items-start gap-2 text-[13.5px] text-slate-600">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                {p}
              </li>
            ))}
          </ul>
        </Section>
      </div>
    </div>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-[12px]">
      <span className="text-slate-400">{label}: </span>
      <span className="font-semibold text-slate-700">{value}</span>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-2 text-[10px] font-bold uppercase tracking-widest text-slate-400">{title}</h3>
      {children}
    </div>
  )
}
