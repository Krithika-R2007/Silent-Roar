import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'

const titleMap: Record<string, string> = {
  '/': 'Intelligence Overview',
  '/map': 'Intelligence Map',
  '/investigations': 'Investigations',
  '/network': 'Network Analysis',
  '/alerts': 'Alerts',
  '/evidence': 'Evidence',
  '/signalwatch': 'SignalWatch',
  '/reports': 'Reports',
}

function resolveTitle(pathname: string) {
  if (titleMap[pathname]) return titleMap[pathname]
  if (pathname.startsWith('/investigations/')) return 'Investigation Detail'
  return 'Silent Roar'
}

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  return (
    <div className="flex h-screen w-full overflow-hidden" style={{ background: '#EFF6F1' }}>
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header title={resolveTitle(location.pathname)} />
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
