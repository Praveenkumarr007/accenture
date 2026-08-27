"""Pydantic schemas"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role_name: str
    is_active: bool
    class Config:
        from_attributes = True


class DataSourceResponse(BaseModel):
    id: int
    name: str
    source_type: str
    status: str
    last_updated: Optional[datetime] = None
    refresh_frequency: Optional[str] = None
    row_count: int = 0
    data_quality_score: float = 1.0
    coverage_days: int = 90
    description: Optional[str] = None
    class Config:
        from_attributes = True


class KPIDefinitionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    formula: str
    data_source: Optional[str] = None
    refresh_frequency: Optional[str] = None
    threshold_percent: float = 10.0
    owner: Optional[str] = None
    allowed_roles: list[str] = []
    dimensions: list[str] = []
    business_meaning: Optional[str] = None
    lineage: dict = {}
    is_active: bool = True
    class Config:
        from_attributes = True


class KPICardResponse(BaseModel):
    id: str
    name: str
    value: float
    change_percent: Optional[float] = None
    previous_value: Optional[float] = None
    priority: Optional[str] = None
    status: str = "normal"
    trend: list[float] = []
    class Config:
        from_attributes = True


class InsightResponse(BaseModel):
    id: int
    kpi_name: str
    title: str
    summary: Optional[str] = None
    narrative: Optional[str] = None
    persona: Optional[str] = None
    current_value: Optional[float] = None
    previous_value: Optional[float] = None
    change_percent: Optional[float] = None
    priority: Optional[str] = None
    confidence_score: float = 0.0
    confidence_level: Optional[str] = None
    status: str = "active"
    evidence_data: list[dict] = []
    alternative_hypotheses: list[dict] = []
    abstention_reason: Optional[str] = None
    is_abstained: bool = False
    date: datetime
    created_at: datetime
    drivers: list[dict] = []
    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    id: int
    driver_name: Optional[str] = None
    lever: Optional[str] = None
    action: str
    expected_impact: Optional[str] = None
    expected_impact_value: Optional[float] = None
    owner: Optional[str] = None
    confidence: float = 0.0
    monitoring_plan: Optional[str] = None
    priority: str = "medium"
    status: str = "pending"
    class Config:
        from_attributes = True


class FeedbackRequest(BaseModel):
    insight_id: int
    rating: str = Field(..., pattern="^(correct|incorrect)$")
    feedback_type: Optional[str] = None
    correction: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    insight_id: int
    user_id: int
    rating: str
    feedback_type: Optional[str] = None
    correction: Optional[str] = None
    persona: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


class FeedbackDashboard(BaseModel):
    total_feedback: int = 0
    positive_count: int = 0
    negative_count: int = 0
    most_common_correction: Optional[str] = None
    feedback_trend: list[dict] = []


class AssistantRequest(BaseModel):
    message: str
    persona: str = "CEO"


class AssistantResponse(BaseModel):
    response: str
    evidence_used: list[dict] = []
    confidence: float = 0.0
    data_sources_consulted: list[str] = []


class TelemetryResponse(BaseModel):
    average_latency_ms: float = 0.0
    total_llm_calls: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    success_rate: float = 100.0
    cache_hits: int = 0
    failed_requests: int = 0


class LineageResponse(BaseModel):
    id: int
    source_system: str
    source_table: Optional[str] = None
    transformation: Optional[str] = None
    target_kpi: Optional[str] = None
    description: Optional[str] = None
    class Config:
        from_attributes = True


class ScenarioSwitchRequest(BaseModel):
    scenario: str
