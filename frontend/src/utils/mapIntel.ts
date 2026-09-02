import { incidents } from '../data/incidents'
import { evidence } from '../data/evidence'
import { alerts } from '../data/alerts'
import { routes } from '../data/routes'

export function getLocationIntel(locationId: string) {
  const relatedIncidents = incidents.filter((i) => i.locationId === locationId)
  const relatedEvidence = evidence.filter((e) => e.locationId === locationId)
  const relatedAlerts = alerts.filter((a) => a.locationId === locationId)
  const relatedRoutes = routes.filter((r) => r.fromLocationId === locationId || r.toLocationId === locationId)

  const tradeEvidence = relatedEvidence.filter((e) => e.type === 'TRADE')
  const satelliteEvidence = relatedEvidence.filter((e) => e.type === 'SATELLITE')
  const behaviourEvidence = relatedEvidence.filter((e) => e.type === 'BEHAVIOUR')
  const linguisticEvidence = relatedEvidence.filter((e) => e.type === 'LINGUISTIC')

  const riskScore =
    relatedIncidents.length > 0
      ? Math.round(relatedIncidents.reduce((sum, i) => sum + i.riskScore, 0) / relatedIncidents.length)
      : relatedAlerts.length > 0
      ? Math.max(...relatedAlerts.map((a) => a.riskScore))
      : 32

  return {
    riskScore,
    relatedIncidents,
    relatedEvidence,
    relatedAlerts,
    relatedRoutes,
    tradeEvidence,
    satelliteEvidence,
    behaviourEvidence,
    linguisticEvidence,
  }
}
