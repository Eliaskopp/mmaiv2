import apiClient from './api-client'
import type { PerformanceEvent, PerformanceEventList, TrainingState } from '../types'

function normalizeEvent(e: PerformanceEvent): PerformanceEvent {
  return { ...e, root_causes: e.root_causes ?? [], highlights: e.highlights ?? [] }
}

function normalizeState(s: TrainingState): TrainingState {
  return {
    ...s,
    current_focus: s.current_focus ?? [],
    active_injuries: s.active_injuries ?? [],
    short_term_goals: s.short_term_goals ?? [],
  }
}

export async function getPerformanceEvents(offset = 0, limit = 20): Promise<PerformanceEventList> {
  const { data } = await apiClient.get<PerformanceEventList>('/memory/events', {
    params: { offset, limit },
  })
  return { ...data, items: data.items.map(normalizeEvent) }
}

export async function getTrainingState(): Promise<TrainingState | null> {
  const { data } = await apiClient.get<TrainingState | null>('/memory/state')
  return data ? normalizeState(data) : null
}
