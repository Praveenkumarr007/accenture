from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from datetime import datetime
from app.core.database import Base


class DataSource(Base):
    __tablename__ = "data_sources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)
    status = Column(String(50), default="healthy")
    last_updated = Column(DateTime, nullable=True)
    refresh_frequency = Column(String(50), nullable=True)
    row_count = Column(Integer, default=0)
    data_quality_score = Column(Float, default=1.0)
    coverage_days = Column(Integer, default=90)
    description = Column(Text, nullable=True)
