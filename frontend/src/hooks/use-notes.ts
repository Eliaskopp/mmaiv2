import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getNotes,
  getNote,
  createNote,
  updateNote,
  deleteNote,
} from '../services/notes'
import type { NoteFilters } from '../services/notes'
import type { NoteCreate, NoteUpdate } from '../types'

export const NOTES_KEY = ['notes'] as const

export function useNotes(filters?: NoteFilters) {
  return useQuery({
    queryKey: [...NOTES_KEY, filters] as const,
    queryFn: () => getNotes(filters),
    staleTime: 30_000,
  })
}

export function useNote(id: string) {
  return useQuery({
    queryKey: [...NOTES_KEY, id] as const,
    queryFn: () => getNote(id),
    enabled: !!id,
    staleTime: 30_000,
  })
}

export function useCreateNote() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: NoteCreate) => createNote(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTES_KEY })
    },
  })
}

export function useUpdateNote() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: NoteUpdate }) => updateNote(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTES_KEY })
    },
  })
}

export function useDeleteNote() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteNote(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTES_KEY })
    },
  })
}
