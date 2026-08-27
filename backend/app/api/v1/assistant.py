from fastapi import APIRouter
from app.core.database import SessionLocal
from app.schemas.schemas import AssistantRequest
from app.llm.llm_service import generate_assistant_response
from app.engines.insight_engine import run_full_analysis
from app.models.models import LLMLog

router = APIRouter()


@router.post("")
def chat_with_assistant(request: AssistantRequest):
    db = SessionLocal()
    try:
        analysis = run_full_analysis(db, "revenue", request.persona)
        context = {
            "kpi_name": analysis.get("kpi_name", "Revenue"),
            "current_value": analysis.get("current_value", 0),
            "previous_value": analysis.get("previous_value", 0),
            "change_percent": analysis.get("change_percent", 0),
            "confidence": analysis.get("confidence", {}).get("confidence", 0) if isinstance(analysis.get("confidence"), dict) else analysis.get("confidence", 0),
            "drivers": analysis.get("drivers", []),
            "evidence": analysis.get("evidence", []),
        }
        response = generate_assistant_response(request.message, context, request.persona)
        db.add(LLMLog(request_type="assistant", tokens_used=response.get("tokens_used", 0),
                       estimated_cost=response.get("estimated_cost", 0), latency_ms=response.get("latency_ms", 0),
                       cached=response.get("cached", False), success=True))
        db.commit()
        return {"response": response.get("response", ""), "evidence_used": response.get("evidence_used", []),
                "confidence": response.get("confidence", context.get("confidence", 0))}
    except Exception as e:
        return {"response": f"Error: {str(e)}", "evidence_used": [], "confidence": 0}
    finally:
        db.close()
