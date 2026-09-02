import { useEffect, useMemo, useState } from 'react'
import { Investigation, GraphNode, GraphEdge, Entity } from '../types'
import { apiClient } from '../services/apiClient'
import { LoadingState } from '../components/ui/States'
import { NetworkGraph } from '../components/network/NetworkGraph'
import { EntityDrawer } from '../components/network/EntityDrawer'
import { buildInvestigationGraph } from '../utils/graph'
import { entityById } from '../data/entities'
import { cx } from '../utils/format'

/** Build a lightweight graph directly from backend investigation data */
function buildBackendGraph(inv: Investigation): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes: GraphNode[] = []
  const edges: GraphEdge[] = []
  const seen = new Set<string>()

  const addNode = (node: GraphNode) => {
    if (seen.has(node.id)) return
    seen.add(node.id)
    nodes.push(node)
  }

  // Central investigation node
  addNode({ id: `inv:${inv.id}`, label: inv.codename, type: 'INCIDENT', confidence: inv.riskScore })

  // Entities (actors)
  inv.entityIds.forEach((id) => {
    addNode({ id: `entity:${id}`, label: id.length > 14 ? id.slice(0, 14) + '…' : id, type: 'ACTOR' })
    edges.push({ id: `inv-ent-${id}`, source: `inv:${inv.id}`, target: `entity:${id}`, relation: 'INVOLVED_IN' })
  })

  // Routes
  inv.routeIds.forEach((id) => {
    addNode({ id: `route:${id}`, label: id.length > 14 ? id.slice(0, 14) + '…' : id, type: 'ROUTE' })
    edges.push({ id: `inv-rte-${id}`, source: `inv:${inv.id}`, target: `route:${id}`, relation: 'TRAVELLED_THROUGH' })
  })

  // Incidents (show up to 8)
  inv.incidentIds.slice(0, 8).forEach((id) => {
    addNode({ id: `incident:${id}`, label: id.length > 14 ? id.slice(0, 14) + '…' : id, type: 'INCIDENT' })
    edges.push({ id: `inv-inc-${id}`, source: `inv:${inv.id}`, target: `incident:${id}`, relation: 'LINKED_TO' })
  })

  // Radial layout by type ring
  const ringOrder: GraphNode['type'][] = ['ACTOR', 'INCIDENT', 'ROUTE', 'LOCATION', 'EVIDENCE']
  const byType: Record<string, GraphNode[]> = {}

  // Place the central node at the middle
  const centralNode = nodes.find((n) => n.id === `inv:${inv.id}`)
  if (centralNode) { centralNode.x = 50; centralNode.y = 50 }

  nodes.filter((n) => n.id !== `inv:${inv.id}`).forEach((n) => {
    byType[n.type] = byType[n.type] || []
    byType[n.type].push(n)
  })

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

export default function NetworkAnalysis() {
  const [investigations, setInvestigations] = useState<Investigation[] | null>(null)
  const [activeId, setActiveId] = useState<string | null>(null)
  const [activeInvestigation, setActiveInvestigation] = useState<Investigation | null>(null)
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null)
  const [isBackendMode, setIsBackendMode] = useState(false)

  useEffect(() => {
    apiClient.getInvestigations().then((data) => {
      setInvestigations(data)
      if (data.length > 0) {
        setActiveId(data[0].id)
        // Detect backend mode by checking if IDs look like backend UUIDs (e.g. RTE-...)
        setIsBackendMode(data[0].id !== 'inv-01' && data[0].id !== 'inv-02')
      }
    })
  }, [])

  useEffect(() => {
    if (activeId) {
      setActiveInvestigation(null)
      apiClient.getInvestigation(activeId).then((inv) => {
        setActiveInvestigation(inv ?? null)
      })
    }
  }, [activeId])

  const graph = useMemo(() => {
    if (!activeInvestigation) return null
    // Use the appropriate graph builder based on data source
    if (isBackendMode) return buildBackendGraph(activeInvestigation)
    return buildInvestigationGraph(activeInvestigation)
  }, [activeInvestigation, isBackendMode])

  if (!investigations) return <LoadingState />

  function handleNodeClick(node: GraphNode) {
    if (node.type === 'ACTOR') {
      const entId = node.id.replace('entity:', '')
      // Try local entity data first, then create a synthetic entity from backend data
      const entity = entityById(entId)
      if (entity) {
        setSelectedEntity(entity)
      } else if (isBackendMode) {
        // Synthetic entity from backend ID
        setSelectedEntity({
          id: entId,
          name: node.label,
          type: 'Possible Actor',
          confidence: node.confidence ?? 70,
          associatedIncidentIds: activeInvestigation?.incidentIds ?? [],
          locationIds: [],
          routeIds: activeInvestigation?.routeIds ?? [],
          signalCount: activeInvestigation?.incidentIds.length ?? 0,
          notes: `Actor identified from backend analysis. ID: ${entId}`,
        })
      }
    }
  }

  return (
    <div className="mx-auto max-w-[1400px] space-y-4 p-6">
      <div className="flex items-center justify-between">
        <div className="flex flex-wrap gap-2">
          {investigations.map((inv) => (
            <button
              key={inv.id}
              onClick={() => {
                setActiveId(inv.id)
                setSelectedEntity(null)
              }}
              className={cx(
                'focus-ring rounded-md border px-3.5 py-1.5 font-ui text-[12.5px] font-medium transition-colors',
                activeId === inv.id
                  ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-700'
                  : 'border-base-700 text-ink-400 hover:border-base-600 hover:text-ink-200'
              )}
            >
              {inv.codename}
            </button>
          ))}
        </div>
        {isBackendMode && (
          <span className="flex items-center gap-1.5 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-[11.5px] font-semibold text-emerald-700">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            LIVE DATA
          </span>
        )}
      </div>

      {!activeInvestigation && activeId && <LoadingState />}

      {activeInvestigation && !graph && <LoadingState />}

      {graph && graph.nodes.length > 0 && (
        <NetworkGraph
          nodes={graph.nodes}
          edges={graph.edges}
          onNodeClick={handleNodeClick}
          selectedNodeId={selectedEntity ? `entity:${selectedEntity.id}` : null}
          height={600}
        />
      )}

      {graph && graph.nodes.length === 0 && (
        <div className="flex h-64 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-[14px] text-slate-400">
          No network data available for this investigation.
        </div>
      )}

      {selectedEntity && <EntityDrawer entity={selectedEntity} onClose={() => setSelectedEntity(null)} />}
    </div>
  )
}
