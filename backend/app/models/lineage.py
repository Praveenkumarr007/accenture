from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from app.core.database import Base


class LineageNode(Base):
    __tablename__ = "lineage_nodes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)
    metadata_ = Column("metadata", JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class LineageEdge(Base):
    __tablename__ = "lineage_edges"
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, nullable=False)
    target_id = Column(Integer, nullable=False)
    label = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
