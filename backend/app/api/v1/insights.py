from fastapi import APIRouter
from app.core.database import SessionLocal
from app.engines.insight_engine import run_full_analysis
from app.models.models import Insight, Anomaly, Driver, Evidence

router = APIRouter()


@router.get("")
def list_insights(persona: str = "CEO"):
    db = SessionLocal()
    try:
        insights = db.query(Insight).order_by(Insight.created_at.desc()).limit(20).all()
        result = []
        for ins in insights:
            anomaly = db.query(Anomaly).filter(Anomaly.id == ins.anomaly_id).first()
            drivers = db.query(Driver).filter(Driver.anomaly_id == ins.anomaly_id).order_by(Driver.rank).all()
            evidence = db.query(Evidence).filter(Evidence.insight_id == ins.id).all()
            result.append({
                "id": ins.id, "anomaly_id": ins.anomaly_id, "title": ins.title,
                "narrative": ins.narrative, "persona": ins.persona,
                "confidence": ins.confidence, "confidence_level": ins.confidence_level,
                "status": ins.status, "is_abstained": ins.is_abstained,
                "abstention_reason": ins.abstention_reason,
                "alternative_hypotheses": ins.alternative_hypotheses or [],
                "created_at": ins.created_at.isoformat() if ins.created_at else "",
                "kpi_name": anomaly.kpi_name if anomaly else "",
                "current_value": anomaly.current_value if anomaly else 0,
                "previous_value": anomaly.previous_value if anomaly else 0,
                "change_percent": round(((anomaly.current_value - anomaly.previous_value) / anomaly.previous_value * 100) if anomaly and anomaly.previous_value else 0, 1),
                "drivers": [{"id": d.id, "name": d.name, "contribution_percent": d.contribution_percent,
                    "confidence": d.confidence, "evidence_summary": d.evidence_summary, "rank": d.rank,
                    "category": d.category, "data_source": d.data_source,
                    "affected_products": d.affected_products or [], "affected_regions": d.affected_regions or [],
                    "calculation_method": d.calculation_method} for d in drivers],
                "evidence": [{"id": e.id, "source": e.source,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "metric": e.metric, "value": e.value, "previous_value": e.previous_value,
                    "change_percent": e.change_percent, "analytical_method": e.analytical_method,
                    "data_quality": e.data_quality, "detail": e.detail} for e in evidence],
            })
        return result
    finally:
        db.close()


@router.get("/{insight_id}")
def get_insight(insight_id: int):
    db = SessionLocal()
    try:
        ins = db.query(Insight).filter(Insight.id == insight_id).first()
        if not ins:
            return {"error": "Insight not found"}
        anomaly = db.query(Anomaly).filter(Anomaly.id == ins.anomaly_id).first()
        drivers = db.query(Driver).filter(Driver.anomaly_id == ins.anomaly_id).order_by(Driver.rank).all()
        evidence = db.query(Evidence).filter(Evidence.insight_id == ins.id).all()
        return {
            "id": ins.id, "anomaly_id": ins.anomaly_id, "title": ins.title,
            "narrative": ins.narrative, "persona": ins.persona,
            "confidence": ins.confidence, "confidence_level": ins.confidence_level,
            "status": ins.status, "is_abstained": ins.is_abstained,
            "abstention_reason": ins.abstention_reason,
            "alternative_hypotheses": ins.alternative_hypotheses or [],
            "created_at": ins.created_at.isoformat() if ins.created_at else "",
            "kpi_name": anomaly.kpi_name if anomaly else "",
            "current_value": anomaly.current_value if anomaly else 0,
            "previous_value": anomaly.previous_value if anomaly else 0,
            "change_percent": round(((anomaly.current_value - anomaly.previous_value) / anomaly.previous_value * 100) if anomaly and anomaly.previous_value else 0, 1),
            "drivers": [{"id": d.id, "name": d.name, "contribution_percent": d.contribution_percent,
                "confidence": d.confidence, "evidence_summary": d.evidence_summary, "rank": d.rank,
                "category": d.category, "data_source": d.data_source,
                "affected_products": d.affected_products or [], "affected_regions": d.affected_regions or [],
                "calculation_method": d.calculation_method} for d in drivers],
            "evidence": [{"id": e.id, "source": e.source,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "metric": e.metric, "value": e.value, "previous_value": e.previous_value,
                "change_percent": e.change_percent, "analytical_method": e.analytical_method,
                "data_quality": e.data_quality, "detail": e.detail} for e in evidence],
        }
    finally:
        db.close()


@router.post("/analyze/{kpi_name}")
def analyze_kpi(kpi_name: str, persona: str = "CEO"):
    db = SessionLocal()
    try:
        return run_full_analysis(db, kpi_name, persona)
    finally:
        db.close()
