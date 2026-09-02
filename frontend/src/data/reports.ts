import { Report } from '../types'

export const reports: Report[] = [
  { id: 'rep-01', caseId: 'CASE-2026-0114', title: 'Emerging Pangolin Network — Investigation Brief', threatLevel: 'CRITICAL', generatedAt: '2026-03-20T09:00:00Z', investigationId: 'inv-01' },
  { id: 'rep-02', caseId: 'CASE-2026-0088', title: 'Repeated Transit Corridor Activity — Interim Brief', threatLevel: 'HIGH', generatedAt: '2026-03-14T09:00:00Z', investigationId: 'inv-02' },
  { id: 'rep-03', caseId: 'CASE-2026-0061', title: 'Selous–Entebbe Ivory Network — Interim Brief', threatLevel: 'HIGH', generatedAt: '2026-03-02T09:00:00Z', investigationId: 'inv-03' },
]

export const reportById = (id: string) => reports.find((r) => r.id === id)
