import { GraphEdge, GraphNode, Investigation } from '../types'
import { incidentById } from '../data/incidents'
import { entityById } from '../data/entities'
import { locationById } from '../data/locations'
import { routeById } from '../data/routes'
import { evidenceById } from '../data/evidence'

export function buildInvestigationGraph(investigation: Investigation): {
  nodes: GraphNode[]
  edges: GraphEdge[]
} {
  const nodes: GraphNode[] = []
  const edges: GraphEdge[] = []
  const seen = new Set<string>()

  const addNode = (node: GraphNode) => {
    if (seen.has(node.id)) return
    seen.add(node.id)
    nodes.push(node)
  }

  investigation.entityIds.forEach((id) => {
    const e = entityById(id)
    if (!e) return
    addNode({ id: `entity:${e.id}`, label: e.name, type: 'ACTOR', confidence: e.confidence })
  })

  investigation.incidentIds.forEach((id) => {
    const inc = incidentById(id)
    if (!inc) return
    addNode({ id: `incident:${inc.id}`, label: inc.title, type: 'INCIDENT' })

    inc.entityIds.forEach((eid) => {
      if (seen.has(`entity:${eid}`)) {
        edges.push({ id: `${eid}-${inc.id}`, source: `entity:${eid}`, target: `incident:${inc.id}`, relation: 'INVOLVED_IN' })
      }
    })

    const loc = locationById(inc.locationId)
    if (loc) {
      addNode({ id: `location:${loc.id}`, label: loc.name, type: 'LOCATION' })
      edges.push({ id: `${inc.id}-${loc.id}`, source: `incident:${inc.id}`, target: `location:${loc.id}`, relation: 'OCCURRED_AT' })
    }
  })

  investigation.routeIds.forEach((id) => {
    const r = routeById(id)
    if (!r) return
    addNode({ id: `route:${r.id}`, label: r.name, type: 'ROUTE' })
    if (seen.has(`location:${r.fromLocationId}`)) {
      edges.push({ id: `${r.id}-from`, source: `location:${r.fromLocationId}`, target: `route:${r.id}`, relation: 'TRAVELLED_THROUGH' })
    }
    if (seen.has(`location:${r.toLocationId}`)) {
      edges.push({ id: `${r.id}-to`, source: `route:${r.id}`, target: `location:${r.toLocationId}`, relation: 'TRAVELLED_THROUGH' })
    }
    r.incidentIds.forEach((iid) => {
      if (seen.has(`incident:${iid}`)) {
        edges.push({ id: `${r.id}-${iid}`, source: `incident:${iid}`, target: `route:${r.id}`, relation: 'LINKED_TO' })
      }
    })
  })

  investigation.evidenceIds.forEach((id) => {
    const ev = evidenceById(id)
    if (!ev) return
    addNode({ id: `evidence:${ev.id}`, label: ev.title, type: 'EVIDENCE' })
    ev.relatedIncidentIds.forEach((iid) => {
      if (seen.has(`incident:${iid}`)) {
        edges.push({ id: `${ev.id}-${iid}`, source: `evidence:${ev.id}`, target: `incident:${iid}`, relation: 'LINKED_TO' })
      }
    })
  })

  // simple radial layout by type ring
  const ringOrder: GraphNode['type'][] = ['ACTOR', 'INCIDENT', 'ROUTE', 'LOCATION', 'EVIDENCE']
  const byType: Record<string, GraphNode[]> = {}
  nodes.forEach((n) => {
    byType[n.type] = byType[n.type] || []
    byType[n.type].push(n)
  })

  const cx = 50
  const cy = 50
  ringOrder.forEach((type, ringIdx) => {
    const group = byType[type] || []
    const radius = 14 + ringIdx * 17
    group.forEach((n, i) => {
      const angle = (i / Math.max(group.length, 1)) * Math.PI * 2 + ringIdx * 0.4
      n.x = cx + radius * Math.cos(angle)
      n.y = cy + radius * Math.sin(angle) * 0.82
    })
  })

  return { nodes, edges }
}
