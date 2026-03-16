export interface ServiceHealth {
  status: string
  latency_ms: number
}

export interface HealthResponse {
  status: string
  version: string
  database: ServiceHealth
  ai: ServiceHealth
}
