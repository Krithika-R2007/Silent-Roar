import { useNavigate } from 'react-router-dom'
import { Search, Network, FileText, Map, MessageSquareWarning } from 'lucide-react'

const actions = [
  { label: 'Find Hidden Link',  icon: Search,               to: '/network',     accent: 'emerald' },
  { label: 'View Network',      icon: Network,              to: '/network',     accent: 'violet' },
  { label: 'Generate Brief',    icon: FileText,             to: '/reports',     accent: 'amber' },
  { label: 'Open Map',          icon: Map,                  to: '/map',         accent: 'teal' },
  { label: 'Analyze Message',   icon: MessageSquareWarning, to: '/signalwatch', accent: 'blue' },
]

const accentBtn: Record<string, string> = {
  emerald: 'hover:bg-emerald-50 hover:text-emerald-800 hover:border-emerald-300 text-emerald-700',
  violet:  'hover:bg-violet-50 hover:text-violet-800 hover:border-violet-300 text-violet-700',
  amber:   'hover:bg-amber-50 hover:text-amber-800 hover:border-amber-300 text-amber-700',
  teal:    'hover:bg-teal-50 hover:text-teal-800 hover:border-teal-300 text-teal-700',
  blue:    'hover:bg-blue-50 hover:text-blue-800 hover:border-blue-300 text-blue-700',
}

export function InvestigationActions() {
  const navigate = useNavigate()

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-4 py-3">
        <span className="label-meta text-slate-500">INVESTIGATION TOOLS</span>
      </div>
      <div className="grid grid-cols-1 gap-2 p-3 sm:grid-cols-5">
        {actions.map(({ label, icon: Icon, to, accent }) => (
          <button
            key={label}
            onClick={() => navigate(to)}
            className={`focus-ring flex flex-col items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-center transition-all ${accentBtn[accent]}`}
          >
            <Icon className="h-4 w-4" strokeWidth={1.75} />
            <span className="font-ui text-[11px] font-semibold leading-tight">{label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
