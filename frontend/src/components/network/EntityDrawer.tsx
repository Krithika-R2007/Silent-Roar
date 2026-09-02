import { X } from 'lucide-react'
import { Entity } from '../../types'
import { ConfidenceBar } from '../ui/States'
import { Badge } from '../ui/Badge'

export function EntityDrawer({ entity, onClose }: { entity: Entity; onClose: () => void }) {
  const signals = [
    'Name similarity',
    'Location overlap',
    'Route overlap',
    'Temporal proximity',
  ].slice(0, Math.max(2, Math.round(entity.confidence / 25)))

  return (
    <div className="animate-slide-in-right fixed inset-y-0 right-0 z-50 w-full max-w-sm border-l border-slate-200 bg-white shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-widest text-amber-600">Possible Entity Match</div>
          <div className="mt-1 text-[17px] font-bold text-slate-800">{entity.name}</div>
        </div>
        <button onClick={onClose} className="focus-ring rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="space-y-5 overflow-y-auto px-5 py-5" style={{ height: 'calc(100% - 65px)' }}>
        <div>
          <Badge tone="amber">{entity.type}</Badge>
        </div>

        <ConfidenceBar value={entity.confidence} />

        <div>
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-slate-400">Signals</div>
          <ul className="space-y-1.5">
            {signals.map((s) => (
              <li key={s} className="flex items-center gap-2 text-[13px] text-slate-700">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                {s}
              </li>
            ))}
          </ul>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <MiniStat label="Associated Incidents" value={entity.associatedIncidentIds.length} />
          <MiniStat label="Locations" value={entity.locationIds.length} />
          <MiniStat label="Routes" value={entity.routeIds.length} />
          <MiniStat label="Signals" value={entity.signalCount} />
        </div>

        <div>
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-slate-400">Notes</div>
          <p className="text-[13px] leading-relaxed text-slate-600">{entity.notes}</p>
        </div>

        <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5 text-[12.5px] leading-relaxed text-amber-700">
          This is a probabilistic entity resolution generated from overlapping signals. It is not a confirmed identity.
        </div>
      </div>
    </div>
  )
}

function MiniStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5">
      <div className="text-xl font-bold text-slate-800">{value}</div>
      <div className="mt-0.5 text-[11px] text-slate-500">{label}</div>
    </div>
  )
}
