export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'WATCH'
export type EvidenceType = 'TRADE' | 'SATELLITE' | 'BEHAVIOUR' | 'LINGUISTIC' | 'NETWORK' | 'DOCUMENT'
export type EntityType = 'ACTOR' | 'INCIDENT' | 'LOCATION' | 'SHIPMENT' | 'ROUTE' | 'EVIDENCE' | 'MESSAGE'
export type RelationType =
  | 'INVOLVED_IN'
  | 'ASSOCIATED_WITH'
  | 'OCCURRED_AT'
  | 'TRAVELLED_THROUGH'
  | 'LINKED_TO'
  | 'NEAR'
  | 'MENTIONED_IN'

export interface Location {
  id: string
  name: string
  country: string
  x: number // percent position on stylized map, 0-100 (legacy, kept for the network graph)
  y: number // percent position on stylized map, 0-100 (legacy, kept for the network graph)
  lat: number // real-world latitude, for the Leaflet intelligence map
  lng: number // real-world longitude, for the Leaflet intelligence map
  kind: 'PORT' | 'CROSSING' | 'MARKET' | 'RESERVE' | 'CITY' | 'CORRIDOR'
}

export interface RouteEdge {
  id: string
  name: string
  fromLocationId: string
  toLocationId: string
  activityLevel: number // 0-100
  commodity: string
  incidentIds: string[]
}

export interface Entity {
  id: string
  name: string
  type: 'Possible Actor' | 'Confirmed Actor' | 'Shipping Contact' | 'Intermediary'
  confidence: number
  associatedIncidentIds: string[]
  locationIds: string[]
  routeIds: string[]
  signalCount: number
  notes: string
}

export interface Incident {
  id: string
  title: string
  species: string
  date: string
  locationId: string
  routeId?: string
  riskScore: number
  status: 'OPEN' | 'UNDER_REVIEW' | 'CLOSED'
  summary: string
  entityIds: string[]
  evidenceIds: string[]
}

export interface Evidence {
  id: string
  type: EvidenceType
  title: string
  timestamp: string
  locationId?: string
  confidence: number
  source: string
  status: 'SUPPORTING' | 'CORROBORATING' | 'UNVERIFIED'
  relatedIncidentIds: string[]
  relationshipCount: number
  description: string
}

export interface Alert {
  id: string
  severity: Severity
  title: string
  time: string
  locationId?: string
  riskScore: number
  evidenceCount: number
  status: 'NEW' | 'REVIEWED' | 'ESCALATED'
  investigationId?: string
  description: string
  linkedIncidents: number
  linkedCountries?: number
}

export interface TimelineEvent {
  id: string
  date: string
  title: string
  description: string
  evidenceId?: string
}

export interface RiskFactor {
  label: string
  points: number
}

export interface Investigation {
  id: string
  codename: string
  riskScore: number
  previousRiskScore?: number
  status: 'ACTIVE' | 'MONITORING' | 'CLOSED'
  lastUpdated: string
  threatSummary: string
  primaryCommodity: string
  originCountry: string
  incidentIds: string[]
  entityIds: string[]
  evidenceIds: string[]
  routeIds: string[]
  timeline: TimelineEvent[]
  riskFactors: RiskFactor[]
}

export interface SignalMessage {
  id: string
  channelId: string
  author: string
  timestamp: string
  text: string
  flaggedTerms: { term: string; confidence: number }[]
  locationMention?: { locationId: string; label: string }
  addedToInvestigation?: boolean
}

export interface Channel {
  id: string
  name: string
  memberCount: number
  lastActivity: string
}

export interface GraphNode {
  id: string
  label: string
  type: EntityType
  confidence?: number
  x?: number
  y?: number
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  relation: RelationType
}

export interface Report {
  id: string
  caseId: string
  title: string
  threatLevel: Severity
  generatedAt: string
  investigationId: string
}
