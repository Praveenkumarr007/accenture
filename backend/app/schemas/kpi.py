from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class KPIDefinitionSchema(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    definition: Optional[str] = None
    formula: Optional[str] = None
    data_sources: Optional[List[str]] = None
    dimensions: Optional[List[str]] = None
    refresh_frequency: Optional[str] = None
    threshold: Optional[float] = 10.0
    owner: Optional[str] = None
    allowed_roles: Optional[List[str]] = None
    business_meaning: Optional[str] = None
    unit: Optional[str] = None
    direction: Optional[str] = "higher_is_better"

    class Config:
        from_attributes = True

class KPIValueSchema(BaseModel):
    id: int
    kpi_definition_id: int
    date: datetime
    value: float
    previous_value: Optional[float] = None
    change_percent: Optional[float] = None

    class Config:
        from_attributes = True

class KPITrendPoint(BaseModel):
    date: str
    value: float
    baseline: Optional[float] = None

class KPIResponse(BaseModel):
    definition: KPIDefinitionSchema
    current: Optional[KPIValueSchema] = None
    previous: Optional[KPIValueSchema] = None
    change_percent: Optional[float] = None
    trend: List[KPITrendPoint] = []
    status: str = "normal"

class KPITrendResponse(BaseModel):
    kpi_name: str
    trend: List[KPITrendPoint]
    baseline: List[KPITrendPoint] = []
