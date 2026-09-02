import { Channel } from '../../types'
import { cx } from '../../utils/format'
import { Hash } from 'lucide-react'

export function ChannelList({
  channels,
  activeId,
  onSelect,
}: {
  channels: Channel[]
  activeId: string | null
  onSelect: (id: string) => void
}) {
  return (
    <div className="panel flex h-full flex-col overflow-hidden">
      <div className="border-b border-base-700 px-4 py-3.5">
        <span className="font-heading label-meta">Channels</span>
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {channels.map((c) => (
          <button
            key={c.id}
            onClick={() => onSelect(c.id)}
            className={cx(
              'focus-ring flex w-full items-center gap-2.5 rounded-md px-3 py-2.5 text-left transition-colors',
              activeId === c.id ? 'bg-emerald-500/10 text-emerald-700' : 'text-ink-400 hover:bg-base-800 hover:text-ink-200'
            )}
          >
            <Hash className="h-3.5 w-3.5 shrink-0" />
            <div className="min-w-0 flex-1">
              <div className="truncate font-ui text-[15px] font-medium">{c.name}</div>
              <div className="font-ui text-[13px] text-ink-600">{c.memberCount} members · {c.lastActivity}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
