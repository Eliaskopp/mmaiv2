from pydantic import BaseModel


class ServiceHealth(BaseModel):
    status: str
    latency_ms: int


class HealthResponse(BaseModel):
    status: str
    version: str
    database: ServiceHealth
    ai: ServiceHealth
