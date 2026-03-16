export type NoteType = 'technique' | 'drill' | 'goal' | 'gear' | 'gym' | 'insight'
export type NoteStatus = 'active' | 'archived'
export type NoteSource = 'ai' | 'manual'

export interface NoteCreate {
  type: NoteType
  title: string
  summary?: string | null
  user_notes?: string | null
}

export interface NoteUpdate {
  title?: string | null
  summary?: string | null
  user_notes?: string | null
  status?: NoteStatus | null
  pinned?: boolean | null
}

export interface NoteResponse {
  id: string
  user_id: string
  type: string
  title: string
  summary: string | null
  user_notes: string | null
  status: string
  pinned: boolean
  source: string
  source_conversation_id: string | null
  created_at: string
  updated_at: string | null
}

export interface NoteListResponse {
  items: NoteResponse[]
  total: number
  offset: number
  limit: number
}
