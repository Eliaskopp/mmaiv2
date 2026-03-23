import { useQuery } from '@tanstack/react-query'
import { getPerformanceEvents, getTrainingState } from '../services/memory'

export const MEMORY_KEY = ['memory'] as const
export const EVENTS_KEY = [...MEMORY_KEY, 'events'] as const
export const STATE_KEY = [...MEMORY_KEY, 'state'] as const

export function usePerformanceEvents(limit = 20) {
  return useQuery({
    queryKey: [...EVENTS_KEY, limit] as const,
    queryFn: () => getPerformanceEvents(0, limit),
    staleTime: 60_000,
  })
}

export function useTrainingState() {
  return useQuery({
    queryKey: STATE_KEY,
    queryFn: getTrainingState,
    staleTime: 60_000,
  })
}
