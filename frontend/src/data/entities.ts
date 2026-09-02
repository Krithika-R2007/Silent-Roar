import { Entity } from '../types'

export const entities: Entity[] = [
  { id: 'ent-01', name: 'Entity K-17', type: 'Possible Actor', confidence: 84, associatedIncidentIds: ['inc-01', 'inc-02', 'inc-09', 'inc-14'], locationIds: ['loc-01', 'loc-02'], routeIds: ['route-01', 'route-02'], signalCount: 12, notes: 'Recurs across three incidents on the Kutai–Serang corridor. No confirmed identity.' },
  { id: 'ent-02', name: 'Entity K-24', type: 'Possible Actor', confidence: 87, associatedIncidentIds: ['inc-02', 'inc-03', 'inc-11', 'inc-13', 'inc-14'], locationIds: ['loc-02', 'loc-03'], routeIds: ['route-02'], signalCount: 15, notes: 'Highest-confidence possible match in this network. Name similarity plus route overlap.' },
  { id: 'ent-03', name: 'Entity M-05', type: 'Intermediary', confidence: 71, associatedIncidentIds: ['inc-03', 'inc-04', 'inc-11'], locationIds: ['loc-03', 'loc-04'], routeIds: ['route-02', 'route-03'], signalCount: 8, notes: 'Possible intermediary between transit and market-side handling.' },
  { id: 'ent-04', name: 'Entity R-09', type: 'Shipping Contact', confidence: 62, associatedIncidentIds: ['inc-01'], locationIds: ['loc-01'], routeIds: ['route-01'], signalCount: 4, notes: 'Freight contact associated with a single incident to date.' },
  { id: 'ent-05', name: 'Entity T-11', type: 'Possible Actor', confidence: 58, associatedIncidentIds: ['inc-05', 'inc-06'], locationIds: ['loc-05', 'loc-06'], routeIds: ['route-04'], signalCount: 6, notes: 'Associated with two ivory-corridor incidents in Thailand.' },
  { id: 'ent-06', name: 'Entity T-19', type: 'Possible Actor', confidence: 75, associatedIncidentIds: ['inc-06', 'inc-07', 'inc-15'], locationIds: ['loc-06', 'loc-07'], routeIds: ['route-05'], signalCount: 9, notes: 'Recurs at Mong La market across two monitoring cycles.' },
  { id: 'ent-07', name: 'Entity Y-03', type: 'Intermediary', confidence: 66, associatedIncidentIds: ['inc-07', 'inc-08'], locationIds: ['loc-07', 'loc-08'], routeIds: ['route-06'], signalCount: 7, notes: 'Possible link between Mong La and Kunming depot inventory anomaly.' },
  { id: 'ent-08', name: 'Entity V-14', type: 'Shipping Contact', confidence: 54, associatedIncidentIds: ['inc-16', 'inc-17'], locationIds: ['loc-09'], routeIds: ['route-07'], signalCount: 5, notes: 'Repeat exporter of record on Hai Phong timber shipments.' },
  { id: 'ent-09', name: 'Entity S-02', type: 'Possible Actor', confidence: 81, associatedIncidentIds: ['inc-18', 'inc-19'], locationIds: ['loc-10', 'loc-11'], routeIds: ['route-08'], signalCount: 11, notes: 'Cargo manifest overlap between Selous and Entebbe incidents.' },
  { id: 'ent-10', name: 'Entity S-06', type: 'Possible Actor', confidence: 69, associatedIncidentIds: ['inc-18', 'inc-20'], locationIds: ['loc-11'], routeIds: ['route-08'], signalCount: 8, notes: 'Associated with corridor displacement following enforcement activity.' },
  { id: 'ent-11', name: 'Entity D-08', type: 'Shipping Contact', confidence: 60, associatedIncidentIds: ['inc-19', 'inc-21'], locationIds: ['loc-10', 'loc-12'], routeIds: ['route-08', 'route-09'], signalCount: 6, notes: 'Freight forwarder flagged in two consecutive terminal incidents.' },
  { id: 'ent-12', name: 'Entity Q-27', type: 'Intermediary', confidence: 47, associatedIncidentIds: [], locationIds: ['loc-04'], routeIds: [], signalCount: 3, notes: 'Low-confidence signal from vendor network mapping. No incident association yet.' },
]

export const entityById = (id: string) => entities.find((e) => e.id === id)
