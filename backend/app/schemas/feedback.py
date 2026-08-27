from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FeedbackCreate(BaseModel):
    insight_id: int
    rating: str
    feedback_type: Optional[str] = None
    correction: Optional[str] = None
    persona: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    insight_id: int
    user_id: Optional[int] = None
    rating: str
    feedback_type: Optional[str] = None
    correction: Optional[str] = None
    persona: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FeedbackSummary(BaseModel):
    total: int
    positive: int
    negative: int
    positive_rate: float
    common_corrections: list
    recent_trend: list
