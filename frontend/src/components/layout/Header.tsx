import { Bell, CircleUserRound } from 'lucide-react'
import { GlobalSearch } from './GlobalSearch'
import { alerts } from '../../data/alerts'

export function Header({ title }: { title: string }) {
  const newAlerts = alerts.filter((a) => a.status === 'NEW').length

  return (
    <header className="flex h-16 shrink-0 items-center justify-between gap-6 border-b border-emerald-100 bg-white/95 px-6 shadow-[0_2px_8px_rgba(20,148,71,0.06)] backdrop-blur-sm">
      <div className="min-w-[200px]">
        <div className="text-[17px] font-bold uppercase tracking-wide text-ink-100">{title}</div>
      </div>

      <GlobalSearch />

      <div className="flex shrink-0 items-center gap-4">

        <button className="focus-ring relative flex h-8 w-8 items-center justify-center rounded-xl text-ink-400 hover:bg-emerald-50 hover:text-emerald-700">
          <Bell className="h-[17px] w-[17px]" strokeWidth={1.75} />
          {newAlerts > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-crimson-500 px-1 text-[12px] font-bold text-white">
              {newAlerts}
            </span>
          )}
        </button>

        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          <span className="text-micro text-ink-400">SYSTEM NOMINAL</span>
        </div>

        <div className="flex items-center gap-2 border-l border-emerald-100 pl-4">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
            <CircleUserRound className="h-4 w-4" />
          </div>
          <span className="text-[15px] font-medium text-ink-300">Analyst 07</span>
        </div>
      </div>
    </header>
  )
}
