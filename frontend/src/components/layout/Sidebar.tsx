import { NavLink } from 'react-router-dom'
import {
  LayoutGrid,
  Map as MapIcon,
  FolderSearch,
  Waypoints,
  Bell,
  FileStack,
  MessageSquareWarning,
  FileText,
  ChevronsLeft,
  ChevronsRight,
  Activity,
  Settings,
  CircleUserRound,
} from 'lucide-react'
import { cx } from '../../utils/format'
import logo from '../../assets/logo.png'

const navItems = [
  { to: '/', label: 'Overview', icon: LayoutGrid, end: true },
  { to: '/map', label: 'Intelligence Map', icon: MapIcon },
  { to: '/investigations', label: 'Investigations', icon: FolderSearch },
  { to: '/network', label: 'Network Analysis', icon: Waypoints },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/evidence', label: 'Evidence', icon: FileStack },
  { to: '/signalwatch', label: 'SignalWatch', icon: MessageSquareWarning },
  { to: '/reports', label: 'Reports', icon: FileText },
]

export function Sidebar({
  collapsed,
  onToggle,
}: {
  collapsed: boolean
  onToggle: () => void
}) {
  return (
    <aside
      className={cx(
        'relative flex h-full flex-col border-r border-emerald-100 bg-white shadow-[2px_0_12px_rgba(20,148,71,0.06)] transition-all duration-200',
        collapsed ? 'w-[68px]' : 'w-[236px]'
      )}
    >
      <div className="flex h-16 items-center justify-center border-b border-emerald-100 px-3">
        {collapsed ? (
          <img src={logo} alt="Silent Roar" className="h-10 w-10 object-contain" />
        ) : (
          <img src={logo} alt="Silent Roar" className="h-11 w-auto object-contain" />
        )}
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2.5 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cx(
                'focus-ring group flex items-center gap-3 rounded-xl px-2.5 py-2 text-[15px] font-medium transition-colors',
                isActive
                  ? 'bg-emerald-500/10 text-emerald-700 ring-1 ring-inset ring-emerald-500/25'
                  : 'text-ink-400 hover:bg-emerald-50 hover:text-emerald-700'
              )
            }
            title={collapsed ? item.label : undefined}
          >
            <item.icon className="h-[17px] w-[17px] shrink-0" strokeWidth={1.75} />
            {!collapsed && <span className="truncate">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="space-y-0.5 border-t border-emerald-100 px-2.5 py-3">
        <div className={cx('flex items-center gap-3 rounded-xl px-2.5 py-2 text-[15px] text-ink-400', collapsed && 'justify-center')}>
          <Activity className="h-[17px] w-[17px] shrink-0 text-emerald-600" strokeWidth={1.75} />
          {!collapsed && (
            <div className="flex flex-1 items-center justify-between">
              <span>System Status</span>
              <span className="flex items-center gap-1 text-micro font-semibold text-emerald-600">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                LIVE
              </span>
            </div>
          )}
        </div>
        <button className={cx('focus-ring flex w-full items-center gap-3 rounded-xl px-2.5 py-2 text-[15px] text-ink-400 transition-colors hover:bg-emerald-50 hover:text-emerald-700', collapsed && 'justify-center')}>
          <Settings className="h-[17px] w-[17px] shrink-0" strokeWidth={1.75} />
          {!collapsed && <span>Settings</span>}
        </button>
        <button className={cx('focus-ring flex w-full items-center gap-3 rounded-xl px-2.5 py-2 text-[15px] text-ink-400 transition-colors hover:bg-emerald-50 hover:text-emerald-700', collapsed && 'justify-center')}>
          <CircleUserRound className="h-[17px] w-[17px] shrink-0" strokeWidth={1.75} />
          {!collapsed && <span>Analyst 07</span>}
        </button>
      </div>

      <button
        onClick={onToggle}
        className="focus-ring absolute -right-3 top-16 flex h-6 w-6 items-center justify-center rounded-full border border-emerald-200 bg-white text-emerald-600 shadow-sm hover:bg-emerald-50 hover:text-emerald-700"
      >
        {collapsed ? <ChevronsRight className="h-3.5 w-3.5" /> : <ChevronsLeft className="h-3.5 w-3.5" />}
      </button>
    </aside>
  )
}
