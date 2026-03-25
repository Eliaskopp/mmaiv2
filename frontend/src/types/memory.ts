// Maps to PerformanceEventResponse (backend/app/schemas/memory.py)
// Arrays are string[] (not nullable) — service layer normalizes null → []
export interface PerformanceEvent {
  id: string
  user_id: string
  conversation_id: string | null
  event_type: string // sparring | competition | drill | open_mat
  discipline: string // NOT nullable in backend schema
  outcome: string | null // win | loss | draw | no_contest | mixed
  finish_type: string | null
  root_causes: string[] // backend sends list|None, normalized in service
  highlights: string[] // backend sends list|None, normalized in service
  opponent_description: string | null
  rpe_score: number | null
  failure_domain: string | null // technical | tactical | physical | mental
  cns_status: string | null // optimal | sluggish | depleted
  event_date: string
  extraction_confidence: number
  created_at: string
}

export interface PerformanceEventList {
  items: PerformanceEvent[]
  total: number
  offset: number
  limit: number
}

// Maps to UserTrainingStateResponse (backend/app/schemas/memory.py)
// Arrays are string[] (not nullable) — service layer normalizes null → []
export interface TrainingState {
  id: string
  user_id: string
  current_focus: string[] // backend sends list|None, normalized in service
  active_injuries: string[] // backend sends list|None, normalized in service
  short_term_goals: string[] // backend sends list|None, normalized in service
  created_at: string
  updated_at: string | null
}
