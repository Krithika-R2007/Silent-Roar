import { useEffect, useState } from 'react'
import { Evidence, EvidenceType } from '../types'
import { apiClient } from '../services/apiClient'
import { LoadingState, EmptyState } from '../components/ui/States'
import { EvidenceCard } from '../components/evidence/EvidenceCard'
import { cx } from '../utils/format'

type FilterKey = EvidenceType | 'ALL'
const filters: FilterKey[] = ['ALL', 'TRADE', 'SATELLITE', 'BEHAVIOUR', 'LINGUISTIC', 'NETWORK', 'DOCUMENT']

export default function EvidencePage() {
  const [evidence, setEvidence] = useState<Evidence[] | null>(null)
  const [filter, setFilter] = useState<FilterKey>('ALL')

  useEffect(() => {
    apiClient.getEvidence().then(setEvidence)
  }, [])

  if (!evidence) return <LoadingState />

  const filtered = evidence.filter((e) => filter === 'ALL' || e.type === filter)

  return (
    <div className="mx-auto max-w-[1400px] space-y-4 p-6">
      <div className="flex flex-wrap gap-2">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cx(
              'focus-ring rounded-md border px-3.5 py-1.5 font-ui text-[12.5px] font-semibold uppercase tracking-wide transition-colors',
              filter === f
                ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-700'
                : 'border-base-700 text-ink-400 hover:border-base-600 hover:text-ink-200'
            )}
          >
            {f}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyState title="No evidence found" description="Try a different category filter." />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((item) => (
            <EvidenceCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  )
}
