import { Severity } from '../../types'
import { severityColor } from '../../utils/format'
import { cx } from '../../utils/format'

export function SeverityBadge({ severity }: { severity: Severity }) {
  const c = severityColor[severity]
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 text-micro font-semibold uppercase tracking-widest',
        c.text,
        c.bg,
        c.border
      )}
    >
      <span className={cx('h-1.5 w-1.5 rounded-full', c.dot)} />
      {severity}
    </span>
  )
}

export function Badge({
  children,
  tone = 'default',
}: {
  children: React.ReactNode
  tone?: 'default' | 'emerald' | 'amber' | 'crimson' | 'cyan'
}) {
  const tones: Record<string, string> = {
    default: 'text-ink-400 bg-base-700/60 border-base-600',
    emerald: 'text-emerald-600 bg-emerald-500/10 border-emerald-500/30',
    amber: 'text-amber-600 bg-amber-500/10 border-amber-500/30',
    crimson: 'text-crimson-600 bg-crimson-500/10 border-crimson-500/30',
    cyan: 'text-cyan-600 bg-cyan-500/10 border-cyan-500/30',
  }
  return (
    <span className={cx('inline-flex items-center rounded-sm border px-2 py-0.5 text-micro font-semibold uppercase tracking-widest', tones[tone])}>
      {children}
    </span>
  )
}
