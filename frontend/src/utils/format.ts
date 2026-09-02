import { Severity } from '../types'

export function formatDate(iso: string) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })
}

export function formatDateShort(iso: string) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString('en-US', { month: 'short', day: '2-digit' }).toUpperCase()
}

export function formatDateTime(iso: string) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('en-US', { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

export const severityColor: Record<Severity, { text: string; bg: string; border: string; dot: string }> = {
  CRITICAL: { text: 'text-crimson-600', bg: 'bg-crimson-500/10', border: 'border-crimson-500/30', dot: 'bg-crimson-500' },
  HIGH: { text: 'text-amber-600', bg: 'bg-amber-500/10', border: 'border-amber-500/30', dot: 'bg-amber-500' },
  MEDIUM: { text: 'text-cyan-600', bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', dot: 'bg-cyan-500' },
  WATCH: { text: 'text-ink-400', bg: 'bg-ink-500/10', border: 'border-ink-500/30', dot: 'bg-ink-400' },
}

export function riskTone(score: number) {
  if (score >= 80) return 'text-crimson-600'
  if (score >= 60) return 'text-amber-600'
  if (score >= 40) return 'text-cyan-600'
  return 'text-emerald-600'
}

export function riskBarColor(score: number) {
  if (score >= 80) return 'bg-crimson-500'
  if (score >= 60) return 'bg-amber-500'
  if (score >= 40) return 'bg-cyan-500'
  return 'bg-emerald-500'
}

export function cx(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}
