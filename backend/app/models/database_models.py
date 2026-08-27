"""SQLAlchemy database models"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserRole(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    permissions = Column(JSON, default=list)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100))
    role_name = Column(String(50), ForeignKey("roles.name"), nullable=False, default="viewer")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime)


class DataSource(Base):
    __tablename__ = "data_sources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    source_type = Column(String(50), nullable=False)
    status = Column(String(20), default="healthy")
    last_updated = Column(DateTime)
    refresh_frequency = Column(String(50))
    row_count = Column(Integer, default=0)
    data_quality_score = Column(Float, default=1.0)
    coverage_days = Column(Integer, default=90)
    connection_config = Column(JSON, default=dict)
    description = Column(Text)


class KPIDefinition(Base):
    __tablename__ = "kpi_definitions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    formula = Column(Text, nullable=False)
    data_source = Column(String(100))
    refresh_frequency = Column(String(50))
    threshold_percent = Column(Float, default=10.0)
    owner = Column(String(100))
    allowed_roles = Column(JSON, default=list)
    dimensions = Column(JSON, default=list)
    business_meaning = Column(Text)
    lineage = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class KPIValue(Base):
    __tablename__ = "kpi_values"
    id = Column(Integer, primary_key=True, index=True)
    kpi_name = Column(String(100), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=False)
    previous_value = Column(Float)
    change_percent = Column(Float)
    baseline_value = Column(Float)
    baseline_period = Column(String(50))
    dimension = Column(String(100))
    dimension_value = Column(String(200))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Anomaly(Base):
    __tablename__ = "anomalies"
    id = Column(Integer, primary_key=True, index=True)
    kpi_name = Column(String(100), nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    current_value = Column(Float)
    expected_value = Column(Float)
    z_score = Column(Float)
    deviation_percent = Column(Float)
    detection_method = Column(String(50))
    is_significant = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Insight(Base):
    __tablename__ = "insights"
    id = Column(Integer, primary_key=True, index=True)
    kpi_name = Column(String(100), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    summary = Column(Text)
    narrative = Column(Text)
    persona = Column(String(50))
    current_value = Column(Float)
    previous_value = Column(Float)
    change_percent = Column(Float)
    priority = Column(String(20))
    confidence_score = Column(Float, default=0.0)
    confidence_level = Column(String(20))
    status = Column(String(30), default="active")
    evidence_data = Column(JSON, default=list)
    alternative_hypotheses = Column(JSON, default=list)
    abstention_reason = Column(Text)
    is_abstained = Column(Boolean, default=False)
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    drivers = relationship("Driver", back_populates="insight", order_by="Driver.rank")
    recommendations = relationship("Recommendation", back_populates="insight")
    feedbacks = relationship("Feedback", back_populates="insight")


class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True, index=True)
    insight_id = Column(Integer, ForeignKey("insights.id"), nullable=False)
    name = Column(String(200), nullable=False)
    contribution_percent = Column(Float, nullable=False)
    confidence = Column(Float, default=0.0)
    evidence_summary = Column(Text)
    supporting_data = Column(JSON, default=dict)
    rank = Column(Integer)
    is_primary = Column(Boolean, default=False)
    data_source = Column(String(100))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    insight = relationship("Insight", back_populates="drivers")


class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True, index=True)
    insight_id = Column(Integer, ForeignKey("insights.id"), nullable=False)
    source_name = Column(String(100), nullable=False)
    metric_name = Column(String(100))
    metric_value = Column(Float)
    previous_metric_value = Column(Float)
    change_percent = Column(Float)
    timestamp = Column(DateTime)
    analytical_method = Column(String(100))
    data_lineage = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, index=True)
    insight_id = Column(Integer, ForeignKey("insights.id"), nullable=False)
    driver_name = Column(String(200))
    lever = Column(String(200))
    action = Column(Text, nullable=False)
    expected_impact = Column(Text)
    expected_impact_value = Column(Float)
    owner = Column(String(100))
    confidence = Column(Float, default=0.0)
    monitoring_plan = Column(Text)
    priority = Column(String(20), default="medium")
    status = Column(String(30), default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    insight = relationship("Insight", back_populates="recommendations")


class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    insight_id = Column(Integer, ForeignKey("insights.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(String(20), nullable=False)
    feedback_type = Column(String(50))
    correction = Column(Text)
    persona = Column(String(50))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    insight = relationship("Insight", back_populates="feedbacks")
    user = relationship("User")


class LLMLog(Base):
    __tablename__ = "llm_logs"
    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String(50))
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    model = Column(String(50))
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Telemetry(Base):
    __tablename__ = "telemetry"
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    extra_metadata = Column("extra_metadata", JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Lineage(Base):
    __tablename__ = "lineage"
    id = Column(Integer, primary_key=True, index=True)
    source_system = Column(String(100), nullable=False)
    source_table = Column(String(100))
    transformation = Column(String(200))
    target_kpi = Column(String(100))
    target_insight_id = Column(Integer, ForeignKey("insights.id"))
    description = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
