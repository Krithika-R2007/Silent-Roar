import { useMemo, useState, useEffect } from 'react'
import { X, MapPin } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { locations } from '../../data/locations'
import { routes } from '../../data/routes'
import { MapLayers } from './MapLayerControls'
import { getLocationIntel } from '../../utils/mapIntel'
import { riskTone, cx } from '../../utils/format'
import { ConfidenceBar } from '../ui/States'
import { apiClient } from '../../services/apiClient'

const kindColor: Record<string, string> = {
  PORT: '#2C7E92',
  CROSSING: '#B5811F',
  MARKET: '#B33832',
  RESERVE: '#149447',
  CITY: '#7B8885',
  CORRIDOR: '#B5811F',
  INCIDENT: '#C4433D',
  LOCATION: '#3E9AB0',
}

// Google Maps-style basemap â€” clean green parks, familiar road styling
const TILE_URL = 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
const TILE_ATTRIBUTION = '&copy; <a href="https://maps.google.com">Google Maps</a>'

/** A live point from the backend /api/map endpoint */
interface LivePoint {
  id: string
  name: string
  type: string
  lat: number
  lng: number
  riskScore: number
  priority: string | null
  relatedCount: number
}

export function IntelligenceMapCanvas({
  layers,
  highlightLocationId,
  height = 560,
}: {
  layers: MapLayers
  highlightLocationId?: string | null
  height?: number
}) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [livePoints, setLivePoints] = useState<LivePoint[] | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (highlightLocationId) setSelectedId(highlightLocationId)
  }, [highlightLocationId])

  // Fetch live map points from backend when available
  useEffect(() => {
    apiClient.getMapData().then((data) => {
      if (data && data.points.length > 0) {
        setLivePoints(
          data.points.map((p) => ({
            id: p.id,
            name: p.name,
            type: p.type,
            lat: p.latitude,
            lng: p.longitude,
            riskScore: p.risk_score ?? 0,
            priority: p.priority,
            relatedCount: p.related_count,
          }))
        )
      }
    })
  }, [])

  const visibleLocations = useMemo(() => {
    // Show all locations when any layer is active; layer toggles affect styling/opacity
    const anyActive = Object.values(layers).some(Boolean)
    if (!anyActive) return []
    return locations.filter((loc) => {
      if (layers.incidents && ['PORT', 'MARKET', 'CROSSING', 'CITY', 'CORRIDOR'].includes(loc.kind)) return true
      if ((layers.environmental || layers.behaviour) && loc.kind === 'RESERVE') return true
      if (layers.alerts) return true
      return false
    })
  }, [layers])

  // selected can be a static location OR a live backend point
  const selectedStatic = selectedId ? locations.find((l) => l.id === selectedId) : null
  const selectedLive = selectedId && !selectedStatic ? livePoints?.find((p) => p.id === selectedId) : null
  const intel = selectedStatic ? getLocationIntel(selectedStatic.id) : null

  // Center on the Indian Ocean (India–Africa corridor)
  const center: [number, number] = [5, 65]

  return (
    <div className="relative w-full overflow-hidden rounded-2xl border border-slate-200 shadow-sm" style={{ height }}>
      <MapContainer
        center={center}
        zoom={4}
        minZoom={2}
        scrollWheelZoom
        className="h-full w-full"
        style={{ background: '#E8F0E9' }}
      >
        <TileLayer url={TILE_URL} attribution={TILE_ATTRIBUTION} maxZoom={20} />

        {layers.routes &&
          routes.map((r) => {
            const from = locations.find((l) => l.id === r.fromLocationId)
            const to = locations.find((l) => l.id === r.toLocationId)
            if (!from || !to) return null
            // Color by activity level: red=critical, amber=high, green=moderate
            const color = r.activityLevel >= 80 ? '#C4433D' : r.activityLevel >= 60 ? '#D19A3E' : '#149447'
            const weight = 1.2 + (r.activityLevel / 100) * 2.8
            const opacity = 0.45 + (r.activityLevel / 100) * 0.5
            return (
              <Polyline
                key={r.id}
                positions={[[from.lat, from.lng], [to.lat, to.lng]]}
                pathOptions={{
                  color,
                  weight,
                  opacity,
                  dashArray: r.activityLevel >= 70 ? undefined : '6 5',
                }}
              >
                <Tooltip sticky opacity={0.95}>
                  <span className="font-semibold">{r.name}</span>
                  <br />
                  <span className="opacity-70">{r.commodity} · activity {r.activityLevel}</span>
                </Tooltip>
              </Polyline>
            )
          })}

        {/* Static local locations */}
        {visibleLocations.map((loc) => {
          const locIntel = getLocationIntel(loc.id)
          const isCritical = locIntel.riskScore >= 70
          const isSelected = selectedId === loc.id
          const fillColor = kindColor[loc.kind] ?? '#7B8885'
          return (
            <CircleMarker
              key={loc.id}
              center={[loc.lat, loc.lng]}
              radius={isSelected ? 10 : isCritical && layers.alerts ? 9 : 7}
              pathOptions={{
                color: isSelected ? '#149447' : isCritical ? fillColor : '#FFFFFF',
                weight: isSelected ? 3 : isCritical ? 2 : 1.5,
                fillColor,
                fillOpacity: 0.92,
              }}
              eventHandlers={{ click: () => setSelectedId(loc.id) }}
            >
              <Tooltip direction="top" offset={[0, -6]} opacity={1} permanent={false}>
                <strong>{loc.name}</strong>
                {locIntel.riskScore > 40 && (
                  <span style={{ marginLeft: 4, opacity: 0.7 }}>· Risk {locIntel.riskScore}</span>
                )}
              </Tooltip>
            </CircleMarker>
          )
        })}

        {/* Live backend points â€” shown when backend is connected */}
        {livePoints &&
          layers.alerts &&
          livePoints.map((pt) => {
            // Skip if we already have a static marker very close to this point
            const nearby = locations.some(
              (l) => Math.abs(l.lat - pt.lat) < 0.5 && Math.abs(l.lng - pt.lng) < 0.5
            )
            if (nearby) return null
            const isSelected = selectedId === pt.id
            const isCritical = pt.priority === 'IMMEDIATE' || pt.riskScore >= 75
            const fillColor = isCritical ? '#C4433D' : '#D19A3E'
            return (
              <CircleMarker
                key={`live-${pt.id}`}
                center={[pt.lat, pt.lng]}
                radius={isSelected ? 9 : isCritical ? 8 : 6}
                pathOptions={{
                  color: isSelected ? '#149447' : '#FFFFFF',
                  weight: isSelected ? 3 : 2,
                  fillColor,
                  fillOpacity: 0.92,
                }}
                eventHandlers={{ click: () => setSelectedId(pt.id) }}
              >
                <Tooltip direction="top" offset={[0, -4]} opacity={1}>
                  <span className="font-medium">{pt.name}</span>
                  {pt.riskScore > 0 && (
                    <span className="ml-1 opacity-70">Â· Risk {pt.riskScore.toFixed(0)}</span>
                  )}
                </Tooltip>
              </CircleMarker>
            )
          })}
      </MapContainer>

      {/* legend */}
      <div className="pointer-events-none absolute bottom-3 left-3 z-[500] flex flex-wrap gap-x-4 gap-y-1 rounded-xl border border-slate-200 bg-white/90 px-3 py-2 shadow-sm backdrop-blur-sm">
        {Object.entries(kindColor)
          .filter(([k]) => !['INCIDENT', 'LOCATION'].includes(k))
          .map(([kind, color]) => (
            <span key={kind} className="flex items-center gap-1.5 text-[11px] text-slate-500">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
              {kind}
            </span>
          ))}
        <span className="flex items-center gap-1.5 text-[11px] text-red-600">
          <span className="inline-block h-0.5 w-4 rounded bg-red-500" /> HIGH ACTIVITY
        </span>
        <span className="flex items-center gap-1.5 text-[11px] text-amber-600">
          <span className="inline-block h-0.5 w-4 rounded bg-amber-500" /> MODERATE
        </span>
        {livePoints && (
          <span className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-600">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            LIVE DATA
          </span>
        )}
      </div>

      {/* Static location popup */}
      {selectedStatic && intel && (
        <div className="absolute right-4 top-4 z-[500] w-[300px] animate-fadeUp rounded-2xl border border-slate-200 bg-white shadow-xl backdrop-blur-md">
          <div className="flex items-start justify-between border-b border-slate-100 px-4 py-3">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-widest text-red-600">Multi-Signal Risk Event</div>
              <div className="mt-1 flex items-center gap-1.5 text-[14px] font-semibold text-slate-800">
                <MapPin className="h-3.5 w-3.5 text-slate-400" />
                {selectedStatic.name}
              </div>
            </div>
            <button onClick={() => setSelectedId(null)} className="focus-ring rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600">
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="space-y-3 px-4 py-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-500">Risk</span>
              <span className={cx('text-lg font-bold', riskTone(intel.riskScore))}>{intel.riskScore} / 100</span>
            </div>

            <IntelRow label="Trade Evidence" value={`${intel.tradeEvidence.length} related incident${intel.tradeEvidence.length === 1 ? '' : 's'}`} />
            <IntelRow label="Environmental Evidence" value={intel.satelliteEvidence.length ? 'Recent forest disturbance' : 'No active signal'} />
            <IntelRow label="Behavioural Evidence" value={intel.behaviourEvidence.length ? 'Movement deviation' : 'No active signal'} />
            <IntelRow label="Linguistic Signal" value={intel.linguisticEvidence.length ? 'Related terminology detected' : 'No active signal'} />

            <ConfidenceBar value={Math.min(96, intel.riskScore + 6)} compact />

            <button
              onClick={() => {
                const inv = intel.relatedIncidents[0]
                navigate(inv ? '/investigations/inv-01' : '/investigations')
              }}
              className="focus-ring mt-1 flex w-full items-center justify-center rounded-xl bg-emerald-700 py-2 text-[13px] font-semibold text-white transition-colors hover:bg-emerald-800"
            >
              View Intelligence
            </button>
          </div>
        </div>
      )}

      {/* Live backend point popup */}
      {selectedLive && (
        <div className="absolute right-4 top-4 z-[500] w-[300px] animate-fadeUp rounded-2xl border border-amber-200 bg-white shadow-xl backdrop-blur-md">
          <div className="flex items-start justify-between border-b border-slate-100 px-4 py-3">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-widest text-amber-600">Backend Intelligence Point</div>
              <div className="mt-1 flex items-center gap-1.5 text-[14px] font-semibold text-slate-800">
                <MapPin className="h-3.5 w-3.5 text-slate-400" />
                {selectedLive.name}
              </div>
            </div>
            <button onClick={() => setSelectedId(null)} className="focus-ring rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600">
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="space-y-3 px-4 py-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-500">Risk Score</span>
              <span className={cx('text-lg font-bold', riskTone(selectedLive.riskScore))}>
                {selectedLive.riskScore.toFixed(0)} / 100
              </span>
            </div>
            <IntelRow label="Priority" value={selectedLive.priority ?? 'WATCH'} />
            <IntelRow label="Type" value={selectedLive.type} />
            <IntelRow label="Related Events" value={String(selectedLive.relatedCount)} />

            <ConfidenceBar value={Math.min(96, selectedLive.riskScore + 6)} compact />

            <button
              onClick={() => navigate('/investigations')}
              className="focus-ring mt-1 flex w-full items-center justify-center rounded-xl bg-emerald-700 py-2 text-[13px] font-semibold text-white transition-colors hover:bg-emerald-800"
            >
              View Investigations
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function IntelRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-t border-slate-100 pt-2 first:border-t-0 first:pt-0">
      <span className="text-[12px] text-slate-500">{label}</span>
      <span className="text-right text-[12px] font-medium text-slate-700">{value}</span>
    </div>
  )
}
