/**
 * apiClient.ts
 * ------------
 * Unified client used by all pages.
 *
 * On first call it probes the backend. If reachable → uses real API.
 * If not reachable → falls back to mock data seamlessly.
 *
 * Usage:
 *   import { apiClient } from './apiClient'
 *   const stats = await apiClient.getOverviewStats()
 */

import * as realApi from './api'
import { mockApi } from './mockApi'

// ── Backend availability state ────────────────────────────────────────────────

let _backendAvailable: boolean | null = null  // null = not probed yet
let _probePromise: Promise<boolean> | null = null

async function isBackendAvailable(): Promise<boolean> {
  if (_backendAvailable !== null) return _backendAvailable
  if (_probePromise) return _probePromise
  _probePromise = realApi.probeBackend().then((ok) => {
    _backendAvailable = ok
    if (ok) {
      console.info('[Silent Roar] Backend connected — using live data')
    } else {
      console.warn('[Silent Roar] Backend unreachable — using mock data')
    }
    return ok
  })
  return _probePromise
}

// Force re-probe (useful for a "Reconnect" button)
export function resetBackendProbe() {
  _backendAvailable = null
  _probePromise = null
}

export function getBackendStatus() {
  return _backendAvailable
}

// ── Unified client ────────────────────────────────────────────────────────────

export const apiClient = {
  // ── Stats / Dashboard ─────────────────────────────────────────────────────

  async getOverviewStats() {
    if (await isBackendAvailable()) {
      const d = await realApi.getDashboardSummary()
      return {
        activeInvestigations: d.active_investigations,
        highRiskNetworks: d.high_risk_routes,
        emergingRoutes: d.emerging_hubs,
        intelligenceAlerts: d.total_alerts,
        evidenceSignals: d.total_incidents,
      }
    }
    return mockApi.getOverviewStats()
  },

  // ── Alerts ────────────────────────────────────────────────────────────────

  async getAlerts(params?: { priority?: string; limit?: number; offset?: number }) {
    if (await isBackendAvailable()) {
      const res = await realApi.getAlerts(params)
      const mapped = res.alerts.map((a) => ({
        id: a.alert_id,
        title: a.title,
        severity: mapPriority(a.priority),
        status: 'NEW' as const,
        time: a.first_detected ?? 'Recently',
        description: a.explanation ?? 'No explanation provided.',
        riskScore: a.risk_score ?? 50,
        evidenceCount: 1,
        linkedIncidents: extractIncidentCount(a.explanation),
        investigationId: a.entity_id ?? undefined,
        locationId: undefined,
      }))
      return { total: res.total, alerts: mapped }
    }
    const all = await mockApi.getAlerts()
    return { total: all.length, alerts: all }
  },

  async getPriorityAlerts(limit = 4) {
    if (await isBackendAvailable()) {
      const res = await realApi.getAlerts({ priority: 'CRITICAL', limit })
      if (res.alerts.length < limit) {
        const high = await realApi.getAlerts({ priority: 'HIGH', limit: limit - res.alerts.length })
        res.alerts.push(...high.alerts)
      }
      return res.alerts.map((a) => ({
        id: a.alert_id,
        title: a.title,
        severity: mapPriority(a.priority),
        status: 'NEW' as const,
        time: a.first_detected ?? 'Recently',
        description: a.explanation ?? 'No explanation provided.',
        riskScore: a.risk_score ?? 50,
        evidenceCount: 1,
        linkedIncidents: extractIncidentCount(a.explanation),
        investigationId: a.entity_id ?? undefined,
        locationId: undefined,
      }))
    }
    const all = await mockApi.getAlerts()
    return all
      .filter((a) => a.status === 'NEW')
      .sort((a, b) => b.riskScore - a.riskScore)
      .slice(0, limit)
  },

  // ── Incidents ─────────────────────────────────────────────────────────────

  async getIncidents(params?: { search?: string; species?: string; limit?: number; offset?: number }) {
    if (await isBackendAvailable()) {
      return realApi.getIncidents(params)
    }
    const all = await mockApi.getIncidents()
    return { total: all.length, incidents: all }
  },

  async getIncident(id: string) {
    if (await isBackendAvailable()) {
      return realApi.getIncidentDetail(id)
    }
    return mockApi.getIncident(id)
  },

  // ── Actors / Network ──────────────────────────────────────────────────────

  async getActors(params?: { name?: string; limit?: number; offset?: number }) {
    if (await isBackendAvailable()) {
      return realApi.getActors(params)
    }
    const all = await mockApi.getEntities()
    return { total: all.length, actors: all }
  },

  async getActor(id: string) {
    if (await isBackendAvailable()) {
      return realApi.getActor(id)
    }
    return mockApi.getEntity(id)
  },

  async getNetwork(targetType: string, targetId: string) {
    if (await isBackendAvailable()) {
      return realApi.getNetwork(targetType, targetId)
    }
    return null
  },

  async getHiddenLinks(targetType: string, targetId: string) {
    if (await isBackendAvailable()) {
      return realApi.getHiddenLinks(targetType, targetId)
    }
    // mock fallback for investigation detail
    return mockApi.findHiddenLinks(targetId)
  },

  // ── Routes ────────────────────────────────────────────────────────────────

  async getRoutes(params?: { limit?: number; offset?: number }) {
    if (await isBackendAvailable()) {
      return realApi.getRoutes(params)
    }
    const all = await mockApi.getRoutes()
    return { total: all.length, routes: all }
  },

  async getRoute(id: string) {
    if (await isBackendAvailable()) {
      return realApi.getRoute(id)
    }
    return mockApi.getRoute(id)
  },

  // ── Map ───────────────────────────────────────────────────────────────────

  async getMapData() {
    if (await isBackendAvailable()) {
      return realApi.getMapData()
    }
    return null
  },

  // ── Search ────────────────────────────────────────────────────────────────

  async search(query: string) {
    if (await isBackendAvailable()) {
      const res = await realApi.searchApi(query)
      // Normalise backend response to match the shape mockApi returns
      return {
        incidents: res.incidents.map((i) => ({
          id: i.incident_id,
          title: `${i.species ?? ''} - ${i.source_location ?? ''}`,
          species: i.species ?? '',
          riskScore: 0,
        })),
        entities: res.actors.map((a) => ({
          id: a.actor_id,
          name: a.full_name ?? String(a.actor_id),
          type: a.role ?? 'ACTOR',
          confidence: 80,
        })),
        locations: res.locations.map((name) => ({ id: name, name, country: '' })),
        routes: res.routes.map((r) => ({
          id: r.route_id,
          name: `${r.source ?? ''} → ${r.destination ?? ''}`,
          activityLevel: 50,
        })),
      }
    }
    return mockApi.search(query)
  },

  // ── Intelligence ──────────────────────────────────────────────────────────

  async getIntelligence(targetType: string, targetId: string) {
    if (await isBackendAvailable()) {
      return realApi.getIntelligence(targetType, targetId)
    }
    return null
  },

  async getInvestigationBrief(targetType: string, targetId: string) {
    if (await isBackendAvailable()) {
      return realApi.getInvestigationBrief(targetType, targetId)
    }
    return mockApi.generateBrief(targetId)
  },

  // ── Messages ──────────────────────────────────────────────────────────────

  async getMessages(channelId?: string) {
    if (await isBackendAvailable()) {
      return realApi.getMessages(channelId) as any
    }
    return mockApi.getMessages(channelId)
  },

  async getChannels() {
    if (await isBackendAvailable()) {
      return realApi.getChannels() as any
    }
    return mockApi.getChannels()
  },

  async analyzeMessage(sender: string, receiver: string, message: string) {
    if (await isBackendAvailable()) {
      return realApi.analyzeMessage(sender, receiver, message)
    }
    return null
  },

  // ── Investigations (real data when backend is up) ──────────────────────────

  async getInvestigations() {
    if (await isBackendAvailable()) {
      const raw = await realApi.getInvestigationsList() as any[]
      return raw.map(normalizeInvestigation)
    }
    return mockApi.getInvestigations()
  },

  async getInvestigation(id: string) {
    if (await isBackendAvailable()) {
      const raw = await realApi.getInvestigationFull(id) as any
      return normalizeInvestigation(raw)
    }
    return mockApi.getInvestigation(id)
  },

  // ── Reports & Evidence (mock) ─────────────────────────────────────────────

  async getReports() {
    return mockApi.getReports()
  },

  async getEvidence() {
    return mockApi.getEvidence()
  },

  async getEvidenceItem(id: string) {
    return mockApi.getEvidenceItem(id)
  },
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Map backend priority strings to frontend Severity type */
function mapPriority(priority: string | null): 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'WATCH' {
  switch ((priority ?? '').toUpperCase()) {
    case 'IMMEDIATE':
    case 'CRITICAL': return 'CRITICAL'
    case 'HIGH':     return 'HIGH'
    case 'MEDIUM':   return 'MEDIUM'
    default:         return 'WATCH'
  }
}

/**
 * Pull incident count out of the backend explanation text.
 * e.g. "Temporal trafficking cluster: 16 incidents within 30 days..."
 * returns 16. Falls back to 1.
 */
function extractIncidentCount(explanation: string | null): number {
  if (!explanation) return 1
  const m = explanation.match(/:\s*(\d+)\s+incidents?\b/i)
  return m ? parseInt(m[1], 10) : 1
}

/**
 * Normalise the raw backend investigation object (from /api/investigation/all
 * or /api/investigation/details/:id) into the Investigation shape the UI expects.
 */
function normalizeInvestigation(raw: any) {
  return {
    id: raw.id ?? raw.target_id ?? '',
    codename: raw.codename ?? raw.case_title ?? raw.title ?? `Investigation ${raw.id}`,
    riskScore: Number(raw.riskScore ?? raw.risk_score ?? 50),
    previousRiskScore: undefined,
    status: (raw.status ?? 'ACTIVE') as 'ACTIVE' | 'MONITORING' | 'CLOSED',
    lastUpdated: raw.lastUpdated ?? 'Recently',
    threatSummary: raw.threatSummary ?? raw.explanation ?? raw.summary ?? '',
    primaryCommodity: raw.primaryCommodity ?? raw.primary_commodity ?? 'Various',
    originCountry: raw.originCountry ?? raw.origin_country ?? 'Multiple',
    // incidentIds / entityIds come back as real arrays from the backend
    incidentIds: Array.isArray(raw.incidentIds) ? raw.incidentIds : [],
    entityIds: Array.isArray(raw.entityIds) ? raw.entityIds : [],
    evidenceIds: Array.isArray(raw.evidenceIds) ? raw.evidenceIds : [],
    routeIds: Array.isArray(raw.routeIds) ? raw.routeIds : [],
    // The backend doesn't return these — provide safe defaults
    timeline: Array.isArray(raw.timeline) ? raw.timeline : [],
    riskFactors: Array.isArray(raw.riskFactors) ? raw.riskFactors : [],
  }
}
