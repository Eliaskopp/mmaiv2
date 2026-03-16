import apiClient from './api-client'
import type { ProfileCreate, ProfileUpdate, ProfileResponse } from '../types'

export async function getProfile(): Promise<ProfileResponse> {
  const { data } = await apiClient.get<ProfileResponse>('/profile')
  return data
}

export async function createProfile(body: ProfileCreate): Promise<ProfileResponse> {
  const { data } = await apiClient.post<ProfileResponse>('/profile', body)
  return data
}

export async function updateProfile(body: ProfileUpdate): Promise<ProfileResponse> {
  const { data } = await apiClient.patch<ProfileResponse>('/profile', body)
  return data
}
