from pydantic import BaseModel


class ACWRResponse(BaseModel):
    acute_load: float
    chronic_load: float
    acwr_ratio: float | None
    risk_zone: str
    is_calibrating: bool
    session_count: int


class DailyVolumePoint(BaseModel):
    date: str
    total_load: float
    total_duration: int
