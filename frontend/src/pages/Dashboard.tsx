import { useEffect, useState, useCallback } from 'react'
import { Clock, Wifi, RefreshCw } from 'lucide-react'
import { BarChart2, TrendingUp } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { IntelligenceSnapshot } from '../components/dashboard/IntelligenceSnapshot'
import { ThreatHeroPanel } from '../components/dashboard/ThreatHeroPanel'
import { SpeciesIntelStrip } from '../components/dashboard/SpeciesIntelStrip'
import { IntelligenceMapCanvas } from '../components/map/IntelligenceMapCanvas'
import { MapLayerControls, MapLayers } from '../components/map/MapLayerControls'
import { LiveIntelFeed } from '../components/dashboard/LiveIntelFeed'
import { CrossEvidencePanel } from '../components/dashboard/CrossEvidencePanel'
import { InvestigationPriorityQueue } from '../components/dashboard/InvestigationPriorityQueue'
import { NetworkPreviewPanel } from '../components/dashboard/NetworkPreviewPanel'
import { TimelinePreviewStrip } from '../components/dashboard/TimelinePreviewStrip'
import { InvestigationActions } from '../components/dashboard/InvestigationActions'
import { LoadingState } from '../components/ui/States'
import { apiClient } from '../services/apiClient'

const defaultLayers: MapLayers = {
  incidents: true,
  routes: true,
  environmental: true,
  behaviour: true,
  alerts: true,
}

// Static seizure trend data derived from the platform's mock incident dataset
const seizureTrendData = [
  { month: 'Jan', pangolin: 3, elephant: 2, rhino: 1, leopard: 0 },
  { month: 'Feb', pangolin: 4, elephant: 2, rhino: 1, leopard: 1 },
  { month: 'Mar', pangolin: 5, elephant: 3, rhino: 2, leopard: 1 },
  { month: 'Apr', pangolin: 4, elephant: 4, rhino: 1, leopard: 2 },
  { month: 'May', pangolin: 6, elephant: 3, rhino: 2, leopard: 1 },
  { month: 'Jun', pangolin: 7, elephant: 5, rhino: 3, leopard: 2 },
]

export default function Dashboard() {
  const [stats, setStats] = useState<Awaited<ReturnType<typeof apiClient.getOverviewStats>> | null>(null)
  const [priorityAlerts, setPriorityAlerts] = useState<Awaited<ReturnType<typeof apiClient.getPriorityAlerts>>>([])
  const [allAlerts, setAllAlerts] = useState<Awaited<ReturnType<typeof apiClient.getPriorityAlerts>>>([])
  const [layers, setLayers] = useState<MapLayers>(defaultLayers)
  const [speciesFilter, setSpeciesFilter] = useState<string | null>(null)
  const [now, setNow] = useState(() => new Date())
  const [loading, setLoading] = useState(true)

  const toggleLayer = useCallback((key: keyof MapLayers) => {
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }))
  }, [])

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 60_000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    Promise.all([
      apiClient.getOverviewStats(),
      apiClient.getPriorityAlerts(4),
      apiClient.getAlerts({ limit: 12 }),
    ]).then(([s, pa, aa]) => {
      setStats(s)
      setPriorityAlerts(pa)
      setAllAlerts(aa.alerts)
      setLoading(false)
    })
  }, [])

  const topThreat = priorityAlerts[0]

  const formatTime = (d: Date) =>
    d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
  const formatDate = (d: Date) =>
    d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' }).toUpperCase()

  return (
    <div className="min-h-full" style={{ background: '#EFF6F1' }}>
      <div className="mx-auto max-w-[1600px] space-y-4 p-5">

        {/* ── SECTION 1: Global Intelligence Header ── */}
        <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white px-5 py-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-baseline gap-3">
              <h1 className="font-display text-[28px] font-black tracking-tight text-slate-900">
                Silent Roar
              </h1>
              <span className="hidden font-ui text-[11px] font-bold uppercase tracking-[0.15em] text-emerald-600 sm:block">
                WILDLIFE INTELLIGENCE NETWORK
              </span>
            </div>
            <p className="mt-0.5 font-ui text-[13px] font-medium text-slate-500">India–Africa Intelligence Overview · Active Investigation Platform</p>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            {/* Date/time */}
            <div className="flex items-center gap-2 text-right">
              <Clock className="h-3.5 w-3.5 text-slate-400" />
              <div>
                <div className="font-mono-intel text-[12px] font-bold text-slate-700">{formatTime(now)}</div>
                <div className="font-mono-intel text-[10px] text-slate-400">{formatDate(now)}</div>
              </div>
            </div>

            {/* Live status */}
            <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              <div>
                <div className="font-mono-intel text-[10px] font-bold text-emerald-700">Intelligence stream active</div>
                <div className="font-mono-intel text-[9px] text-emerald-600 opacity-70">Last updated 2 min ago</div>
              </div>
            </div>

            {/* Data freshness */}
            <div className="flex items-center gap-1.5 text-slate-400">
              <Wifi className="h-3.5 w-3.5" />
              <span className="font-mono-intel text-[10px]">LIVE</span>
            </div>
          </div>
        </div>

        {/* ── SECTION 2: Intelligence Snapshot (compact indicators) ── */}
        {loading ? (
          <LoadingState label="Loading intelligence data..." />
        ) : (
          <IntelligenceSnapshot data={{
            totalAlerts: stats?.intelligenceAlerts,
            emergingHubs: stats?.emergingRoutes,
            totalIncidents: stats?.evidenceSignals,
            criticalAlerts: stats?.highRiskNetworks,
          }} />
        )}

        {/* ── SECTION 3: Hero Threat Panel ── */}
        <ThreatHeroPanel
          title={topThreat?.title ?? 'High-Risk Trafficking Corridor Detected'}
          corridor="Chennai → Mombasa Corridor"
          riskScore={topThreat?.riskScore ?? 81.6}
          confidence={topThreat ? Math.min(99, topThreat.riskScore + 2.1) : 83.7}
          signalCount={topThreat ? topThreat.linkedIncidents + 2 : 14}
          explanation="Multiple independent evidence streams converge on the same trafficking corridor. Trade data, route displacement, entity overlap, and linguistic signals all align."
          priority={topThreat?.severity === 'CRITICAL' ? 'CRITICAL' : 'HIGH'}
          investigationId={topThreat?.investigationId}
          evidenceStreams={[
            { label: 'TRADE',      value: 81, detail: '4 linked incidents',    icon: <BarChart2 className="h-3.5 w-3.5" /> },
            { label: 'ROUTE',      value: 86, detail: 'Rapid recent activity', icon: <TrendingUp className="h-3.5 w-3.5" /> },
            { label: 'LINGUISTIC', value: 72, detail: 'Coded terminology',     icon: <BarChart2 className="h-3.5 w-3.5" /> },
            { label: 'ANIMAL',     value: 64, detail: 'Behavioural anomaly',   icon: <TrendingUp className="h-3.5 w-3.5" /> },
          ]}
        />

        {/* ── SECTION 4: Species Intelligence Strip ── */}
        <SpeciesIntelStrip activeFilter={speciesFilter} onFilterChange={setSpeciesFilter} />

        {/* ── SECTION 5+6: Map + Live Intel Feed ── */}
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-5">
          {/* Map — 3/5 width */}
          <div className="xl:col-span-3">
            <div className="flex h-full flex-col rounded-2xl border border-slate-200 bg-white shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
                <span className="label-meta text-slate-500">INTELLIGENCE MAP</span>
                <div className="flex gap-1">
                  {(['ALL', 'INCIDENTS', 'ROUTES', 'ACTORS', 'SIGNALS'] as const).map((f) => (
                    <button
                      key={f}
                      className="focus-ring rounded-md px-2 py-1 text-[10px] font-semibold text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
                    >
                      {f}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex-1 p-3">
                <IntelligenceMapCanvas layers={layers} height={400} />
              </div>
              <div className="border-t border-slate-100 px-4 py-2.5">
                <MapLayerControls layers={layers} onToggle={toggleLayer} />
              </div>
            </div>
          </div>

          {/* Live Intel Feed — 2/5 width */}
          <div className="xl:col-span-2">
            <LiveIntelFeed alerts={allAlerts.slice(0, 10)} />
          </div>
        </div>

        {/* ── SECTIONS 7+8+9: Cross Evidence, Change Detection, Network Preview ── */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {/* Cross Evidence Panel */}
          <CrossEvidencePanel
            riskScore={topThreat?.riskScore ?? 81.6}
            crossAlignment={91}
            tradeScore={81}
            routeScore={86}
            entityScore={78}
            linguisticScore={72}
            animalScore={64}
          />

          {/* Change Detection — Seizure Trends as real chart */}
          <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-4 py-3">
              <span className="label-meta text-slate-500">WHAT CHANGED? — SEIZURE TRENDS</span>
            </div>
            <div className="p-4">
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <div className="font-display text-sm font-semibold text-slate-700">CHENNAI → MOMBASA</div>
                  <div className="mt-0.5 flex items-center gap-2 text-[11px] text-slate-500">
                    <span className="font-ui text-slate-400">Prev 30 days: 2 incidents</span>
                    <span className="font-ui font-semibold text-red-600">Current: 6 incidents +200%</span>
                  </div>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={160}>
                <AreaChart data={seizureTrendData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                  <defs>
                    <linearGradient id="pangolinGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#D97706" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#D97706" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="elephantGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#059669" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#059669" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #E2E8F0', background: '#FFF' }}
                    labelStyle={{ fontWeight: 600, color: '#334155' }}
                  />
                  <Area type="monotone" dataKey="pangolin" name="Pangolin" stroke="#D97706" fill="url(#pangolinGrad)" strokeWidth={2} dot={false} />
                  <Area type="monotone" dataKey="elephant" name="Elephant" stroke="#059669" fill="url(#elephantGrad)" strokeWidth={2} dot={false} />
                  <Area type="monotone" dataKey="rhino"    name="Rhino"    stroke="#7C3AED" fill="none" strokeWidth={1.5} strokeDasharray="4 2" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
              <div className="mt-2 flex flex-wrap gap-3">
                {[
                  { label: 'Pangolin', color: '#D97706' },
                  { label: 'Elephant', color: '#059669' },
                  { label: 'Rhino',    color: '#7C3AED' },
                ].map(({ label, color }) => (
                  <span key={label} className="flex items-center gap-1 text-[10px] text-slate-500">
                    <span className="h-1.5 w-3 rounded-full" style={{ backgroundColor: color }} />
                    {label}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Network Preview */}
          <NetworkPreviewPanel
            stats={{
              relatedIncidents:  12,
              recurringEntities:  3,
              sharedCorridors:    2,
              emergingNetworks:   1,
            }}
          />
        </div>

        {/* ── SECTIONS 10+11: Investigation Priority + Timeline ── */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <InvestigationPriorityQueue items={[
            {
              rank: 1, title: 'Chennai–Mombasa corridor',
              priority: 'IMMEDIATE', riskScore: 81.6, confidence: 83.7, evidenceStreams: 5,
              reason: 'Multiple converging evidence streams, rapid escalation',
              id: priorityAlerts[0]?.investigationId,
            },
            {
              rank: 2, title: 'Tuticorin–Maputo corridor',
              priority: 'IMMEDIATE', riskScore: 80.9, confidence: 79.2, evidenceStreams: 4,
              reason: 'Recurring actor overlap, route displacement detected',
            },
            {
              rank: 3, title: 'Mombasa hub network',
              priority: 'HIGH', riskScore: 78.0, confidence: 76.5, evidenceStreams: 4,
              reason: 'High shipment frequency, entity recurrence',
              id: priorityAlerts[1]?.investigationId,
            },
            {
              rank: 4, title: 'Selous–Entebbe ivory network',
              priority: 'HIGH', riskScore: 74.4, confidence: 71.8, evidenceStreams: 3,
              reason: 'Manifest overlap, route displacement',
              id: 'inv-03',
            },
          ]} />
          <TimelinePreviewStrip />
        </div>

        {/* ── SECTION 12: Investigation Actions ── */}
        <InvestigationActions />

      </div>
    </div>
  )
}
