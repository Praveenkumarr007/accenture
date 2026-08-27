from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta, timezone
from app.core.database import SessionLocal
from app.core.kpi_contracts import KPI_CONTRACTS, get_kpi_names
from app.engines.kpi_engine import calculate_kpi, compute_daily_kpis, get_all_kpi_current
from app.engines.materiality_engine import calculate_materiality_score

router = APIRouter()


@router.get("")
def list_kpis(persona: str = "CEO"):
    db = SessionLocal()
    try:
        kpis = get_all_kpi_current(db)
        result = []
        for kpi in kpis:
            contract = KPI_CONTRACTS.get(kpi["kpi_key"], {})
            if persona != "CEO" and persona not in contract.get("allowed_roles", []):
                continue
            mat = calculate_materiality_score(
                kpi["change_percent"],
                abs(kpi["current_value"] - kpi["previous_value"]),
            )
            kpi["priority_level"] = mat["priority_level"]
            kpi["priority_score"] = mat["priority_score"]
            result.append(kpi)
        return result
    finally:
        db.close()


@router.get("/definitions")
def list_kpi_definitions():
    return [
        {
            "id": i + 1,
            "name": v["name"],
            "description": v["description"],
            "definition": v["definition"],
            "formula": v["formula"],
            "data_sources": v["data_sources"],
            "dimensions": v["dimensions"],
            "refresh_frequency": v["refresh_frequency"],
            "threshold": v["threshold"],
            "owner": v["owner"],
            "allowed_roles": v["allowed_roles"],
            "business_meaning": v["business_meaning"],
            "unit": v["unit"],
        }
        for i, (k, v) in enumerate(KPI_CONTRACTS.items())
    ]


@router.get("/{kpi_name}")
def get_kpi(kpi_name: str):
    kpi_key = kpi_name.lower().replace(" ", "_").replace("-", "_")
    contract = KPI_CONTRACTS.get(kpi_key)
    if not contract:
        raise HTTPException(status_code=404, detail=f"KPI '{kpi_name}' not found")
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        current = calculate_kpi(kpi_key, db, now - timedelta(days=7), now)
        previous = calculate_kpi(kpi_key, db, now - timedelta(days=14), now - timedelta(days=7))
        change_pct = ((current - previous) / abs(previous) * 100) if previous else 0
        mat = calculate_materiality_score(change_pct, abs(current - previous))
        return {
            "name": contract["name"],
            "kpi_key": kpi_key,
            "current_value": current,
            "previous_value": previous,
            "change_percent": round(change_pct, 1),
            "priority_level": mat["priority_level"],
            "priority_score": mat["priority_score"],
            "definition": contract["definition"],
            "formula": contract["formula"],
            "business_meaning": contract["business_meaning"],
            "owner": contract["owner"],
            "unit": contract["unit"],
            "threshold": contract["threshold"],
        }
    finally:
        db.close()


@router.get("/{kpi_name}/trend")
def get_kpi_trend(kpi_name: str, days: int = 30):
    kpi_key = kpi_name.lower().replace(" ", "_").replace("-", "_")
    if kpi_key not in KPI_CONTRACTS:
        raise HTTPException(status_code=404, detail=f"KPI '{kpi_name}' not found")
    db = SessionLocal()
    try:
        daily = compute_daily_kpis(db, kpi_key, days)
        return {"kpi_name": KPI_CONTRACTS[kpi_key]["name"], "data": [{"date": d["date"], "value": d["value"]} for d in daily]}
    finally:
        db.close()
