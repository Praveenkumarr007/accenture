from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DataSourceSchema(BaseModel):
    id: int
    name: str
    type: str
    status: str
    last_updated: Optional[datetime] = None
    refresh_frequency: Optional[str] = None
    row_count: int = 0
    coverage_days: int = 0
    data_quality_score: float = 100.0

    class Config:
        from_attributes = True
