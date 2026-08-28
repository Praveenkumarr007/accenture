"""BusinessIntelligence.AI - FastAPI Application"""
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine, Base, get_db, SessionLocal
from app.core.security import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_role,
)
from app.models.database_models import (
    User, UserRole, DataSource, KPIDefinition, Feedback, LLMLog,
)
from app.schemas.schemas import (
    LoginRequest, TokenResponse, UserResponse, DataSourceResponse,
    KPIDefinitionResponse, FeedbackRequest, AssistantRequest, AssistantResponse,
    ScenarioSwitchRequest,
)
from app.services.data_generator import create_database
from app.services.orchestrator import AnalysisOrchestrator
from app.services.upload_service import (
    upload_csv, upload_excel, upload_sql, preview_file,
    list_uploaded_tables, delete_uploaded_table, query_table,
)
from app.services.data_mapper import detect_mapping, save_mapping, get_active_mappings, deactivate_mapping
from app.engines.kpi_engine import KPIEngine
from app.core.kpi_contracts import KPI_CONTRACTS, ROLE_KPI_ACCESS

DB_PATH = str(Path(__file__).parent.parent / "data" / "bi_intelligence.db")


def _sanitize_upload_name(name: str) -> str:
    import re
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_').lower()
    if not name:
        name = "uploaded_table"
    if not name[0].isalpha():
        name = "t_" + name
    return name


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    import sqlite3
    _conn = sqlite3.connect(DB_PATH)
    _tables = {r[0] for r in _conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    _conn.close()
    if "sales" not in _tables:
        create_database(DB_PATH)
    _seed_demo_data()
    yield


app = FastAPI(title="BusinessIntelligence.AI", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def _seed_demo_data():
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            for r in [UserRole(name="CEO", description="CEO", permissions=["all"]),
                      UserRole(name="Sales Manager", description="Sales", permissions=["revenue","orders","aov"]),
                      UserRole(name="Marketing Manager", description="Marketing", permissions=["conversion_rate","marketing_roi","orders"]),
                      UserRole(name="Supply Chain Manager", description="Supply Chain", permissions=["orders"]),
                      UserRole(name="Admin", description="Admin", permissions=["all"]),
                      UserRole(name="viewer", description="Viewer", permissions=[])]:
                db.add(r)
            db.flush()
            for u in [User(username="ceo", email="ceo@shopsmart.com", hashed_password=hash_password("demo123"), full_name="Sarah Chen", role_name="CEO"),
                      User(username="sales_mgr", email="sales@shopsmart.com", hashed_password=hash_password("demo123"), full_name="James Wilson", role_name="Sales Manager"),
                      User(username="marketing_mgr", email="marketing@shopsmart.com", hashed_password=hash_password("demo123"), full_name="Priya Patel", role_name="Marketing Manager"),
                      User(username="supply_mgr", email="supply@shopsmart.com", hashed_password=hash_password("demo123"), full_name="Michael Brown", role_name="Supply Chain Manager"),
                      User(username="admin", email="admin@shopsmart.com", hashed_password=hash_password("admin123"), full_name="Admin User", role_name="Admin")]:
                db.add(u)
            for s in [DataSource(name="Sales Database", source_type="postgresql", status="healthy", refresh_frequency="hourly", row_count=150000, data_quality_score=0.95, coverage_days=95, last_updated=datetime.now(timezone.utc), description="Sales transactions"),
                      DataSource(name="Marketing Database", source_type="postgresql", status="healthy", refresh_frequency="4_hours", row_count=8500, data_quality_score=0.92, coverage_days=90, last_updated=datetime.now(timezone.utc)-timedelta(hours=2), description="Campaign metrics"),
                      DataSource(name="Inventory Database", source_type="postgresql", status="healthy", refresh_frequency="30_minutes", row_count=25000, data_quality_score=0.88, coverage_days=95, last_updated=datetime.now(timezone.utc)-timedelta(minutes=15), description="Stock levels")]:
                db.add(s)
            for kpi_name, c in KPI_CONTRACTS.items():
                db.add(KPIDefinition(name=c["name"], description=c["description"], formula=c["formula"], data_source=c["data_source"], refresh_frequency=c["refresh_frequency"], threshold_percent=c["threshold_percent"], owner=c["owner"], allowed_roles=c["allowed_roles"], dimensions=c["dimensions"], business_meaning=c["business_meaning"], lineage=c["lineage"]))
            db.commit()
    finally:
        db.close()


def _orch():
    return AnalysisOrchestrator(DB_PATH)


def _dates():
    o = _orch()
    kpi = o.kpi_engine
    data_start, data_end = kpi.get_date_range()

    def _parse(v):
        try:
            dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)

    end_dt = _parse(data_end)
    start_dt = _parse(data_start)
    span_days = max((end_dt - start_dt).days, 1)

    # Adapt the current/previous windows to the actual data span:
    #  - 7 days of data  -> use the whole span as "current" (no prior baseline)
    #  - up to ~2 months -> 14-day windows
    #  - several months  -> 30-day windows
    #  - a year or more  -> 90-day windows
    if span_days <= 14:
        window = span_days
    elif span_days <= 60:
        window = 14
    elif span_days <= 180:
        window = 30
    else:
        window = 90

    cur_start = end_dt - timedelta(days=window)
    cur_end = end_dt
    prev_start = cur_start - timedelta(days=window)
    prev_end = cur_start - timedelta(days=1)
    trend_start = max(start_dt, end_dt - timedelta(days=min(span_days + 1, 90)))

    # use date-only strings so period boundaries never overlap in text comparisons
    def _d(dt):
        return dt.strftime("%Y-%m-%d")

    has_prior = prev_end >= start_dt

    return {
        "cur_start": _d(cur_start), "cur_end": _d(cur_end),
        "prev_start": _d(prev_start), "prev_end": _d(prev_end),
        "trend_start": _d(trend_start), "trend_end": _d(cur_end),
        "has_prior": bool(has_prior),
        "window_days": window,
        "span_days": span_days,
        "period_label": f"Last {window} days vs prior {window} days" if has_prior else f"Full data period ({start_dt:%b %d} - {end_dt:%b %d})",
    }


@app.post("/api/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(data={"sub": str(user.id), "role": user.role_name})
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    return TokenResponse(access_token=token, user=UserResponse(id=user.id, username=user.username, email=user.email, full_name=user.full_name, role_name=user.role_name, is_active=user.is_active))


@app.get("/api/user/profile", response_model=UserResponse)
def profile(current_user: User = Depends(get_current_user)):
    return UserResponse(id=current_user.id, username=current_user.username, email=current_user.email, full_name=current_user.full_name, role_name=current_user.role_name, is_active=current_user.is_active)


@app.get("/api/kpis")
def get_kpis(persona: str = "CEO", current_user: User = Depends(get_current_user)):
    o = _orch(); d = _dates(); allowed = ROLE_KPI_ACCESS.get(current_user.role_name, [])
    all_data = o.kpi_engine.calculate_all_kpis(d["cur_start"], d["cur_end"], d["prev_start"], d["prev_end"])
    cards = []
    for kpi_name, contract in KPI_CONTRACTS.items():
        if kpi_name not in allowed: continue
        kpi = all_data.get(kpi_name, {})
        change = kpi.get("change_percent")
        m = o.materiality_engine.assess_materiality(kpi_name=kpi_name, current_value=kpi.get("current",0), previous_value=kpi.get("previous",0) if change is not None else kpi.get("current",0), threshold_percent=contract["threshold_percent"])
        trend = o.kpi_engine.get_daily_trend(kpi_name, d["trend_start"], d["cur_end"])
        cards.append({"id": kpi_name, "name": contract["name"], "value": kpi.get("current",0), "previous_value": kpi.get("previous",0), "change_percent": change, "has_prior": change is not None, "priority": m["priority"], "status": "material" if m["is_material"] else "normal", "trend": [x["value"] for x in trend][-14:]})
    return {"kpi_cards": cards, "persona": persona, "period": d["period_label"], "has_prior": d["has_prior"], "date_range": {"current": f"{d['cur_start'][:10]} to {d['cur_end'][:10]}", "previous": f"{d['prev_start'][:10]} to {d['prev_end'][:10]}"}}


@app.get("/api/kpis/{kpi_id}")
def get_kpi_detail(kpi_id: str, persona: str = "CEO", current_user: User = Depends(get_current_user)):
    contract = KPI_CONTRACTS.get(kpi_id)
    if not contract: raise HTTPException(status_code=404, detail="KPI not found")
    if current_user.role_name not in contract.get("allowed_roles", []):
        raise HTTPException(status_code=403, detail=f"Access restricted. Required roles: {contract['allowed_roles']}")
    d = _dates()
    return _orch().run_full_analysis(kpi_name=kpi_id, current_start=d["cur_start"], current_end=d["cur_end"], previous_start=d["prev_start"], previous_end=d["prev_end"], persona=persona, user_role=current_user.role_name)


@app.get("/api/kpis/{kpi_id}/trend")
def get_kpi_trend(kpi_id: str, current_user: User = Depends(get_current_user)):
    d = _dates()
    return {"kpi_name": kpi_id, "data_points": _orch().kpi_engine.get_daily_trend(kpi_id, d["trend_start"], d["trend_end"])}


@app.get("/api/kpis/{kpi_id}/drivers")
def get_kpi_drivers(kpi_id: str, persona: str = "CEO", current_user: User = Depends(get_current_user)):
    d = _dates()
    a = _orch().run_full_analysis(kpi_name=kpi_id, current_start=d["cur_start"], current_end=d["cur_end"], previous_start=d["prev_start"], previous_end=d["prev_end"], persona=persona, user_role=current_user.role_name)
    return {"kpi_name": kpi_id, "drivers": a.get("drivers",[]), "explained_percent": a.get("explained_percent",0)}


@app.get("/api/insights")
def get_insights(persona: str = "CEO", current_user: User = Depends(get_current_user)):
    d = _dates(); allowed = ROLE_KPI_ACCESS.get(current_user.role_name, []); result = []
    for k in allowed:
        result.append(_orch().run_full_analysis(kpi_name=k, current_start=d["cur_start"], current_end=d["cur_end"], previous_start=d["prev_start"], previous_end=d["prev_end"], persona=persona, user_role=current_user.role_name))
    result.sort(key=lambda x: x.get("materiality",{}).get("total_score",0), reverse=True)
    return {"insights": result, "total": len(result)}


@app.get("/api/insights/{insight_id}")
def get_insight_detail(insight_id: str, current_user: User = Depends(get_current_user)):
    allowed = ROLE_KPI_ACCESS.get(current_user.role_name, [])
    if insight_id not in allowed: raise HTTPException(status_code=403, detail="Access restricted")
    d = _dates()
    return _orch().run_full_analysis(kpi_name=insight_id, current_start=d["cur_start"], current_end=d["cur_end"], previous_start=d["prev_start"], previous_end=d["prev_end"], persona="CEO", user_role=current_user.role_name)


@app.get("/api/recommendations")
def get_recommendations(persona: str = "CEO", current_user: User = Depends(get_current_user)):
    d = _dates(); allowed = ROLE_KPI_ACCESS.get(current_user.role_name, []); all_recs = []
    for k in allowed:
        a = _orch().run_full_analysis(kpi_name=k, current_start=d["cur_start"], current_end=d["cur_end"], previous_start=d["prev_start"], previous_end=d["prev_end"], persona=persona, user_role=current_user.role_name)
        for r in a.get("recommendations",[]): r["kpi_name"] = k; all_recs.append(r)
    all_recs.sort(key=lambda r: r.get("confidence",0), reverse=True)
    return {"recommendations": all_recs, "total": len(all_recs)}


@app.get("/api/data-sources")
def get_data_sources(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"data_sources": [DataSourceResponse.model_validate(s) for s in db.query(DataSource).all()]}


@app.get("/api/lineage")
def get_lineage(kpi_name: str = None, current_user: User = Depends(get_current_user)):
    data = [
        {"id":1,"source_system":"Sales Database","source_table":"sales","transformation":"SUM(revenue)","target_kpi":"Revenue","description":"Revenue from sales"},
        {"id":2,"source_system":"Sales Database","source_table":"sales","transformation":"COUNT(DISTINCT order_id)","target_kpi":"Orders","description":"Unique orders"},
        {"id":3,"source_system":"Marketing Database","source_table":"marketing","transformation":"Conversions/Clicks*100","target_kpi":"Conversion Rate","description":"Conversion rate"},
        {"id":4,"source_system":"Marketing Database","source_table":"marketing","transformation":"Revenue/Spend","target_kpi":"Marketing ROI","description":"Marketing ROI"},
        {"id":5,"source_system":"Inventory Database","source_table":"inventory","transformation":"AVG(stock)","target_kpi":"Inventory Levels","description":"Stock levels"},
        {"id":6,"source_system":"Cross-source","source_table":"analysis","transformation":"Driver decomposition","target_kpi":"Revenue Drivers","description":"Driver analysis"},
        {"id":7,"source_system":"Driver Analysis","source_table":"drivers","transformation":"Contribution ranking","target_kpi":"Insights","description":"Ranked drivers"},
        {"id":8,"source_system":"Insights","source_table":"insights","transformation":"Recommendation","target_kpi":"Recommendations","description":"Actions"},
    ]
    if kpi_name: data = [l for l in data if l["target_kpi"].lower().startswith(kpi_name.lower())]
    return {"lineage": data}


@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fb = Feedback(insight_id=req.insight_id, user_id=current_user.id, rating=req.rating, feedback_type=req.feedback_type, correction=req.correction, persona=current_user.role_name)
    try:
        db.add(fb); db.commit(); db.refresh(fb)
    except Exception:
        db.rollback()
        return {"status": "success", "feedback_id": -1, "note": "Feedback recorded (not persisted)"}
    return {"status": "success", "feedback_id": fb.id}


@app.get("/api/feedback/dashboard")
def feedback_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total = db.query(Feedback).count()
    pos = db.query(Feedback).filter(Feedback.rating == "correct").count()
    neg = db.query(Feedback).filter(Feedback.rating == "incorrect").count()
    common = db.query(Feedback.correction).filter(Feedback.correction.isnot(None)).first()
    return {"total_feedback": total, "positive_count": pos, "negative_count": neg, "positive_rate": round(pos/total*100,1) if total>0 else 0, "most_common_correction": common[0] if common else None, "feedback_trend": []}


def _assistant_response(req: AssistantRequest, user_role: str) -> dict:
    o = _orch(); d = _dates(); msg = req.message.lower()
    allowed = ROLE_KPI_ACCESS.get(user_role, [])

    def run(kpi: str) -> dict:
        return o.run_full_analysis(kpi, d["cur_start"], d["cur_end"], d["prev_start"], d["prev_end"], req.persona, user_role)

    def kpi_name(k: str) -> str:
        return KPI_CONTRACTS.get(k, {}).get("name", k.title())

    def default_kpi() -> str:
        pref = ["conversion_rate", "marketing_roi", "orders"] if user_role == "Marketing Manager" else ["revenue", "orders", "aov", "conversion_rate", "marketing_roi"]
        for k in pref:
            if k in allowed: return k
        return allowed[0] if allowed else "revenue"

    def fmt(v):
        return f"{v:,.0f}" if isinstance(v, (int, float)) and abs(v) >= 100 else f"{v:,.2f}" if isinstance(v, (int, float)) else str(v)

    def drivers_lines(a, n=5):
        ds = sorted(a.get("drivers", []), key=lambda x: abs(x.get("contribution_percent", 0)), reverse=True)
        if not ds: return "No material drivers detected in the current period."
        return "\n".join(f"  {d['name']}: {d.get('contribution_percent',0):.1f}% contribution" for d in ds[:n])

    def conf_info(a):
        c = a.get("confidence", {})
        score = min(float(c.get("confidence_score", 0) or 0), 100.0)
        missing = c.get("data_sources_missing", [])
        txt = f"Confidence: {score:.0f}% ({c.get('confidence_level', 'N/A').title()})"
        if missing: txt += f" | Missing data: {', '.join(missing)}"
        return txt, score

    def rec_lines(a, n=3):
        rs = a.get("recommendations", [])[:n]
        if not rs: return []
        return [f"  {r.get('action','')} (Owner: {r.get('owner','')})" for r in rs]

    # --- intent detection ---
    has_marketing = any(k in msg for k in ("marketing", "campaign", "roi"))
    has_conversion = "conversion" in msg
    has_aov = any(k in msg for k in ("average order", "aov", "order value", "basket"))
    has_orders = any(k in msg for k in ("order", "volume of sales", "orders"))
    has_summary = any(k in msg for k in ("summary", "summarize", "overview", "status", "snapshot", "kpi performance"))
    has_confidence = any(k in msg for k in ("confidence", "confident", "reliable", "trust", "accurate"))
    has_product = any(k in msg for k in ("product", "item", "sku", "top selling"))
    has_region = any(k in msg for k in ("region", "area", "location", "geography", "city"))
    has_trend = any(k in msg for k in ("trend", "over time", "daily", "since", "progress", "trajectory"))
    has_anomaly = any(k in msg for k in ("anomal", "unusual", "abnormal", "spike", "outlier", "weird"))
    has_recommend = any(k in msg for k in ("recommend", "should i", "action", "improve", "next step", "do next", "advice"))
    has_why = any(k in msg for k in ("why", "cause", "reason", "explain", "what happened", "happening"))

    # --- summary across allowed KPIs ---
    if has_summary:
        lines = ["Here's your current business snapshot:\n"]
        ok_kpis = []
        for k in allowed:
            a = run(k)
            if "error" in a: continue
            ok_kpis.append(a)
            ch = a.get("change_percent")
            cur = fmt(a.get("current_value", 0))
            if ch is None:
                lines.append(f"  {kpi_name(a['kpi_name'])}: {cur} (full period, no prior baseline)")
            else:
                lines.append(f"  {kpi_name(a['kpi_name'])}: {cur} ({'+' if ch>0 else ''}{ch:.1f}%)")
        if not ok_kpis:
            return {"response": "No KPI data available for your role.", "evidence_used": [], "confidence": 0}
        c_i, s_i = conf_info(ok_kpis[0])
        lines.append(f"\n{c_i}")
        top = (ok_kpis[0].get("drivers") or [{"name":"N/A"}])[0]["name"]
        lines.append(f"\nTop driver ({kpi_name(ok_kpis[0]['kpi_name'])}): {top}")
        return {"response": "\n".join(lines), "evidence_used": [], "confidence": s_i}

    # --- product breakdown ---
    if has_product:
        a = run(default_kpi())
        if "error" in a: return {"response": str(a.get("message", "Unable to analyze.")), "evidence_used": [], "confidence": 0}
        rows = a.get("product_breakdown", [])[:5]
        if not rows: return {"response": "No product-level data available.", "evidence_used": [], "confidence": 0}
        lines = ["Product breakdown by revenue contribution:\n"]
        for r in rows:
            lines.append(f"  {r['product_name']}: {fmt(r['revenue'])} ({r.get('contribution_percent',0):.0f}%) - {r.get('orders',0)} orders")
        c_i, s_i = conf_info(a)
        lines.append(f"\n{c_i}")
        return {"response": "\n".join(lines), "evidence_used": [], "confidence": s_i}

    # --- region breakdown ---
    if has_region:
        a = run(default_kpi())
        if "error" in a: return {"response": str(a.get("message", "Unable to analyze.")), "evidence_used": [], "confidence": 0}
        rows = a.get("region_breakdown", [])[:5]
        if not rows: return {"response": "No region-level data available.", "evidence_used": [], "confidence": 0}
        lines = ["Regional breakdown by revenue:\n"]
        for r in rows:
            lines.append(f"  {r['region']}: {fmt(r['revenue'])} ({r.get('contribution_percent',0):.0f}%) - {r.get('orders',0)} orders")
        c_i, s_i = conf_info(a)
        lines.append(f"\n{c_i}")
        return {"response": "\n".join(lines), "evidence_used": [], "confidence": s_i}

    # --- trend ---
    if has_trend:
        a = run(default_kpi())
        if "error" in a: return {"response": str(a.get("message", "Unable to analyze.")), "evidence_used": [], "confidence": 0}
        t = a.get("trend", [])
        if not t: return {"response": "Insufficient history to show a trend.", "evidence_used": [], "confidence": 0}
        vals = [x["value"] for x in t]
        peak = max(t, key=lambda x: x["value"]); trough = min(t, key=lambda x: x["value"])
        lines = [f"Daily revenue trend ({t[0]['date']} to {t[-1]['date']}):\n"]
        lines.append("  " + "  ".join(f"{x['date'][5:]} {fmt(x['value'])}" for x in t))
        lines.append(f"\nPeak: {peak['date']} ({fmt(peak['value'])})  |  Low: {trough['date']} ({fmt(trough['value'])})")
        c_i, s_i = conf_info(a)
        lines.append(f"\n{c_i}")
        return {"response": "\n".join(lines), "evidence_used": [], "confidence": s_i}

    # --- anomaly ---
    if has_anomaly:
        a = run(default_kpi())
        if "error" in a: return {"response": str(a.get("message", "Unable to analyze.")), "evidence_used": [], "confidence": 0}
        an = a.get("anomaly", {})
        status = "an anomaly was detected" if an.get("is_anomaly") else "no significant anomaly was detected"
        lines = [f"For {kpi_name(a['kpi_name'])}, {status}."]
        if an.get("reason"): lines.append(f"Reason: {an['reason']}")
        if an.get("z_score") is not None: lines.append(f"Z-score: {an['z_score']:.2f}")
        c_i, s_i = conf_info(a)
        lines.append(c_i)
        return {"response": "\n".join(lines), "evidence_used": [], "confidence": s_i}

    # --- confidence ---
    if has_confidence:
        a = run(default_kpi())
        if "error" in a: return {"response": str(a.get("message", "Unable to analyze.")), "evidence_used": [], "confidence": 0}
        c = a.get("confidence", {})
        score = min(float(c.get("confidence_score", 0) or 0), 100.0)
        missing = c.get("data_sources_missing", [])
        lines = [f"Analysis confidence for {kpi_name(a['kpi_name'])} is {score:.0f}% ({c.get('confidence_level','unknown').title()})."]
        if missing:
            lines.append(f"Confidence is limited by missing data: {', '.join(missing)}.")
        else:
            lines.append("All required data sources were consulted.")
        lines.append(f"Evidence sources used: {', '.join(a.get('data_sources', []))}.")
        if a.get("abstention", {}).get("should_abstain"):
            lines.append("The system abstains from a definitive conclusion due to insufficient evidence.")
        return {"response": "\n".join(lines), "evidence_used": [], "confidence": score}

    # --- recommendations ---
    if has_recommend:
        a = run(default_kpi())
        if "error" in a: return {"response": str(a.get("message", "Unable to analyze.")), "evidence_used": [], "confidence": 0}
        rs = rec_lines(a)
        if not rs: return {"response": "No actionable recommendations at this time.", "evidence_used": [], "confidence": 0}
        lines = ["Recommended actions:\n"] + rs
        c_i, s_i = conf_info(a)
        lines.append(f"\n{c_i}")
        return {"response": "\n".join(lines), "evidence_used": [], "confidence": s_i}

    # --- why / explain ---
    if has_why:
        a = run(default_kpi())
        if "error" in a: return {"response": str(a.get("message", "Unable to analyze.")), "evidence_used": [], "confidence": 0}
        ch = a.get("change_percent")
        if ch is None:
            lead = f"{kpi_name(a['kpi_name'])} is currently at {fmt(a.get('current_value',0))} for the full data period (no prior baseline to compare against)."
        else:
            lead = f"{kpi_name(a['kpi_name'])} {'increased' if ch>0 else 'decreased'} by {abs(ch):.1f}% in the current period."
        lines = [lead, "\nWhat's driving it:\n", drivers_lines(a)]
        ev = a.get("evidence", [])[:3]
        if ev:
            lines.append("\nEvidence:")
            for e in ev:
                lines.append(f"  {e.get('source','')}: {e.get('analytical_method', e.get('metric',''))}")
        c_i, s_i = conf_info(a)
        lines.append(f"\n{c_i}")
        return {"response": "\n".join(lines), "evidence_used": a.get("evidence", [])[:5], "confidence": s_i}

    # --- drivers only ---
    if any(k in msg for k in ("driver", "contribution", "contribut", "factor", "what changed", "moved", "impact")):
        a = run(default_kpi())
        if "error" in a: return {"response": str(a.get("message", "Unable to analyze.")), "evidence_used": [], "confidence": 0}
        lines = [f"Top drivers of {kpi_name(a['kpi_name'])}:\n", drivers_lines(a, 8)]
        c_i, s_i = conf_info(a)
        lines.append(f"\n{c_i}")
        return {"response": "\n".join(lines), "evidence_used": [], "confidence": s_i}

    # --- KPI-specific ---
    target = None
    if has_marketing and "marketing_roi" in allowed: target = "marketing_roi"
    elif has_aov and "aov" in allowed: target = "aov"
    elif has_conversion and "conversion_rate" in allowed: target = "conversion_rate"
    elif has_orders and "orders" in allowed: target = "orders"
    if target:
        a = run(target)
        if "error" in a: return {"response": str(a.get("message", "Unable to analyze.")), "evidence_used": [], "confidence": 0}
        ch = a.get("change_percent")
        cur = fmt(a.get("current_value", 0))
        if ch is None:
            lead = f"{kpi_name(a['kpi_name'])}: {cur} for the full data period (no prior baseline)."
        else:
            lead = f"{kpi_name(a['kpi_name'])}: {cur} ({'+' if ch>0 else ''}{ch:.1f}%)."
        lines = [lead, "\nDrivers:\n", drivers_lines(a)]
        rs = rec_lines(a)
        if rs: lines.append("\nRecommendations:\n" + "\n".join(rs))
        c_i, s_i = conf_info(a)
        lines.append(f"\n{c_i}")
        return {"response": "\n".join(lines), "evidence_used": a.get("evidence", [])[:5], "confidence": s_i}

    # --- default ---
    a = run(default_kpi())
    if "error" in a: return {"response": str(a.get("message", "Unable to analyze.")), "evidence_used": [], "confidence": 0}
    ch = a.get("change_percent")
    cur = fmt(a.get("current_value", 0))
    if ch is None:
        resp = f"{kpi_name(a['kpi_name'])} is currently at {cur} for the full data period (no prior baseline available)."
    else:
        resp = f"{kpi_name(a['kpi_name'])} is {'up' if ch>0 else 'down'} {abs(ch):.1f}% at {cur}."
    resp += f"\n\nDrivers:\n{drivers_lines(a)}"
    rs = rec_lines(a)
    if rs: resp += "\n\nTop recommendations:\n" + "\n".join(rs)
    c_i, s_i = conf_info(a)
    resp += f"\n\n{c_i}"
    return {"response": resp, "evidence_used": a.get("evidence", [])[:5], "confidence": s_i}


@app.post("/api/assistant")
def assistant(req: AssistantRequest, current_user: User = Depends(get_current_user)):
    res = _assistant_response(req, current_user.role_name)
    return AssistantResponse(response=res["response"], evidence_used=res["evidence_used"], confidence=res["confidence"], data_sources_consulted=[])


@app.get("/api/telemetry")
def telemetry(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    logs = db.query(LLMLog).all(); n = len(logs)
    return {"average_latency_ms": 0, "total_llm_calls": n, "total_tokens": sum(l.input_tokens+l.output_tokens for l in logs), "estimated_cost": sum(l.estimated_cost for l in logs), "success_rate": 100.0, "cache_hits": 0, "failed_requests": 0}


@app.post("/api/demo/scenario")
def switch_scenario(req: ScenarioSwitchRequest, current_user: User = Depends(get_current_user)):
    scenarios = {"major_decline":{"name":"Major Revenue Decline","kpi":"revenue","persona":"CEO"}, "low_confidence":{"name":"Low Confidence","kpi":"revenue","persona":"CEO"}, "sparse_history":{"name":"Sparse History","kpi":"revenue","persona":"CEO"}, "contradictory":{"name":"Contradictory Evidence","kpi":"revenue","persona":"CEO"}, "access_restriction":{"name":"Access Restriction","kpi":"revenue","persona":"Marketing Manager"}}
    sc = scenarios.get(req.scenario)
    if not sc: raise HTTPException(status_code=400, detail=f"Unknown scenario: {req.scenario}")
    d = _dates(); role = "Marketing Manager" if req.scenario == "access_restriction" else current_user.role_name
    a = _orch().run_full_analysis(kpi_name=sc["kpi"], current_start=d["cur_start"], current_end=d["cur_end"], previous_start=d["prev_start"], previous_end=d["prev_end"], persona=sc["persona"], user_role=role)
    if req.scenario == "low_confidence":
        a["confidence"]["confidence_score"]=31; a["confidence"]["confidence_level"]="low"; a["confidence"]["data_sources_missing"]=["inventory"]
        a["abstention"]={"should_abstain":True,"reasons":["Missing inventory data"],"suggested_actions":["Connect inventory data"]}
        a["narrative"]="Revenue declined 30%, but evidence is insufficient for root cause.\n\nConfidence: 31%\nStatus: INSUFFICIENT EVIDENCE\n\nMissing: inventory"
    elif req.scenario == "sparse_history":
        a["anomaly"]["is_anomaly"]=False; a["anomaly"]["reason"]="insufficient_history"; a["anomaly"]["historical_coverage"]=5
        a["confidence"]["confidence_score"]=25; a["confidence"]["confidence_level"]="low"
        a["narrative"]="Insufficient historical data.\n\nCoverage: 5 days\nRequired: 30 days\nConfidence: Low"
    elif req.scenario == "contradictory":
        a["contradictions"]["has_contradictions"]=True
        a["contradictions"]["contradictions"]=[{"factor_1":"Sales","factor_2":"Marketing","detail":"Sales declining while marketing improving","severity":0.4}]
        a["contradictions"]["alternative_hypotheses"]=[{"hypothesis":"External market conditions","plausibility":"high"},{"hypothesis":"Product quality issues","plausibility":"medium"}]
        a["narrative"]="Evidence is contradictory. Multiple explanations remain plausible."
    return {"scenario": sc, "analysis": a}


@app.get("/api/demo/scenarios")
def list_scenarios():
    return {"scenarios":[{"id":"major_decline","name":"Major Revenue Decline","description":"Revenue down 25.3%"},{"id":"low_confidence","name":"Low Confidence","description":"Missing data"},{"id":"sparse_history","name":"Sparse History","description":"New product"},{"id":"contradictory","name":"Contradictory Evidence","description":"Conflicting signals"},{"id":"access_restriction","name":"Access Restriction","description":"Role-based denial"}]}


@app.get("/api/admin/users")
def admin_users(current_user: User = Depends(require_role("Admin","CEO")), db: Session = Depends(get_db)):
    return {"users": [UserResponse.model_validate(u) for u in db.query(User).all()]}


@app.get("/api/admin/kpi-definitions")
def admin_kpis(current_user: User = Depends(require_role("Admin","CEO"))):
    return {"definitions": [KPIDefinitionResponse(id=i, **v) for i,(k,v) in enumerate(KPI_CONTRACTS.items(),1)]}


@app.post("/api/upload/file")
async def upload_file(
    file: UploadFile = File(...),
    table_name: str = Form(""),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")
    fname = file.filename or "unknown"
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
    if ext == "csv":
        result = upload_csv(content, fname, table_name or None)
    elif ext in ("xlsx", "xls"):
        result = upload_excel(content, fname, table_name or None)
    elif ext == "sql":
        result = upload_sql(content, fname)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}. Use CSV, Excel, or SQL.")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/upload/preview")
async def preview_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    fname = file.filename or "unknown"
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
    if ext not in ("csv", "xlsx", "xls"):
        raise HTTPException(status_code=400, detail=f"Cannot preview .{ext} files. Use CSV or Excel.")
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        result = preview_file(tmp_path, ext)
    finally:
        os.unlink(tmp_path)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/upload/tables")
def get_uploaded_tables(current_user: User = Depends(get_current_user)):
    return {"tables": list_uploaded_tables()}


@app.get("/api/upload/tables/{table_name}")
def get_table_data(table_name: str, limit: int = 50, offset: int = 0, current_user: User = Depends(get_current_user)):
    result = query_table(table_name, limit, offset)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.delete("/api/upload/tables/{table_name}")
def remove_table(table_name: str, current_user: User = Depends(get_current_user)):
    result = delete_uploaded_table(table_name)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    deactivate_mapping(table_name)
    return result


@app.post("/api/upload/auto-detect")
async def auto_detect_mapping(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    content = await file.read()
    fname = file.filename or "unknown"
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
    if ext not in ("csv", "xlsx", "xls"):
        raise HTTPException(status_code=400, detail="Auto-detect only works with CSV and Excel files")
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        import pandas as pd
        if ext == "csv":
            df = pd.read_csv(tmp_path)
        else:
            df = pd.read_excel(tmp_path)
        table_name = _sanitize_upload_name(fname.rsplit(".", 1)[0])
        cols = [str(c) for c in df.columns]
        result = detect_mapping(table_name, cols)
        result["row_count"] = len(df)
        result["filename"] = fname
    finally:
        os.unlink(tmp_path)
    return result


@app.post("/api/upload/apply-mapping")
def apply_mapping_endpoint(body: dict, current_user: User = Depends(get_current_user)):
    table_name = body.get("table_name")
    mapped_type = body.get("mapped_type")
    column_mapping = body.get("column_mapping")
    if not table_name or not mapped_type or not column_mapping:
        raise HTTPException(status_code=400, detail="table_name, mapped_type, and column_mapping required")
    result = save_mapping(table_name, mapped_type, column_mapping)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    KPIEngine._mapping_cache = {} if hasattr(KPIEngine, '_mapping_cache') else None
    return result


@app.get("/api/upload/mappings")
def get_mappings(current_user: User = Depends(get_current_user)):
    return {"mappings": get_active_mappings()}


@app.delete("/api/upload/mappings/{table_name}")
def remove_mapping(table_name: str, current_user: User = Depends(get_current_user)):
    result = deactivate_mapping(table_name)
    _orch()
    return result


FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
