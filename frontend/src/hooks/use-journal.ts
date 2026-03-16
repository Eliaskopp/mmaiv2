import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getSessions,
  getSession,
  createSession,
  updateSession,
  deleteSession,
} from '../services/journal'
import type { SessionFilters } from '../services/journal'
import type { SessionCreate, SessionUpdate } from '../types'

export const SESSIONS_KEY = ['sessions'] as const

export function useJournalSessions(filters?: SessionFilters) {
  return useQuery({
    queryKey: [...SESSIONS_KEY, filters] as const,
    queryFn: () => getSessions(filters),
    staleTime: 30_000,
  })
}

export function useJournalSession(id: string) {
  return useQuery({
    queryKey: [...SESSIONS_KEY, id] as const,
    queryFn: () => getSession(id),
    enabled: !!id,
    staleTime: 30_000,
  })
}

export function useCreateJournalSession() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: SessionCreate) => createSession(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SESSIONS_KEY })
    },
  })
}

export function useUpdateJournalSession() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: SessionUpdate }) => updateSession(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SESSIONS_KEY })
    },
  })
}

export function useDeleteJournalSession() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteSession(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SESSIONS_KEY })
    },
  })
}
