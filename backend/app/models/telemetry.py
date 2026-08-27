from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Text
from datetime import datetime
from app.core.database import Base


class LLMLog(Base):
    __tablename__ = "llm_logs"
    id = Column(Integer, primary_key=True, index=True)
    operation = Column(String(100), nullable=False)
    model = Column(String(100))
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    latency_ms = Column(Float)
    success = Column(Integer, default=1)
    error = Column(Text)
    request_payload = Column(JSON)
    response_payload = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class TelemetryEntryModel(Base):
    __tablename__ = "telemetry_entries"
    id = Column(Integer, primary_key=True, index=True)
    operation = Column(String(100), nullable=False)
    latency_ms = Column(Float)
    llm_calls = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    success = Column(Integer, default=1)
    cache_hit = Column(Integer, default=0)
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
