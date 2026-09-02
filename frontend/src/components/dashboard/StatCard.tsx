import { LineChart, Line, ResponsiveContainer } from 'recharts'
import { ArrowUpRight, ArrowDownRight, LucideIcon } from 'lucide-react'
import { cx } from '../../utils/format'

export function StatCard({
  label,
  value,
  delta,
  trend,
  icon: Icon,
  sparkline,
  tone = 'emerald',
}: {
  label: string
  value: number | string
  delta?: string
  trend?: 'up' | 'down'
  icon: LucideIcon
  sparkline?: number[]
  tone?: 'emerald' | 'amber' | 'crimson' | 'cyan'
}) {
  const toneClasses: Record<string, string> = {
    emerald: 'text-emerald-600 bg-emerald-500/10',
    amber: 'text-amber-600 bg-amber-500/10',
    crimson: 'text-crimson-600 bg-crimson-500/10',
    cyan: 'text-cyan-600 bg-cyan-500/10',
  }
  const strokeColor: Record<string, string> = {
    emerald: '#2CAE5F',
    amber: '#D19A3E',
    crimson: '#C4433D',
    cyan: '#3E9AB0',
  }

  const data = (sparkline ?? []).map((v, i) => ({ i, v }))

  return (
    <div className="panel flex flex-col justify-between p-4">
      <div className="flex items-start justify-between">
        <div className={cx('flex h-8 w-8 items-center justify-center rounded-md', toneClasses[tone])}>
          <Icon className="h-4 w-4" strokeWidth={1.75} />
        </div>
        {delta && (
          <span
            className={cx(
              'flex items-center gap-0.5 text-micro font-semibold',
              trend === 'down' ? 'text-crimson-600' : 'text-emerald-600'
            )}
          >
            {trend === 'down' ? <ArrowDownRight className="h-3 w-3" /> : <ArrowUpRight className="h-3 w-3" />}
            {delta}
          </span>
        )}
      </div>

      <div className="mt-4 flex items-end justify-between gap-3">
        <div>
          <div className="text-3xl font-bold tabular-nums text-ink-100">{value}</div>
          <div className="mt-0.5 text-[14px] text-ink-500">{label}</div>
        </div>
        {data.length > 1 && (
          <div className="h-9 w-20 shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <Line type="monotone" dataKey="v" stroke={strokeColor[tone]} strokeWidth={1.75} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  )
}
