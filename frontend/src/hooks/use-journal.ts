import { useQuery, useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { InfiniteData } from '@tanstack/react-query'
import {
  getSessions,
  getSession,
  createSession,
  updateSession,
  deleteSession,
} from '../services/journal'
import type { SessionFilters } from '../services/journal'
import type { SessionCreate, SessionUpdate, SessionListResponse, SessionResponse } from '../types'

export const SESSIONS_KEY = ['sessions'] as const

const PAGE_SIZE = 20

export function useJournalSessions(filters?: SessionFilters) {
  return useQuery({
    queryKey: [...SESSIONS_KEY, filters] as const,
    queryFn: () => getSessions(filters),
    staleTime: 30_000,
  })
}

export function useInfiniteJournalSessions(
  filters?: Omit<SessionFilters, 'offset' | 'limit'>,
) {
  return useInfiniteQuery({
    queryKey: [...SESSIONS_KEY, 'infinite', filters] as const,
    queryFn: ({ pageParam = 0 }) =>
      getSessions({ ...filters, offset: pageParam, limit: PAGE_SIZE }),
    initialPageParam: 0,
    getNextPageParam: (lastPage, _allPages, lastPageParam) => {
      const nextOffset = (lastPageParam as number) + PAGE_SIZE
      return nextOffset < lastPage.total ? nextOffset : undefined
    },
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
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: SESSIONS_KEY })
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

type InfiniteSessionData = InfiniteData<SessionListResponse, number>

export function useUpdateJournalSession() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: SessionUpdate }) => updateSession(id, body),
    onMutate: async ({ id, body }) => {
      // Cancel in-flight fetches so they don't overwrite our optimistic update
      await queryClient.cancelQueries({ queryKey: SESSIONS_KEY })

      // Snapshot every infinite-query cache entry for rollback
      const previousData = queryClient.getQueriesData<InfiniteSessionData>({
        queryKey: [...SESSIONS_KEY, 'infinite'],
      })

      // Deep-map: replace the edited item in-place (array length stays constant)
      queryClient.setQueriesData<InfiniteSessionData>(
        { queryKey: [...SESSIONS_KEY, 'infinite'] },
        (old) => {
          if (!old) return old
          return {
            ...old,
            pages: old.pages.map((page) => ({
              ...page,
              items: page.items.map((item) =>
                item.id === id
                  ? { ...item, ...body } as SessionResponse
                  : item,
              ),
            })),
          }
        },
      )

      return { previousData }
    },
    onError: (_err, _vars, context) => {
      // Rollback to snapshot on failure
      if (context?.previousData) {
        for (const [key, data] of context.previousData) {
          queryClient.setQueryData(key, data)
        }
      }
    },
    onSettled: () => {
      // Always refetch for server truth
      queryClient.invalidateQueries({ queryKey: SESSIONS_KEY })
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

export function useDeleteJournalSession() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteSession(id),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: SESSIONS_KEY })
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}
