from pydantic import BaseModel, Field, field_validator
from typing import Optional
import time

class Event(BaseModel):
    """
    Compact activity event.
    """
    ts: int = Field(..., description="Epoch milliseconds")
    app: str = Field(..., min_length=1, max_length=128)
    window: Optional[str] = Field(None, max_length=256)
    idle: bool = Field(...)
    focus_secs: int = Field(..., ge=0, le=3600)

    @field_validator("ts")
    @classmethod
    def _ts_reasonable(cls, v: int):
        # Must be within +/- 365 days of 'now' to prevent nonsense
        now_ms = int(time.time() * 1000)
        if abs(now_ms - v) > 365 * 24 * 3600 * 1000:
            raise ValueError("timestamp too far from current time")
        return v
