import { useQuery } from '@tanstack/react-query'
import { getACWR, getVolumeTrends } from '../services/stats'

export const STATS_KEY = ['stats'] as const
export const ACWR_KEY = [...STATS_KEY, 'acwr'] as const
export const VOLUME_KEY = [...STATS_KEY, 'volume'] as const

export function useACWR() {
  return useQuery({
    queryKey: ACWR_KEY,
    queryFn: getACWR,
    staleTime: 60_000,
  })
}

export function useVolumeTrends(days: number = 30) {
  return useQuery({
    queryKey: [...VOLUME_KEY, days] as const,
    queryFn: () => getVolumeTrends(days),
    staleTime: 60_000,
  })
}
