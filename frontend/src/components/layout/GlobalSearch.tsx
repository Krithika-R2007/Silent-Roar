import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, MapPin, Users, Waypoints, FileWarning } from 'lucide-react'
import { apiClient } from '../../services/apiClient'
import { cx } from '../../utils/format'

interface SearchResults {
  incidents: { id: string; title: string; species: string; riskScore: number }[]
  entities: { id: string; name: string; type: string; confidence: number }[]
  locations: { id: string; name: string; country: string }[]
  routes: { id: string; name: string; activityLevel: number }[]
}

export function GlobalSearch() {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [results, setResults] = useState<SearchResults | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  useEffect(() => {
    if (!query.trim()) {
      setResults(null)
      return
    }
    let active = true
    apiClient.search(query).then((r) => {
      if (active) setResults(r as SearchResults)
    })
    return () => { active = false }
  }, [query])

  const hasResults =
    results && (results.incidents.length || results.entities.length || results.locations.length || results.routes.length)

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
      <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-white px-3 py-2 shadow-sm focus-within:border-emerald-400 focus-within:ring-2 focus-within:ring-emerald-500/20">
        <Search className="h-4 w-4 shrink-0 text-emerald-500" />
        <input
          value={query}
          onChange={(e) => { setQuery(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)}
          placeholder="Search incidents, actors, routes, locations…"
          className="w-full bg-transparent text-[14px] text-slate-700 placeholder:text-slate-400 focus:outline-none"
        />
        {query && (
          <button onClick={() => { setQuery(''); setResults(null) }} className="text-slate-300 hover:text-slate-500 text-[12px]">✕</button>
        )}
      </div>

      {open && query.trim() && (
        <div className="absolute left-0 right-0 top-[calc(100%+6px)] z-50 max-h-96 overflow-y-auto rounded-2xl border border-slate-200 bg-white shadow-xl">
          {!hasResults && (
            <div className="px-4 py-6 text-center text-[13px] text-slate-400">No matches for "{query}"</div>
          )}

          {results && results.incidents.length > 0 && (
            <ResultGroup label="Incidents" icon={<FileWarning className="h-3.5 w-3.5" />}>
              {results.incidents.slice(0, 4).map((item) => (
                <ResultRow
                  key={String(item.id)}
                  primary={item.title}
                  secondary={item.species}
                  onClick={() => { navigate('/evidence'); setOpen(false) }}
                />
              ))}
            </ResultGroup>
          )}

          {results && results.entities.length > 0 && (
            <ResultGroup label="Entities" icon={<Users className="h-3.5 w-3.5" />}>
              {results.entities.slice(0, 4).map((item) => (
                <ResultRow
                  key={String(item.id)}
                  primary={String(item.name)}
                  secondary={`${item.type} · ${item.confidence}% confidence`}
                  onClick={() => { navigate('/network'); setOpen(false) }}
                />
              ))}
            </ResultGroup>
          )}

          {results && results.locations.length > 0 && (
            <ResultGroup label="Locations" icon={<MapPin className="h-3.5 w-3.5" />}>
              {results.locations.slice(0, 4).map((item) => (
                <ResultRow
                  key={String(item.id)}
                  primary={String(item.name)}
                  secondary={String(item.country)}
                  onClick={() => { navigate('/map'); setOpen(false) }}
                />
              ))}
            </ResultGroup>
          )}

          {results && results.routes.length > 0 && (
            <ResultGroup label="Routes" icon={<Waypoints className="h-3.5 w-3.5" />}>
              {results.routes.slice(0, 4).map((item) => (
                <ResultRow
                  key={String(item.id)}
                  primary={String(item.name)}
                  secondary={`Activity ${item.activityLevel}`}
                  onClick={() => { navigate('/map'); setOpen(false) }}
                />
              ))}
            </ResultGroup>
          )}
        </div>
      )}
    </div>
  )
}

function ResultGroup({ label, icon, children }: { label: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="border-b border-slate-100 py-1 last:border-b-0">
      <div className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-emerald-600">
        {icon}
        {label}
      </div>
      {children}
    </div>
  )
}

function ResultRow({ primary, secondary, onClick }: { primary: string; secondary: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={cx('flex w-full flex-col items-start px-3 py-2 text-left transition-colors hover:bg-slate-50')}
    >
      <span className="text-[13px] font-medium text-slate-700">{primary}</span>
      <span className="text-[11px] text-slate-400">{secondary}</span>
    </button>
  )
}
