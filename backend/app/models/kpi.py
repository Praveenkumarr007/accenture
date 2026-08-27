from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON
from datetime import datetime
from app.core.database import Base


class KPIDefinition(Base):
    __tablename__ = "kpi_definitions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    formula = Column(String(500))
    data_source = Column(String(100))
    refresh_frequency = Column(String(50))
    threshold_percent = Column(Float, default=10.0)
    owner = Column(String(100))
    allowed_roles = Column(JSON, default=[])
    dimensions = Column(JSON, default=[])
    business_meaning = Column(Text)
    lineage = Column(JSON, default={})
    is_active = Column(Integer, default=1)


class KPIValue(Base):
    __tablename__ = "kpi_values"
    id = Column(Integer, primary_key=True, index=True)
    kpi_name = Column(String(100), nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    value = Column(Float, nullable=False)
    dimension = Column(String(100))
    dimension_value = Column(String(255))
    granularity = Column(String(50), default="daily")
