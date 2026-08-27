from fastapi import APIRouter
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.models import LLMLog

router = APIRouter()


@router.get("")
def get_telemetry():
    db = SessionLocal()
    try:
        llm_calls = db.query(func.count(LLMLog.id)).scalar() or 0
        total_tokens = db.query(func.sum(LLMLog.tokens_used)).scalar() or 0
        total_cost = db.query(func.sum(LLMLog.estimated_cost)).scalar() or 0
        avg_latency = db.query(func.avg(LLMLog.latency_ms)).scalar() or 0
        failed = db.query(func.count(LLMLog.id)).filter(LLMLog.success == False).scalar() or 0
        cache_hits = db.query(func.count(LLMLog.id)).filter(LLMLog.cached == True).scalar() or 0
        success_rate = ((llm_calls - failed) / llm_calls * 100) if llm_calls > 0 else 100.0
        return {"avg_latency_ms": round(avg_latency, 1), "llm_calls": llm_calls,
                "tokens_used": int(total_tokens), "estimated_cost": round(total_cost, 4),
                "success_rate": round(success_rate, 1), "cache_hits": cache_hits, "failed_requests": failed}
    finally:
        db.close()


@router.get("/history")
def telemetry_history():
    return []
