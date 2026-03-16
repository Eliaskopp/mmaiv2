export interface RecoveryLogCreate {
  sleep_quality?: number | null
  soreness?: number | null
  energy?: number | null
  notes?: string | null
  logged_for?: string | null
}

export interface RecoveryLogResponse {
  id: string
  user_id: string
  sleep_quality: number | null
  soreness: number | null
  energy: number | null
  notes: string | null
  logged_for: string
  created_at: string
}

export interface RecoveryLogListResponse {
  items: RecoveryLogResponse[]
  total: number
  offset: number
  limit: number
}
