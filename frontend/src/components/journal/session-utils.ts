import type { LucideIcon } from 'lucide-react'
import {
  Flame,
  Shield,
  Zap,
  Swords,
  Grip,
  Activity,
  Dumbbell,
  MoreHorizontal,
} from 'lucide-react'
import type { SessionResponse } from '../../types'

interface SessionTypeConfig {
  label: string
  color: string
  icon: LucideIcon
}

export const SESSION_TYPE_MAP: Record<string, SessionTypeConfig> = {
  muay_thai:     { label: 'Muay Thai',     color: '#EF4444', icon: Flame },
  bjj_gi:        { label: 'BJJ Gi',        color: '#3B82F6', icon: Shield },
  bjj_nogi:      { label: 'BJJ No-Gi',     color: '#8B5CF6', icon: Shield },
  boxing:        { label: 'Boxing',         color: '#F59E0B', icon: Zap },
  mma:           { label: 'MMA',            color: '#FF6B35', icon: Swords },
  wrestling:     { label: 'Wrestling',      color: '#10B981', icon: Grip },
  conditioning:  { label: 'Conditioning',   color: '#06B6D4', icon: Activity },
  strength:      { label: 'Strength',       color: '#EC4899', icon: Dumbbell },
  other:         { label: 'Other',          color: '#6B7280', icon: MoreHorizontal },
}

export const SESSION_TYPE_OPTIONS = Object.entries(SESSION_TYPE_MAP).map(([value, cfg]) => ({
  value,
  label: cfg.label,
}))

interface DateGroup {
  label: string
  sessions: SessionResponse[]
}

export function groupSessionsByDate(sessions: SessionResponse[]): DateGroup[] {
  const now = new Date()
  const todayStr = now.toISOString().slice(0, 10)
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  const yesterdayStr = yesterday.toISOString().slice(0, 10)

  const groups: Map<string, DateGroup> = new Map()

  for (const session of sessions) {
    const dateStr = session.session_date.slice(0, 10)
    let label: string
    if (dateStr === todayStr) {
      label = 'Today'
    } else if (dateStr === yesterdayStr) {
      label = 'Yesterday'
    } else {
      const d = new Date(dateStr + 'T00:00:00')
      label = d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
    }

    const existing = groups.get(dateStr)
    if (existing) {
      existing.sessions.push(session)
    } else {
      groups.set(dateStr, { label, sessions: [session] })
    }
  }

  return Array.from(groups.values())
}

export function getRPEColor(value: number): string {
  if (value <= 3) return '#22C55E'
  if (value <= 6) return '#EAB308'
  if (value <= 8) return '#F97316'
  return '#EF4444'
}

export function getRPELabel(value: number): string {
  if (value <= 3) return 'Light'
  if (value <= 6) return 'Moderate'
  if (value <= 8) return 'Hard'
  return 'Max Effort'
}
