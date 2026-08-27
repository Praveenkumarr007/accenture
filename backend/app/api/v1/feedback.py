from fastapi import APIRouter
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.models import Feedback
from app.schemas.schemas import FeedbackCreate

router = APIRouter()


@router.post("")
def create_feedback(feedback: FeedbackCreate):
    db = SessionLocal()
    try:
        fb = Feedback(insight_id=feedback.insight_id, user_id=1, feedback_type=feedback.feedback_type,
                      comment=feedback.comment, persona="CEO")
        db.add(fb)
        db.commit()
        db.refresh(fb)
        return {"id": fb.id, "status": "recorded"}
    finally:
        db.close()


@router.get("")
def list_feedback():
    db = SessionLocal()
    try:
        feedbacks = db.query(Feedback).order_by(Feedback.created_at.desc()).limit(50).all()
        return [
            {"id": f.id, "insight_id": f.insight_id, "feedback_type": f.feedback_type,
             "comment": f.comment, "persona": f.persona,
             "created_at": f.created_at.isoformat() if f.created_at else ""}
            for f in feedbacks
        ]
    finally:
        db.close()


@router.get("/dashboard")
def feedback_dashboard():
    db = SessionLocal()
    try:
        total = db.query(func.count(Feedback.id)).scalar() or 0
        positive = db.query(func.count(Feedback.id)).filter(Feedback.feedback_type == "correct").scalar() or 0
        negative = db.query(func.count(Feedback.id)).filter(
            Feedback.feedback_type.in_(["incorrect_driver", "incorrect_recommendation"])).scalar() or 0
        most_common = db.query(Feedback.feedback_type, func.count(Feedback.id).label("cnt")
                              ).group_by(Feedback.feedback_type).order_by(func.count(Feedback.id).desc()).first()
        recent = db.query(Feedback).order_by(Feedback.created_at.desc()).limit(10).all()
        return {
            "total_feedback": total, "positive_count": positive, "negative_count": negative,
            "most_common_correction": most_common[0] if most_common else None,
            "recent_feedback": [{"id": f.id, "insight_id": f.insight_id, "feedback_type": f.feedback_type,
                "comment": f.comment, "persona": f.persona,
                "created_at": f.created_at.isoformat() if f.created_at else ""} for f in recent],
        }
    finally:
        db.close()
