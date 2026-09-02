import { Loader2, Inbox, TriangleAlert } from 'lucide-react'
import { cx } from '../../utils/format'

export function ConfidenceBar({ value, compact = false }: { value: number; compact?: boolean }) {
  return (
    <div className="w-full">
      {!compact && (
        <div className="mb-1 flex items-center justify-between">
          <span className="text-micro text-ink-500">Confidence</span>
          <span className="text-micro font-semibold text-emerald-600">{value}%</span>
        </div>
      )}
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-base-700">
        <div className="h-full rounded-full bg-emerald-500 transition-all duration-700" style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}

export function LoadingState({ label = 'Loading intelligence…', className }: { label?: string; className?: string }) {
  return (
    <div className={cx('flex flex-col items-center justify-center gap-3 py-16 text-ink-500', className)}>
      <Loader2 className="h-5 w-5 animate-spin text-emerald-500" />
      <span className="text-micro">{label}</span>
    </div>
  )
}

export function EmptyState({
  title,
  description,
  icon,
}: {
  title: string
  description?: string
  icon?: React.ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-16 text-center">
      <div className="mb-1 flex h-10 w-10 items-center justify-center rounded-full bg-base-700/60 text-ink-500">
        {icon ?? <Inbox className="h-4 w-4" />}
      </div>
      <p className="text-base font-medium text-ink-300">{title}</p>
      {description && <p className="max-w-xs text-sm text-ink-500">{description}</p>}
    </div>
  )
}

export function ErrorState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-16 text-center">
      <div className="mb-1 flex h-10 w-10 items-center justify-center rounded-full bg-crimson-500/10 text-crimson-600">
        <TriangleAlert className="h-4 w-4" />
      </div>
      <p className="text-base font-medium text-ink-300">{title}</p>
      {description && <p className="max-w-xs text-sm text-ink-500">{description}</p>}
    </div>
  )
}
