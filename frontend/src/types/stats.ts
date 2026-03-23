export interface ACWRResponse {
  acute_load: number
  chronic_load: number
  acwr_ratio: number | null
  risk_zone: string
  is_calibrating: boolean
}

export interface DailyVolumePoint {
  date: string
  total_load: number
  total_duration: number
}
