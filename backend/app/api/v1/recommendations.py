from fastapi import APIRouter
from app.core.database import SessionLocal
from app.models.models import Recommendation

router = APIRouter()


@router.get("")
def list_recommendations(insight_id: int = None, persona: str = None):
    db = SessionLocal()
    try:
        query = db.query(Recommendation)
        if insight_id:
            query = query.filter(Recommendation.insight_id == insight_id)
        if persona:
            query = query.filter(Recommendation.persona == persona)
        recs = query.order_by(Recommendation.created_at.desc()).limit(20).all()
        return [
            {"id": r.id, "insight_id": r.insight_id, "driver_name": r.driver_name,
             "lever": r.lever, "action": r.action, "expected_impact": r.expected_impact,
             "expected_impact_value": r.expected_impact_value, "owner": r.owner,
             "confidence": r.confidence, "monitoring_plan": r.monitoring_plan,
             "priority": r.priority, "persona": r.persona,
             "created_at": r.created_at.isoformat() if r.created_at else ""}
            for r in recs
        ]
    finally:
        db.close()
