from fastapi import APIRouter
from app.core.database import SessionLocal
from app.models.models import Driver

router = APIRouter()


@router.get("")
def list_drivers(anomaly_id: int = None):
    db = SessionLocal()
    try:
        query = db.query(Driver)
        if anomaly_id:
            query = query.filter(Driver.anomaly_id == anomaly_id)
        drivers = query.order_by(Driver.rank).all()
        return [
            {"id": d.id, "anomaly_id": d.anomaly_id, "name": d.name,
             "contribution_percent": d.contribution_percent, "confidence": d.confidence,
             "evidence_summary": d.evidence_summary, "rank": d.rank, "category": d.category,
             "data_source": d.data_source, "affected_products": d.affected_products or [],
             "affected_regions": d.affected_regions or [], "calculation_method": d.calculation_method}
            for d in drivers
        ]
    finally:
        db.close()


@router.get("/{driver_id}")
def get_driver(driver_id: int):
    db = SessionLocal()
    try:
        d = db.query(Driver).filter(Driver.id == driver_id).first()
        if not d:
            return {"error": "Driver not found"}
        return {"id": d.id, "name": d.name, "contribution_percent": d.contribution_percent,
                "confidence": d.confidence, "evidence_summary": d.evidence_summary,
                "rank": d.rank, "category": d.category, "data_source": d.data_source,
                "affected_products": d.affected_products or [], "affected_regions": d.affected_regions or [],
                "calculation_method": d.calculation_method}
    finally:
        db.close()
