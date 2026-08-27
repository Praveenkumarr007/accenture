from fastapi import APIRouter
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.engines.insight_engine import run_full_analysis
from app.schemas.schemas import ReportRequest

router = APIRouter()


@router.post("/generate")
def generate_report(request: ReportRequest):
    db = SessionLocal()
    try:
        analysis = run_full_analysis(db, request.kpi_name, request.persona)
        report = {
            "title": f"{request.kpi_name} Intelligence Report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "persona": request.persona,
            "executive_summary": analysis.get("narrative", ""),
            "kpi_movement": {"name": analysis.get("kpi_name"), "current_value": analysis.get("current_value"),
                "previous_value": analysis.get("previous_value"), "change_percent": analysis.get("change_percent"),
                "priority_level": analysis.get("priority_level")},
            "confidence": analysis.get("confidence", {}),
            "is_abstained": analysis.get("is_abstained", False),
            "abstention_reason": analysis.get("abstention_reason"),
        }
        if request.include_evidence:
            report["drivers"] = analysis.get("drivers", [])
            report["evidence"] = analysis.get("evidence", [])
            report["alternative_hypotheses"] = analysis.get("alternative_hypotheses", [])
        if request.include_recommendations:
            report["recommendations"] = analysis.get("recommendations", [])
        return report
    finally:
        db.close()
