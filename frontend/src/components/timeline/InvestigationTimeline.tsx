import { useState } from 'react'
import { TimelineEvent } from '../../types'
import { evidenceById } from '../../data/evidence'
import { formatDateShort } from '../../utils/format'
import { ConfidenceBar } from '../ui/States'
import { cx } from '../../utils/format'

export function InvestigationTimeline({ events }: { events: TimelineEvent[] }) {
  const [openId, setOpenId] = useState<string | null>(events[0]?.id ?? null)

  return (
    <div className="relative pl-6">
      <div className="absolute bottom-2 left-[7px] top-2 w-px bg-base-700" />
      <div className="space-y-1">
        {events.map((event) => {
          const isOpen = openId === event.id
          const ev = event.evidenceId ? evidenceById(event.evidenceId) : undefined
          return (
            <div key={event.id} className="relative">
              <span
                className={cx(
                  'absolute -left-6 top-1.5 h-3 w-3 rounded-full ring-4 ring-base-950',
                  isOpen ? 'bg-emerald-400' : 'bg-base-600'
                )}
              />
              <button
                onClick={() => setOpenId(isOpen ? null : event.id)}
                className="focus-ring w-full rounded-md px-3 py-3 text-left transition-colors hover:bg-base-800/60"
              >
                <div className="flex items-center gap-2.5">
                  <span className="label-meta text-emerald-600">{formatDateShort(event.date)}</span>
                </div>
                <div className="mt-1 text-[13.5px] font-semibold text-ink-100">{event.title}</div>
                <p className="mt-1 text-[12.5px] leading-relaxed text-ink-400">{event.description}</p>
              </button>

              {isOpen && ev && (
                <div className="animate-fadeUp ml-3 mt-1 mb-2 rounded-md border border-base-700 bg-base-850 p-3.5">
                  <div className="flex items-center justify-between">
                    <span className="label-meta text-ink-500">{ev.type} Evidence</span>
                    <span className="text-micro text-ink-500">{ev.source}</span>
                  </div>
                  <p className="mt-1.5 text-[12.5px] text-ink-300">{ev.description}</p>
                  <div className="mt-2.5">
                    <ConfidenceBar value={ev.confidence} compact />
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
