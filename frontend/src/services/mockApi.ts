import { incidents, incidentById } from '../data/incidents'
import { entities, entityById } from '../data/entities'
import { locations, locationById } from '../data/locations'
import { routes, routeById } from '../data/routes'
import { evidence, evidenceById } from '../data/evidence'
import { alerts, alertById } from '../data/alerts'
import { channels, messages, messagesByChannel } from '../data/messages'
import { investigations, investigationById } from '../data/investigations'
import { reports } from '../data/reports'

// This module simulates a backend API surface over local mock data so the
// UI layer can later be pointed at a real service with minimal changes.
// Every exported function returns a Promise, matching a real fetch client.

const delay = (ms = 220) => new Promise((resolve) => setTimeout(resolve, ms))

export const mockApi = {
  async getOverviewStats() {
    await delay(150)
    return {
      activeInvestigations: investigations.filter((i) => i.status === 'ACTIVE').length + 21,
      highRiskNetworks: 7,
      emergingRoutes: routes.filter((r) => r.activityLevel > 55).length + 5,
      intelligenceAlerts: alerts.length + 6,
      evidenceSignals: 143,
    }
  },

  async getAlerts() {
    await delay()
    return alerts
  },

  async getAlert(id: string) {
    await delay(120)
    return alertById(id) ?? null
  },

  async getIncidents() {
    await delay()
    return incidents
  },

  async getIncident(id: string) {
    await delay(120)
    return incidentById(id) ?? null
  },

  async getEntities() {
    await delay()
    return entities
  },

  async getEntity(id: string) {
    await delay(120)
    return entityById(id) ?? null
  },

  async getLocations() {
    await delay(100)
    return locations
  },

  async getLocation(id: string) {
    await delay(80)
    return locationById(id) ?? null
  },

  async getRoutes() {
    await delay(100)
    return routes
  },

  async getRoute(id: string) {
    await delay(80)
    return routeById(id) ?? null
  },

  async getEvidence() {
    await delay()
    return evidence
  },

  async getEvidenceItem(id: string) {
    await delay(100)
    return evidenceById(id) ?? null
  },

  async getInvestigations() {
    await delay()
    return investigations
  },

  async getInvestigation(id: string) {
    await delay(150)
    return investigationById(id) ?? null
  },

  async getChannels() {
    await delay(120)
    return channels
  },

  async getMessages(channelId?: string) {
    await delay(150)
    return channelId ? messagesByChannel(channelId) : messages
  },

  async getReports() {
    await delay(150)
    return reports
  },

  async search(query: string) {
    await delay(180)
    const q = query.trim().toLowerCase()
    if (!q) return { incidents: [], entities: [], locations: [], routes: [] }
    return {
      incidents: incidents.filter((i) => i.title.toLowerCase().includes(q) || i.species.toLowerCase().includes(q)),
      entities: entities.filter((e) => e.name.toLowerCase().includes(q)),
      locations: locations.filter((l) => l.name.toLowerCase().includes(q) || l.country.toLowerCase().includes(q)),
      routes: routes.filter((r) => r.name.toLowerCase().includes(q)),
    }
  },

  // Simulated "Find Hidden Links" analysis result for an investigation
  async findHiddenLinks(investigationId: string) {
    await delay(1400)
    const inv = investigationById(investigationId)
    return {
      relatedIncidents: inv?.incidentIds.length ?? 12,
      recurringEntities: inv?.entityIds.length ?? 3,
      sharedCorridors: inv?.routeIds.length ?? 2,
      emergingNetworks: 1,
    }
  },

  async generateBrief(investigationId: string) {
    await delay(1600)
    const inv = investigationById(investigationId)
    if (!inv) return null
    return inv
  },
}
