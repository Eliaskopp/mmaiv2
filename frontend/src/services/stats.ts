import apiClient from './api-client'
import type { ACWRResponse, DailyVolumePoint } from '../types'

export async function getACWR(): Promise<ACWRResponse> {
  const { data } = await apiClient.get<ACWRResponse>('/stats/acwr')
  return data
}

export async function getVolumeTrends(days?: number): Promise<DailyVolumePoint[]> {
  const { data } = await apiClient.get<DailyVolumePoint[]>('/stats/volume', {
    params: days ? { days } : undefined,
  })
  return data
}
