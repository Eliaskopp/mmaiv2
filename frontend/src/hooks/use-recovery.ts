import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getRecoveryLogs, getRecoveryLog, upsertRecoveryLog } from '../services/recovery'
import type { RecoveryLogFilters } from '../services/recovery'
import type { RecoveryLogCreate } from '../types'
import type { AxiosError } from 'axios'

export const RECOVERY_LOGS_KEY = ['recovery-logs'] as const

export function useRecoveryLogs(filters?: RecoveryLogFilters) {
  return useQuery({
    queryKey: [...RECOVERY_LOGS_KEY, filters] as const,
    queryFn: () => getRecoveryLogs(filters),
    staleTime: 60_000,
  })
}

export function useRecoveryLog(date: string) {
  return useQuery({
    queryKey: [...RECOVERY_LOGS_KEY, date] as const,
    queryFn: () => getRecoveryLog(date),
    enabled: !!date,
    staleTime: 60_000,
    retry: (_count, error) => (error as AxiosError)?.response?.status !== 404,
  })
}

export function useUpsertRecoveryLog() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: RecoveryLogCreate) => upsertRecoveryLog(body),
    onSuccess: (data) => {
      queryClient.setQueryData([...RECOVERY_LOGS_KEY, data.logged_for], data)
      queryClient.invalidateQueries({ queryKey: RECOVERY_LOGS_KEY })
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}
