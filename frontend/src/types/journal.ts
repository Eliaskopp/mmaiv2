export type SessionType =
  | 'muay_thai'
  | 'bjj_gi'
  | 'bjj_nogi'
  | 'boxing'
  | 'mma'
  | 'wrestling'
  | 'conditioning'
  | 'strength'
  | 'other'

export type SessionSource = 'manual' | 'voice' | 'ai'

export interface SessionCreate {
  session_type: SessionType
  session_date?: string | null
  title?: string | null
  notes?: string | null
  duration_minutes?: number | null
  rounds?: number | null
  round_duration_minutes?: number | null
  intensity_rpe?: number | null
  mood_before?: number | null
  mood_after?: number | null
  energy_level?: number | null
  techniques?: string[] | null
  training_partner?: string | null
  gym_name?: string | null
  source?: SessionSource
}

export interface SessionUpdate {
  session_type?: SessionType
  session_date?: string | null
  title?: string | null
  notes?: string | null
  duration_minutes?: number | null
  rounds?: number | null
  round_duration_minutes?: number | null
  intensity_rpe?: number | null
  mood_before?: number | null
  mood_after?: number | null
  energy_level?: number | null
  techniques?: string[] | null
  training_partner?: string | null
  gym_name?: string | null
  source?: SessionSource
}

export interface SessionResponse {
  id: string
  user_id: string
  session_type: string
  session_date: string
  title: string | null
  notes: string | null
  duration_minutes: number | null
  rounds: number | null
  round_duration_minutes: number | null
  intensity_rpe: number | null
  mood_before: number | null
  mood_after: number | null
  energy_level: number | null
  techniques: string[] | null
  training_partner: string | null
  gym_name: string | null
  source: string
  exertion_load: number | null
  created_at: string
  updated_at: string | null
}

export interface SessionListResponse {
  items: SessionResponse[]
  total: number
  offset: number
  limit: number
}
