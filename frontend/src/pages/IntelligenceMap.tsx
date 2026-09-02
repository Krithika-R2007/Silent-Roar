import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { IntelligenceMapCanvas } from '../components/map/IntelligenceMapCanvas'
import { MapLayerControls, MapLayers } from '../components/map/MapLayerControls'

const defaultLayers: MapLayers = { incidents: true, routes: true, environmental: true, behaviour: true, alerts: true }

export default function IntelligenceMap() {
  const [layers, setLayers] = useState<MapLayers>(defaultLayers)
  const [searchParams] = useSearchParams()
  const highlight = searchParams.get('location')

  const toggle = (key: keyof MapLayers) => setLayers((prev) => ({ ...prev, [key]: !prev[key] }))

  return (
    <div className="mx-auto max-w-[1400px] space-y-5 p-6">
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[220px_1fr]">
        <MapLayerControls layers={layers} onToggle={toggle} />
        <div>
          <IntelligenceMapCanvas layers={layers} highlightLocationId={highlight} height={620} />
        </div>
      </div>
    </div>
  )
}
