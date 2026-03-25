import apiClient from './api-client'
import type { RecoveryLogCreate, RecoveryLogResponse, RecoveryLogListResponse } from '../types'

export interface RecoveryLogFilters {
  offset?: number
  limit?: number
  date_from?: string
  date_to?: string
}

export async function getRecoveryLogs(
  filters?: RecoveryLogFilters,
): Promise<RecoveryLogListResponse> {
  const { data } = await apiClient.get<RecoveryLogListResponse>('/recovery/logs', {
    params: filters,
  })
  return data
}

export async function getRecoveryLog(date: string): Promise<RecoveryLogResponse> {
  const { data } = await apiClient.get<RecoveryLogResponse>(`/recovery/logs/${date}`)
  return data
}

export async function upsertRecoveryLog(body: RecoveryLogCreate): Promise<RecoveryLogResponse> {
  const { data } = await apiClient.post<RecoveryLogResponse>('/recovery/logs', body)
  return data
}
