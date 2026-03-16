import apiClient from './api-client'
import type { AuthResponse, LoginRequest, RegisterRequest, User } from '../types/auth'

export async function login(data: LoginRequest): Promise<AuthResponse> {
  const resp = await apiClient.post<AuthResponse>('/auth/login', data)
  return resp.data
}

export async function register(data: RegisterRequest): Promise<AuthResponse> {
  const resp = await apiClient.post<AuthResponse>('/auth/register', data)
  return resp.data
}

export async function getMe(): Promise<User> {
  const resp = await apiClient.get<User>('/auth/me')
  return resp.data
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout')
}
