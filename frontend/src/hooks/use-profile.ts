import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getProfile, createProfile, updateProfile } from '../services/profile'
import type { ProfileCreate, ProfileUpdate } from '../types'

export const PROFILE_KEY = ['profile'] as const

export function useProfile() {
  return useQuery({
    queryKey: PROFILE_KEY,
    queryFn: getProfile,
    staleTime: 60_000,
  })
}

export function useCreateProfile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: ProfileCreate) => createProfile(body),
    onSuccess: (data) => {
      queryClient.setQueryData(PROFILE_KEY, data)
    },
  })
}

export function useUpdateProfile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: ProfileUpdate) => updateProfile(body),
    onSuccess: (data) => {
      queryClient.setQueryData(PROFILE_KEY, data)
    },
  })
}
