import { SignalMessage } from '../../types'
import { formatDateTime, cx } from '../../utils/format'
import { AlertTriangle, CheckCircle2 } from 'lucide-react'

export function ConversationWindow({
  messages,
  selectedId,
  onSelect,
}: {
  messages: SignalMessage[]
  selectedId: string | null
  onSelect: (message: SignalMessage) => void
}) {
  return (
    <div className="panel flex h-full flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-base-700 px-4 py-3.5">
        <span className="label-meta">Conversation</span>
        <span className="flex items-center gap-1 text-micro font-semibold text-amber-600">
          <AlertTriangle className="h-3 w-3" />
          SYNTHETIC DEMO DATA
        </span>
      </div>

      <div className="flex-1 space-y-1 overflow-y-auto p-3">
        {messages.map((m) => (
          <button
            key={m.id}
            onClick={() => onSelect(m)}
            className={cx(
              'focus-ring block w-full rounded-md border px-3.5 py-2.5 text-left transition-colors',
              selectedId === m.id
                ? 'border-emerald-500/40 bg-emerald-500/8'
                : 'border-transparent hover:bg-base-800/60'
            )}
          >
            <div className="flex items-center justify-between">
              <span className="text-[12.5px] font-semibold text-ink-200">{m.author}</span>
              <span className="text-[13px] text-ink-600">{formatDateTime(m.timestamp)}</span>
            </div>
            <p className="mt-1 text-[15px] text-ink-300">{m.text}</p>
            <div className="mt-1.5 flex items-center gap-2">
              {m.flaggedTerms.length > 0 && (
                <span className="flex items-center gap-1 text-[13px] text-amber-600">
                  <AlertTriangle className="h-3 w-3" />
                  {m.flaggedTerms.length} flagged term{m.flaggedTerms.length === 1 ? '' : 's'}
                </span>
              )}
              {m.addedToInvestigation && (
                <span className="flex items-center gap-1 text-[13px] text-emerald-600">
                  <CheckCircle2 className="h-3 w-3" />
                  In investigation
                </span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
