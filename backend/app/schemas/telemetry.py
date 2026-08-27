from pydantic import BaseModel
from typing import List, Dict, Any

class TelemetrySummary(BaseModel):
    total_requests: int
    failed_requests: int
    success_rate: float
    average_latency_ms: float
    total_llm_calls: int
    total_tokens: int
    estimated_cost: float
    cache_hits: int
    cache_hit_rate: float

class LLMLogSchema(BaseModel):
    id: int
    operation: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    latency_ms: float
    success: bool

    class Config:
        from_attributes = True
