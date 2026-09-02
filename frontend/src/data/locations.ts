import { Location } from '../types'

// Stylized demonstration corridor. `x`/`y` are legacy percentage positions
// used only by the abstract network graph. `lat`/`lng` are approximate
// real-world coordinates for the named locality, used by the Leaflet
// intelligence map.
export const locations: Location[] = [
  // ── South / Southeast Asia ──────────────────────────────────────────────
  { id: 'loc-01', name: 'Kutai Basin', country: 'Indonesia', x: 78, y: 62, lat: 0.35, lng: 117.4, kind: 'RESERVE' },
  { id: 'loc-02', name: 'Port Serang', country: 'Indonesia', x: 71, y: 68, lat: -6.12, lng: 106.15, kind: 'PORT' },
  { id: 'loc-03', name: 'Northern Crossing', country: 'Malaysia', x: 66, y: 52, lat: 1.55, lng: 110.35, kind: 'CROSSING' },
  { id: 'loc-04', name: 'Kuching Transit Market', country: 'Malaysia', x: 69, y: 58, lat: 1.5533, lng: 110.3592, kind: 'MARKET' },
  { id: 'loc-05', name: 'Sattahip Freight Yard', country: 'Thailand', x: 58, y: 40, lat: 12.6624, lng: 100.9067, kind: 'PORT' },
  { id: 'loc-06', name: 'Mae Sot Corridor', country: 'Thailand', x: 52, y: 36, lat: 16.7154, lng: 98.5686, kind: 'CORRIDOR' },
  { id: 'loc-07', name: 'Mong La Market', country: 'Myanmar', x: 55, y: 30, lat: 21.4167, lng: 99.9167, kind: 'MARKET' },
  { id: 'loc-08', name: 'Kunming Depot', country: 'China', x: 60, y: 22, lat: 25.0389, lng: 102.7183, kind: 'CITY' },
  { id: 'loc-09', name: 'Hai Phong Terminal', country: 'Vietnam', x: 64, y: 28, lat: 20.8449, lng: 106.6881, kind: 'PORT' },

  // ── India (matches backend investigation_targets.csv) ───────────────────
  { id: 'loc-13', name: 'Mumbai Port', country: 'India', x: 44, y: 42, lat: 18.9388, lng: 72.8354, kind: 'PORT' },
  { id: 'loc-14', name: 'Kochi Port', country: 'India', x: 44, y: 48, lat: 9.9312, lng: 76.2673, kind: 'PORT' },
  { id: 'loc-15', name: 'Tuticorin Port', country: 'India', x: 46, y: 50, lat: 8.7642, lng: 78.1348, kind: 'PORT' },
  { id: 'loc-16', name: 'Chennai Terminal', country: 'India', x: 47, y: 46, lat: 13.0827, lng: 80.2707, kind: 'PORT' },
  { id: 'loc-17', name: 'Sundarbans Reserve', country: 'India', x: 50, y: 38, lat: 21.9497, lng: 89.1833, kind: 'RESERVE' },

  // ── East Africa ──────────────────────────────────────────────────────────
  { id: 'loc-10', name: 'Entebbe Cargo Hub', country: 'Uganda', x: 20, y: 48, lat: 0.0512, lng: 32.4633, kind: 'PORT' },
  { id: 'loc-11', name: 'Selous Corridor', country: 'Tanzania', x: 24, y: 60, lat: -8.75, lng: 37.75, kind: 'CORRIDOR' },
  { id: 'loc-12', name: 'Dar Es Salaam Terminal', country: 'Tanzania', x: 27, y: 66, lat: -6.7924, lng: 39.2083, kind: 'PORT' },
  { id: 'loc-18', name: 'Mombasa', country: 'Kenya', x: 25, y: 56, lat: -4.0435, lng: 39.6682, kind: 'PORT' },
  { id: 'loc-19', name: 'Nairobi Transit Hub', country: 'Kenya', x: 23, y: 54, lat: -1.2921, lng: 36.8219, kind: 'CITY' },
  { id: 'loc-20', name: 'Serengeti Reserve', country: 'Tanzania', x: 22, y: 58, lat: -2.3333, lng: 34.8333, kind: 'RESERVE' },
]

export const locationById = (id: string) => locations.find((l) => l.id === id)

/** Match by display name — used when backend returns a location name string rather than an id */
export const locationByName = (name: string) => {
  const q = name.toLowerCase().trim()
  return locations.find((l) => l.name.toLowerCase() === q)
}
