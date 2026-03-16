import apiClient from './api-client'
import type { SessionCreate, SessionUpdate, SessionResponse, SessionListResponse } from '../types'

export interface SessionFilters {
  offset?: number
  limit?: number
  date_from?: string
  date_to?: string
  session_type?: string
}

export async function getSessions(filters?: SessionFilters): Promise<SessionListResponse> {
  const { data } = await apiClient.get<SessionListResponse>('/journal/sessions', {
    params: filters,
  })
  return data
}

export async function getSession(id: string): Promise<SessionResponse> {
  const { data } = await apiClient.get<SessionResponse>(`/journal/sessions/${id}`)
  return data
}

export async function createSession(body: SessionCreate): Promise<SessionResponse> {
  const { data } = await apiClient.post<SessionResponse>('/journal/sessions', body)
  return data
}

export async function updateSession(id: string, body: SessionUpdate): Promise<SessionResponse> {
  const { data } = await apiClient.patch<SessionResponse>(`/journal/sessions/${id}`, body)
  return data
}

export async function deleteSession(id: string): Promise<void> {
  await apiClient.delete(`/journal/sessions/${id}`)
}
