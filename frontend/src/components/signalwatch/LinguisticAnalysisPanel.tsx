import { useNavigate } from 'react-router-dom'
import { SignalMessage } from '../../types'
import { ConfidenceBar } from '../ui/States'
import { MapPin, PlusCircle, Check, ScanSearch } from 'lucide-react'

export function LinguisticAnalysisPanel({
  message,
  onAddToInvestigation,
}: {
  message: SignalMessage | null
  onAddToInvestigation: (message: SignalMessage) => void
}) {
  const navigate = useNavigate()

  if (!message) {
    return (
      <div className="panel flex h-full flex-col items-center justify-center gap-2 p-6 text-center">
        <ScanSearch className="h-5 w-5 text-ink-600" />
        <p className="text-[12.5px] text-ink-500">Select a message to view linguistic analysis.</p>
      </div>
    )
  }

  return (
    <div className="panel flex h-full flex-col overflow-hidden">
      <div className="border-b border-base-700 px-4 py-3.5">
        <span className="font-heading label-meta text-emerald-600">AI Linguistic Analysis</span>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        <div className="rounded-md border border-base-700 bg-base-850 p-3">
          <p className="text-[15px] italic text-ink-300">"{message.text}"</p>
        </div>

        {message.flaggedTerms.map((term) => (
          <div key={term.term} className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-ui text-[12.5px] font-semibold text-ink-200">Potential coded terminology</span>
            </div>
            <div className="rounded-md border border-amber-500/25 bg-amber-500/5 px-3 py-2">
              <span className="text-[15px] font-medium text-amber-600">"{term.term}"</span>
            </div>
            <ConfidenceBar value={term.confidence} />
            <div className="pt-1">
              <span className="label-meta mb-1.5 block">Contextual indicators</span>
              <ul className="space-y-1">
                {['Repeated terminology', 'Location reference', 'Route reference', 'Historical pattern similarity']
                  .slice(0, 2 + Math.round(term.confidence / 40))
                  .map((ind) => (
                    <li key={ind} className="flex items-center gap-2 text-[14px] text-ink-400">
                      <span className="h-1 w-1 rounded-full bg-emerald-400" />
                      {ind}
                    </li>
                  ))}
              </ul>
            </div>
          </div>
        ))}

        <div className="rounded-md border border-base-600 bg-base-800/60 px-3 py-2.5 text-[11.5px] leading-relaxed text-ink-500">
          Ordinary words are not inherently criminal. This is an AI hypothesis based on context, not a confirmed determination.
        </div>

        {message.locationMention && (
          <div className="rounded-md border border-cyan-500/25 bg-cyan-500/5 p-3">
            <div className="flex items-center gap-1.5 text-[12.5px] font-semibold text-cyan-600">
              <MapPin className="h-3.5 w-3.5" />
              Location Signal Detected
            </div>
            <div className="mt-1 text-[15px] text-ink-200">{message.locationMention.label}</div>
            <button
              onClick={() => navigate(`/map?location=${message.locationMention?.locationId}`)}
              className="focus-ring mt-2.5 flex w-full items-center justify-center gap-1.5 rounded-md border border-cyan-500/30 py-1.5 text-[12.5px] font-semibold text-cyan-600 hover:bg-cyan-500/10"
            >
              View On Map
            </button>
          </div>
        )}

        <button
          onClick={() => onAddToInvestigation(message)}
          disabled={message.addedToInvestigation}
          className="focus-ring flex w-full items-center justify-center gap-2 rounded-md bg-emerald-500 py-2.5 text-[15px] font-bold text-base-950 transition-colors hover:bg-emerald-400 disabled:cursor-default disabled:bg-emerald-900/50 disabled:text-emerald-500"
        >
          {message.addedToInvestigation ? (
            <>
              <Check className="h-4 w-4" /> Added to Investigation
            </>
          ) : (
            <>
              <PlusCircle className="h-4 w-4" /> Add to Investigation
            </>
          )}
        </button>
      </div>
    </div>
  )
}
