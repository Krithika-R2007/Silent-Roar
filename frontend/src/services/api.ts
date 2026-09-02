/**
 * api.ts
 * ------
 * Real HTTP client for the Silent Roar FastAPI backend.
 * Base URL is read from VITE_API_URL env var (default: http://localhost:8000).
 */

const BASE = import.meta.env.VITE_API_URL ?? ''

// ── Low-level fetch helper ────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { message?: string }).message ?? `API error ${res.status}`)
  }
  return res.json() as Promise<T>
}

// ── Health probe ──────────────────────────────────────────────────────────────

export async function probeBackend(): Promise<boolean> {
  try {
    const ctrl = new AbortController()
    const timer = setTimeout(() => ctrl.abort(), 3000)
    const res = await fetch(`/api/health`, { signal: ctrl.signal })
    clearTimeout(timer)
    return res.ok
  } catch {
    return false
  }
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export interface DashboardSummary {
  total_incidents: number
  total_actors: number
  total_routes: number
  total_shipments: number
  total_alerts: number
  critical_alerts: number
  high_alerts: number
  watch_alerts: number
  active_investigations: number
  high_risk_routes: number
  emerging_hubs: number
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return apiFetch('/api/dashboard/summary')
}

// ── Alerts ────────────────────────────────────────────────────────────────────

export interface ApiAlert {
  alert_id: string
  title: string
  pattern_type: string | null
  entity_type: string | null
  entity_id: string | null
  priority: string | null
  risk_score: number | null
  confidence: number | null
  explanation: string | null
  first_detected: string | null
  last_detected: string | null
}

export interface AlertListResponse {
  total: number
  alerts: ApiAlert[]
}

export async function getAlerts(params?: {
  priority?: string
  pattern_type?: string
  limit?: number
  offset?: number
}): Promise<AlertListResponse> {
  const q = new URLSearchParams()
  if (params?.priority) q.set('priority', params.priority)
  if (params?.pattern_type) q.set('pattern_type', params.pattern_type)
  if (params?.limit !== undefined) q.set('limit', String(params.limit))
  if (params?.offset !== undefined) q.set('offset', String(params.offset))
  return apiFetch(`/api/alerts${q.toString() ? `?${q}` : ''}`)
}

// ── Incidents ─────────────────────────────────────────────────────────────────

export interface ApiIncident {
  incident_id: string
  incident_date: string | null
  species: string | null
  commodity: string | null
  quantity: number | null
  source_location: string | null
  destination: string | null
  route_id: string | null
  lead_actor: string | null
  seizure_status: string | null
  latitude: number | null
  longitude: number | null
}

export interface IncidentListResponse {
  total: number
  incidents: ApiIncident[]
}

export async function getIncidents(params?: {
  search?: string
  species?: string
  limit?: number
  offset?: number
}): Promise<IncidentListResponse> {
  const q = new URLSearchParams()
  if (params?.search) q.set('search', params.search)
  if (params?.species) q.set('species', params.species)
  if (params?.limit !== undefined) q.set('limit', String(params.limit))
  if (params?.offset !== undefined) q.set('offset', String(params.offset))
  return apiFetch(`/api/incidents${q.toString() ? `?${q}` : ''}`)
}

export async function getIncidentDetail(id: string) {
  return apiFetch<Record<string, unknown>>(`/api/incidents/${id}`)
}

// ── Actors ────────────────────────────────────────────────────────────────────

export interface ApiActor {
  actor_id: string
  full_name: string | null
  alias: string | null
  nationality: string | null
  role: string | null
  primary_region: string | null
  threat_score: number | null
}

export interface ActorListResponse {
  total: number
  actors: ApiActor[]
}

export async function getActors(params?: {
  name?: string
  limit?: number
  offset?: number
}): Promise<ActorListResponse> {
  const q = new URLSearchParams()
  if (params?.name) q.set('name', params.name)
  if (params?.limit !== undefined) q.set('limit', String(params.limit))
  if (params?.offset !== undefined) q.set('offset', String(params.offset))
  return apiFetch(`/api/actors${q.toString() ? `?${q}` : ''}`)
}

export async function getActor(id: string) {
  return apiFetch<Record<string, unknown>>(`/api/actors/${id}`)
}

// ── Routes ────────────────────────────────────────────────────────────────────

export interface ApiRoute {
  route_id: string
  source: string | null
  transit: string | null
  destination: string | null
  risk_score: number | null
  route_status: string | null
  incident_count: number | null
  actor_count: number | null
}

export interface RouteListResponse {
  total: number
  routes: ApiRoute[]
}

export async function getRoutes(params?: {
  limit?: number
  offset?: number
}): Promise<RouteListResponse> {
  const q = new URLSearchParams()
  if (params?.limit !== undefined) q.set('limit', String(params.limit))
  return apiFetch(`/api/routes${q.toString() ? `?${q}` : ''}`)
}

export async function getRoute(id: string) {
  return apiFetch<Record<string, unknown>>(`/api/routes/${id}`)
}

// ── Map ───────────────────────────────────────────────────────────────────────

export interface ApiMapPoint {
  id: string
  type: string
  latitude: number
  longitude: number
  name: string
  risk_score: number | null
  priority: string | null
  related_count: number
}

export interface ApiMapRoute {
  route_id: string
  source: string | null
  transit: string | null
  destination: string | null
  risk_score: number | null
}

export interface MapDataResponse {
  points: ApiMapPoint[]
  routes: ApiMapRoute[]
}

export async function getMapData(): Promise<MapDataResponse> {
  return apiFetch('/api/map')
}

// ── Search ────────────────────────────────────────────────────────────────────

export interface ApiSearchResponse {
  incidents: Record<string, unknown>[]
  actors: Record<string, unknown>[]
  routes: Record<string, unknown>[]
  locations: string[]
}

export async function searchApi(q: string): Promise<ApiSearchResponse> {
  return apiFetch(`/api/search?q=${encodeURIComponent(q)}`)
}

// ── Network ───────────────────────────────────────────────────────────────────

export async function getNetwork(targetType: string, targetId: string) {
  return apiFetch<Record<string, unknown>>(`/api/network/${targetType}/${targetId}`)
}

export async function getHiddenLinks(targetType: string, targetId: string) {
  return apiFetch<Record<string, unknown>>(`/api/hidden-links/${targetType}/${targetId}`)
}

// ── Intelligence ──────────────────────────────────────────────────────────────

export async function getIntelligence(targetType: string, targetId: string) {
  return apiFetch<Record<string, unknown>>(`/api/intelligence/${targetType}/${targetId}`)
}

export async function getInvestigationBrief(targetType: string, targetId: string) {
  return apiFetch<Record<string, unknown>>(`/api/investigation/${targetType}/${targetId}`)
}

export async function getInvestigationsList() {
  return apiFetch<Record<string, unknown>[]>('/api/investigation/all')
}

export async function getInvestigationFull(targetId: string) {
  return apiFetch<Record<string, unknown>>(`/api/investigation/details/${targetId}`)
}

// ── Messages ──────────────────────────────────────────────────────────────────

export async function getChannels() {
  return apiFetch<Record<string, unknown>[]>('/api/messages/channels')
}

export async function getMessages(channel?: string) {
  const q = channel ? `?channel=${encodeURIComponent(channel)}` : ''
  return apiFetch<Record<string, unknown>[]>(`/api/messages${q}`)
}

export async function analyzeMessage(sender: string, receiver: string, message: string) {
  return apiFetch<Record<string, unknown>>('/api/messages/analyze', {
    method: 'POST',
    body: JSON.stringify({ sender, receiver, message }),
  })
}
