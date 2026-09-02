import { useEffect, useMemo, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ChevronLeft, Clock, MapPin } from 'lucide-react'
import { apiClient } from '../services/apiClient'
import { Investigation, GraphNode, GraphEdge, Entity } from '../types'
import { LoadingState, ErrorState } from '../components/ui/States'
import { Badge } from '../components/ui/Badge'
import { RiskDial } from '../components/ui/RiskIndicators'
import { ExplainableAIPanel } from '../components/dashboard/ExplainableAIPanel'
import { FindHiddenLinksButton } from '../components/network/FindHiddenLinksButton'
import { NetworkGraph } from '../components/network/NetworkGraph'
import { EntityDrawer } from '../components/network/EntityDrawer'
import { InvestigationTimeline } from '../components/timeline/InvestigationTimeline'
import { EvidenceCard } from '../components/evidence/EvidenceCard'
import { buildInvestigationGraph } from '../utils/graph'
import { incidentById } from '../data/incidents'
import { entityById } from '../data/entities'
import { evidenceById } from '../data/evidence'
import { locationById } from '../data/locations'
import { cx } from '../utils/format'

/** Build a radial graph from backend investigation data (no local data lookups) */
function buildBackendGraph(inv: Investigation): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes: GraphNode[] = []
  const edges: GraphEdge[] = []
  const seen = new Set<string>()
  const addNode = (node: GraphNode) => { if (!seen.has(node.id)) { seen.add(node.id); nodes.push(node) } }

  addNode({ id: `inv:${inv.id}`, label: inv.codename, type: 'INCIDENT', confidence: inv.riskScore })
  inv.entityIds.forEach((id) => {
    addNode({ id: `entity:${id}`, label: id.length > 14 ? id.slice(0, 14) + '…' : id, type: 'ACTOR' })
    edges.push({ id: `inv-ent-${id}`, source: `inv:${inv.id}`, target: `entity:${id}`, relation: 'INVOLVED_IN' })
  })
  inv.routeIds.forEach((id) => {
    addNode({ id: `route:${id}`, label: id.length > 14 ? id.slice(0, 14) + '…' : id, type: 'ROUTE' })
    edges.push({ id: `inv-rte-${id}`, source: `inv:${inv.id}`, target: `route:${id}`, relation: 'TRAVELLED_THROUGH' })
  })
  inv.incidentIds.slice(0, 8).forEach((id) => {
    addNode({ id: `incident:${id}`, label: id.length > 14 ? id.slice(0, 14) + '…' : id, type: 'INCIDENT' })
    edges.push({ id: `inv-inc-${id}`, source: `inv:${inv.id}`, target: `incident:${id}`, relation: 'LINKED_TO' })
  })

  const centralNode = nodes.find((n) => n.id === `inv:${inv.id}`)
  if (centralNode) { centralNode.x = 50; centralNode.y = 50 }

  const byType: Record<string, GraphNode[]> = {}
  nodes.filter((n) => n.id !== `inv:${inv.id}`).forEach((n) => {
    byType[n.type] = byType[n.type] || []
    byType[n.type].push(n)
  })
  const ringOrder: GraphNode['type'][] = ['ACTOR', 'INCIDENT', 'ROUTE', 'LOCATION', 'EVIDENCE']
  ringOrder.forEach((type, ringIdx) => {
    const group = byType[type] || []
    const radius = 18 + ringIdx * 14
    group.forEach((n, i) => {
      const angle = (i / Math.max(group.length, 1)) * Math.PI * 2 + ringIdx * 0.5
      n.x = 50 + radius * Math.cos(angle)
      n.y = 50 + radius * Math.sin(angle) * 0.8
    })
  })
  return { nodes, edges }
}

/** Decide which graph builder to use — mock data builder if IDs are local, backend builder otherwise */
function buildGraph(inv: Investigation): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const isMockId = inv.id === 'inv-01' || inv.id === 'inv-02' || inv.id === 'inv-03'
  if (isMockId) return buildInvestigationGraph(inv)
  // For backend investigations, use backend builder so empty arrays produce meaningful node
  const backendGraph = buildBackendGraph(inv)
  if (backendGraph.nodes.length > 0) return backendGraph
  // Fallback to mock builder (handles local data IDs)
  return buildInvestigationGraph(inv)
}

type TabKey = 'overview' | 'timeline' | 'network' | 'evidence' | 'locations' | 'brief'

const tabs: { key: TabKey; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'timeline', label: 'Timeline' },
  { key: 'network', label: 'Network' },
  { key: 'evidence', label: 'Evidence' },
  { key: 'locations', label: 'Locations' },
  { key: 'brief', label: 'Intelligence Brief' },
]

export default function InvestigationDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [investigation, setInvestigation] = useState<Investigation | null | undefined>(undefined)
  const [tab, setTab] = useState<TabKey>('overview')
  const [showNetworkResult, setShowNetworkResult] = useState(false)
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null)
  const [boosted, setBoosted] = useState(false)

  useEffect(() => {
    if (!id) return
    apiClient.getInvestigation(id).then(setInvestigation)
    const flag = sessionStorage.getItem(`boosted:${id}`)
    if (flag === 'true') {
      setBoosted(true)
      sessionStorage.removeItem(`boosted:${id}`)
    }
  }, [id])

  const graph = useMemo(() => (investigation ? buildGraph(investigation) : null), [investigation])

  if (investigation === undefined) return <LoadingState />
  if (investigation === null) return <ErrorState title="Investigation not found" description="This investigation record could not be located." />

  const displayRisk = boosted ? investigation.riskScore : investigation.previousRiskScore ?? investigation.riskScore

  function handleNodeClick(node: GraphNode) {
    if (node.type === 'ACTOR') {
      const entId = node.id.replace('entity:', '')
      const entity = entityById(entId)
      if (entity) {
        setSelectedEntity(entity)
      } else {
        // Synthetic entity from backend ID
        setSelectedEntity({
          id: entId,
          name: node.label,
          type: 'Possible Actor',
          confidence: node.confidence ?? 70,
          associatedIncidentIds: investigation?.incidentIds ?? [],
          locationIds: [],
          routeIds: investigation?.routeIds ?? [],
          signalCount: investigation?.incidentIds.length ?? 0,
          notes: `Actor identified from backend analysis. ID: ${entId}`,
        })
      }
    }
  }

  return (
    <div className="mx-auto max-w-[1400px] space-y-5 p-6">
      <button
        onClick={() => navigate('/investigations')}
        className="focus-ring flex items-center gap-1 text-micro font-semibold text-ink-500 hover:text-ink-300"
      >
        <ChevronLeft className="h-3.5 w-3.5" />
        ALL INVESTIGATIONS
      </button>

      <div className="panel flex flex-col gap-5 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <RiskDial score={boosted ? investigation.riskScore : displayRisk} size={72} />
          <div>
            <div className="flex items-center gap-2">
              <Badge tone="emerald">{investigation.status.replace('_', ' ')}</Badge>
              <span className="flex items-center gap-1 font-ui text-micro text-ink-500">
                <Clock className="h-3 w-3" />
                Updated {investigation.lastUpdated}
              </span>
            </div>
            <h1 className="mt-1.5 font-display text-2xl font-bold text-ink-100">{investigation.codename}</h1>
            {investigation.previousRiskScore && (
              <div className="mt-1 flex items-center gap-1.5 text-[14px] text-ink-500">
                Risk score:
                <span className={cx('font-semibold transition-colors', boosted ? 'text-crimson-600' : 'text-ink-300')}>
                  {investigation.previousRiskScore} → {boosted ? investigation.riskScore : investigation.previousRiskScore}
                </span>
                {boosted && <span className="text-micro font-semibold text-emerald-600">NEW SIGNAL ADDED</span>}
              </div>
            )}
          </div>
        </div>
        <div className="flex gap-4 text-center text-[14px] sm:gap-6">
          <MiniMetric label="Incidents" value={investigation.incidentIds.length} />
          <MiniMetric label="Entities" value={investigation.entityIds.length} />
          <MiniMetric label="Evidence" value={investigation.evidenceIds.length} />
          <MiniMetric label="Routes" value={investigation.routeIds.length} />
        </div>
      </div>

      <div className="flex gap-1 overflow-x-auto border-b border-base-700">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cx(
              'focus-ring shrink-0 whitespace-nowrap border-b-2 px-3.5 py-2.5 text-[15px] font-medium transition-colors',
              tab === t.key ? 'border-emerald-400 text-emerald-700' : 'border-transparent text-ink-500 hover:text-ink-300'
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-5">
          <div className="space-y-5 lg:col-span-3">
            <div className="panel p-5">
              <h2 className="font-heading label-meta mb-2">Threat Summary</h2>
              <p className="text-[16px] leading-relaxed text-ink-200">{investigation.threatSummary}</p>
              <div className="mt-4 grid grid-cols-2 gap-3 text-[12.5px] sm:grid-cols-3">
                <InfoField label="Primary Commodity" value={investigation.primaryCommodity} />
                <InfoField label="Origin" value={investigation.originCountry} />
                <InfoField label="Status" value={investigation.status} />
              </div>
            </div>

            <div className="panel p-5">
              <h2 className="font-heading label-meta mb-3">Find Hidden Links</h2>
              <p className="mb-4 text-[12.5px] text-ink-500">
                Run correlation analysis across incidents, entities, routes, and evidence linked to this investigation.
              </p>
              <FindHiddenLinksButton
                investigationId={investigation.id}
                onComplete={() => {
                  setShowNetworkResult(true)
                  setTab('network')
                }}
              />
            </div>
          </div>

          <div className="lg:col-span-2">
            <ExplainableAIPanel riskScore={investigation.riskScore} factors={investigation.riskFactors} />
          </div>
        </div>
      )}

      {tab === 'timeline' && (
        <div className="panel p-5">
          <InvestigationTimeline events={investigation.timeline} />
        </div>
      )}

      {tab === 'network' && (
        <div className="space-y-3">
          {showNetworkResult && graph && graph.nodes.length > 0 && (
            <div className="animate-fadeUp rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-[12.5px] text-emerald-700">
              Network graph revealed from correlation analysis. Click a red actor node to review a possible entity match.
            </div>
          )}
          {graph && graph.nodes.length > 0 ? (
            <NetworkGraph
              nodes={graph.nodes}
              edges={graph.edges}
              onNodeClick={handleNodeClick}
              selectedNodeId={selectedEntity ? `entity:${selectedEntity.id}` : null}
              height={520}
            />
          ) : (
            <div className="flex h-64 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-[14px] text-slate-400">
              No network data available. Run "Find Hidden Links" from the Overview tab first.
            </div>
          )}
        </div>
      )}

      {tab === 'evidence' && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {investigation.evidenceIds.map((eid) => {
            const item = evidenceById(eid)
            return item ? <EvidenceCard key={eid} item={item} /> : null
          })}
        </div>
      )}

      {tab === 'locations' && (
        <div className="space-y-3">
          {[...new Set(investigation.incidentIds.map((iid) => incidentById(iid)?.locationId).filter(Boolean))].map((locId) => {
            const loc = locationById(locId as string)
            if (!loc) return null
            const relatedIncidents = investigation.incidentIds.filter((iid) => incidentById(iid)?.locationId === loc.id)
            return (
              <button
                key={loc.id}
                onClick={() => navigate(`/map?location=${loc.id}`)}
                className="focus-ring panel flex w-full items-center justify-between p-4 text-left hover:border-emerald-500/30"
              >
                <div className="flex items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-md bg-cyan-500/10 text-cyan-600">
                    <MapPin className="h-4 w-4" />
                  </span>
                  <div>
                    <div className="text-[13.5px] font-semibold text-ink-100">{loc.name}</div>
                    <div className="text-[14px] text-ink-500">{loc.country} · {loc.kind}</div>
                  </div>
                </div>
                <span className="text-[14px] text-ink-500">{relatedIncidents.length} linked incident{relatedIncidents.length === 1 ? '' : 's'}</span>
              </button>
            )
          })}
        </div>
      )}

      {tab === 'brief' && (
        <div className="panel flex flex-col items-center gap-3 p-10 text-center">
          <p className="text-[15px] text-ink-400">
            Generate a full intelligence brief for this investigation, including AI assessment and investigative priorities.
          </p>
          <button
            onClick={() => navigate('/reports')}
            className="focus-ring rounded-md bg-emerald-500 px-5 py-2.5 text-[15px] font-bold text-base-950 hover:bg-emerald-400"
          >
            Go to Reports
          </button>
        </div>
      )}

      {selectedEntity && <EntityDrawer entity={selectedEntity} onClose={() => setSelectedEntity(null)} />}
    </div>
  )
}

function MiniMetric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="font-display text-xl font-bold text-ink-100">{value}</div>
      <div className="font-ui text-[13px] text-ink-500">{label}</div>
    </div>
  )
}

function InfoField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-micro text-ink-500">{label}</div>
      <div className="mt-0.5 text-ink-200">{value}</div>
    </div>
  )
}
