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
    try:
        now = datetime.fromisoformat(data_end.replace("Z", "+00:00"))
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
    except Exception:
        now = datetime.now(timezone.utc)
    try:
        start_dt = datetime.fromisoformat(data_start.replace("Z", "+00:00"))
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        days_total = (now - start_dt).days
    except Exception:
        days_total = 90
    lookback = min(days_total, 90)
    cur_start = (now - timedelta(days=min(7, lookback))).isoformat()
    cur_end = now.isoformat()
    prev_start = (now - timedelta(days=min(14, lookback * 2))).isoformat()
    prev_end = cur_start
    return {
        "cur_start": cur_start, "cur_end": cur_end,
        "prev_start": prev_start, "prev_end": prev_end,
        "trend_start": (now - timedelta(days=lookback)).isoformat(), "trend_end": cur_end,
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
        m = o.materiality_engine.assess_materiality(kpi_name=kpi_name, current_value=kpi.get("current",0), previous_value=kpi.get("previous",0), threshold_percent=contract["threshold_percent"])
        trend = o.kpi_engine.get_daily_trend(kpi_name, d["prev_start"], d["cur_end"])
        cards.append({"id": kpi_name, "name": contract["name"], "value": kpi.get("current",0), "previous_value": kpi.get("previous",0), "change_percent": kpi.get("change_percent",0), "priority": m["priority"], "status": "material" if m["is_material"] else "normal", "trend": [x["value"] for x in trend][-14:]})
    return {"kpi_cards": cards, "persona": persona}


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


@app.post("/api/assistant")
def assistant(req: AssistantRequest, current_user: User = Depends(get_current_user)):
    o = _orch(); d = _dates(); msg = req.message.lower()
    kpi = "marketing_roi" if "marketing" in msg or "campaign" in msg else "conversion_rate" if "conversion" in msg else "orders" if "order" in msg else "revenue"
    a = o.run_full_analysis(kpi_name=kpi, current_start=d["cur_start"], current_end=d["cur_end"], previous_start=d["prev_start"], previous_end=d["prev_end"], persona=req.persona, user_role=current_user.role_name)
    if "error" in a: return AssistantResponse(response=a.get("message","Unable to analyze."), confidence=0)
    drivers_text = "\n".join(f"- {d['name']}: {d['contribution_percent']}%" for d in a.get("drivers",[])[:5])
    conf = a.get("confidence",{}).get("confidence_score",0); ch = a.get("change_percent",0); direction = "increased" if ch > 0 else "decreased"
    if a.get("abstention",{}).get("should_abstain"):
        resp = f"{a['kpi_name']} {direction} {abs(ch):.1f}%. Confidence: {conf}%. Missing: {', '.join(a.get('confidence',{}).get('data_sources_missing',[]))}."
    else:
        resp = f"{a['kpi_name']} {direction} {abs(ch):.1f}% with {conf}% confidence.\n\nKey drivers:\n{drivers_text}"
        if a.get("recommendations"): resp += f"\n\nTop recommendation: {a['recommendations'][0]['action']}"
    ev = [{"source":e.get("source",""),"metric":e.get("metric",""),"change":e.get("change_percent",0)} for e in a.get("evidence",[])[:5]]
    return AssistantResponse(response=resp, evidence_used=ev, confidence=conf, data_sources_consulted=a.get("data_sources",[]))


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
