import apiClient from './api-client'
import type { NoteCreate, NoteUpdate, NoteResponse, NoteListResponse } from '../types'

export interface NoteFilters {
  offset?: number
  limit?: number
  type?: string
  status?: string
  pinned?: boolean
}

export async function getNotes(filters?: NoteFilters): Promise<NoteListResponse> {
  const { data } = await apiClient.get<NoteListResponse>('/notes', {
    params: filters,
  })
  return data
}

export async function getNote(id: string): Promise<NoteResponse> {
  const { data } = await apiClient.get<NoteResponse>(`/notes/${id}`)
  return data
}

export async function createNote(body: NoteCreate): Promise<NoteResponse> {
  const { data } = await apiClient.post<NoteResponse>('/notes', body)
  return data
}

export async function updateNote(id: string, body: NoteUpdate): Promise<NoteResponse> {
  const { data } = await apiClient.patch<NoteResponse>(`/notes/${id}`, body)
  return data
}

export async function deleteNote(id: string): Promise<void> {
  await apiClient.delete(`/notes/${id}`)
}
