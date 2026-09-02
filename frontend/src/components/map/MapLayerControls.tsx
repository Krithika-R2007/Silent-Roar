import { Boxes, Waypoints, Satellite, PawPrint, Siren } from 'lucide-react'
import { cx } from '../../utils/format'

export interface MapLayers {
  incidents: boolean
  routes: boolean
  environmental: boolean
  behaviour: boolean
  alerts: boolean
}

const layerConfig: { key: keyof MapLayers; label: string; icon: typeof Boxes }[] = [
  { key: 'incidents', label: 'Trade Incidents', icon: Boxes },
  { key: 'routes', label: 'Trafficking Routes', icon: Waypoints },
  { key: 'environmental', label: 'Environmental Signals', icon: Satellite },
  { key: 'behaviour', label: 'Animal Behaviour', icon: PawPrint },
  { key: 'alerts', label: 'Intelligence Alerts', icon: Siren },
]

export function MapLayerControls({
  layers,
  onToggle,
}: {
  layers: MapLayers
  onToggle: (key: keyof MapLayers) => void
}) {
  return (
    <div className="panel flex flex-col gap-1 p-3">
      <span className="font-heading label-meta mb-1 px-1">Map Layers</span>
      {layerConfig.map(({ key, label, icon: Icon }) => (
        <button
          key={key}
          onClick={() => onToggle(key)}
          className={cx(
            'focus-ring flex items-center gap-2.5 rounded-md px-2.5 py-2 text-left text-[15px] transition-colors',
            layers[key] ? 'bg-emerald-500/10 text-emerald-700' : 'text-ink-400 hover:bg-base-800 hover:text-ink-200'
          )}
        >
          <span
            className={cx(
              'flex h-4 w-4 shrink-0 items-center justify-center rounded-sm border',
              layers[key] ? 'border-emerald-500 bg-emerald-500' : 'border-base-600'
            )}
          >
            {layers[key] && <span className="h-1.5 w-1.5 rounded-[1px] bg-base-950" />}
          </span>
          <Icon className="h-3.5 w-3.5 shrink-0" strokeWidth={1.75} />
          <span className="font-ui truncate">{label}</span>
        </button>
      ))}
    </div>
  )
}
