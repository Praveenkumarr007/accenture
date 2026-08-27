from fastapi import APIRouter
from app.core.database import SessionLocal
from app.models.models import DataSource

router = APIRouter()


@router.get("")
def list_data_sources():
    db = SessionLocal()
    try:
        sources = db.query(DataSource).all()
        return [
            {"id": s.id, "name": s.name, "type": s.type, "status": s.status,
             "last_updated": s.last_updated.isoformat() if s.last_updated else None,
             "refresh_frequency": s.refresh_frequency, "row_count": s.row_count,
             "coverage_days": s.coverage_days, "quality_score": s.quality_score}
            for s in sources
        ]
    finally:
        db.close()
