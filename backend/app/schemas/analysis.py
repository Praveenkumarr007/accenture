from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AnomalySchema(BaseModel):
    id: int
    kpi_name: str
    date: datetime
    current_value: Optional[float] = None
    expected_value: Optional[float] = None
    deviation: Optional[float] = None
    z_score: Optional[float] = None
    severity: Optional[str] = None
    method: Optional[str] = None

    class Config:
        from_attributes = True

class DriverSchema(BaseModel):
    id: int
    name: str
    contribution_percent: float
    confidence: Optional[float] = None
    direction: Optional[str] = None
    metric_affected: Optional[str] = None
    previous_value: Optional[float] = None
    current_value: Optional[float] = None
    change_percent: Optional[float] = None
    evidence_summary: Optional[Dict[str, Any]] = None
    data_source: Optional[str] = None
    calculation_method: Optional[str] = None
    rank: Optional[int] = None

    class Config:
        from_attributes = True

class EvidenceSchema(BaseModel):
    id: int
    source: str
    source_table: Optional[str] = None
    metric_name: str
    metric_value: Optional[float] = None
    previous_value: Optional[float] = None
    change_percent: Optional[float] = None
    timestamp: Optional[datetime] = None
    analytical_method: Optional[str] = None
    data_freshness: Optional[str] = None
    confidence: Optional[float] = None

    class Config:
        from_attributes = True

class RecommendationSchema(BaseModel):
    id: int
    driver_name: Optional[str] = None
    lever: Optional[str] = None
    action: str
    expected_impact: Optional[str] = None
    expected_impact_value: Optional[float] = None
    owner: Optional[str] = None
    owner_role: Optional[str] = None
    confidence: Optional[float] = None
    priority: Optional[str] = None
    monitoring_plan: Optional[str] = None

    class Config:
        from_attributes = True

class ConfidenceSchema(BaseModel):
    score: float
    level: str
    factors: Dict[str, float]
    data_completeness: float
    data_freshness_score: float
    statistical_strength: float
    source_corroboration: float

class AlternativeHypothesis(BaseModel):
    description: str
    confidence: float
    supporting_evidence: List[str] = []

class InsightSchema(BaseModel):
    id: int
    kpi_name: str
    title: Optional[str] = None
    summary: Optional[str] = None
    narrative: Optional[str] = None
    persona_narrative: Optional[Dict[str, str]] = None
    priority: Optional[str] = None
    priority_score: Optional[float] = None
    confidence: Optional[float] = None
    confidence_level: Optional[str] = None
    status: Optional[str] = "active"
    abstained: bool = False
    abstention_reason: Optional[str] = None
    contradiction_detected: bool = False
    contradiction_details: Optional[str] = None
    alternative_hypotheses: Optional[List[AlternativeHypothesis]] = None
    current_value: Optional[float] = None
    previous_value: Optional[float] = None
    change_percent: Optional[float] = None
    baseline_value: Optional[float] = None
    drivers: List[DriverSchema] = []
    evidence: List[EvidenceSchema] = []
    recommendations: List[RecommendationSchema] = []
    data_sources_checked: Optional[List[str]] = None
    persona: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
