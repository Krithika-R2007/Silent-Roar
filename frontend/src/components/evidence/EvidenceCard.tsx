import { Evidence } from '../../types'
import { formatDateTime } from '../../utils/format'
import { locationById } from '../../data/locations'
import { Badge } from '../ui/Badge'
import { ConfidenceBar } from '../ui/States'
import { Boxes, Satellite, PawPrint, MessageSquareText, Waypoints, FileText } from 'lucide-react'

const typeIcon: Record<Evidence['type'], typeof Boxes> = {
  TRADE: Boxes,
  SATELLITE: Satellite,
  BEHAVIOUR: PawPrint,
  LINGUISTIC: MessageSquareText,
  NETWORK: Waypoints,
  DOCUMENT: FileText,
}

const statusTone: Record<Evidence['status'], 'emerald' | 'cyan' | 'default'> = {
  SUPPORTING: 'emerald',
  CORROBORATING: 'cyan',
  UNVERIFIED: 'default',
}

export function EvidenceCard({ item }: { item: Evidence }) {
  const Icon = typeIcon[item.type]
  const loc = item.locationId ? locationById(item.locationId) : undefined

  return (
    <div className="panel p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-base-700/60 text-emerald-600">
            <Icon className="h-4 w-4" strokeWidth={1.75} />
          </span>
          <div>
            <div className="label-meta text-ink-500">{item.id.toUpperCase()}</div>
            <div className="font-display text-[13.5px] font-semibold text-ink-100">{item.title}</div>
          </div>
        </div>
        <Badge tone={statusTone[item.status]}>{item.status}</Badge>
      </div>

      <p className="mt-3 text-[12.5px] leading-relaxed text-ink-400">{item.description}</p>

      <div className="mt-3 grid grid-cols-2 gap-y-1.5 text-[14px]">
        <InfoField label="Type" value={item.type} />
        <InfoField label="Timestamp" value={formatDateTime(item.timestamp)} />
        <InfoField label="Location" value={loc?.name ?? '—'} />
        <InfoField label="Source" value={item.source} />
        <InfoField label="Relationships" value={String(item.relationshipCount)} />
      </div>

      <div className="mt-3">
        <ConfidenceBar value={item.confidence} compact />
      </div>
    </div>
  )
}

function InfoField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-ink-600">{label}: </span>
      <span className="text-ink-300">{value}</span>
    </div>
  )
}
