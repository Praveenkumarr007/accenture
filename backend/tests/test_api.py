"""Tests for API endpoints"""
import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture(scope="module")
def test_paths():
    tmp = tempfile.mkdtemp()
    db_path = os.path.join(tmp, "bi_intelligence.db")
    return {"tmp": tmp, "db_path": db_path}


@pytest.fixture(scope="module")
def client(test_paths):
    from app.services.data_generator import create_database
    create_database(test_paths["db_path"])

    with patch("app.main.DB_PATH", test_paths["db_path"]):
        from app.core.database import Base, engine, SessionLocal
        Base.metadata.create_all(bind=engine)

        from app.models.database_models import User, UserRole, DataSource, KPIDefinition
        from app.core.security import hash_password
        from app.core.kpi_contracts import KPI_CONTRACTS

        db = SessionLocal()
        try:
            if db.query(User).count() == 0:
                for r in [
                    UserRole(name="CEO", description="CEO", permissions=["all"]),
                    UserRole(name="Sales Manager", description="Sales", permissions=["revenue", "orders", "aov"]),
                    UserRole(name="Marketing Manager", description="Marketing", permissions=["conversion_rate", "marketing_roi", "orders"]),
                    UserRole(name="Admin", description="Admin", permissions=["all"]),
                ]:
                    db.add(r)
                db.flush()
                for u in [
                    User(username="ceo", email="ceo@shopsmart.com", hashed_password=hash_password("demo123"), full_name="Sarah Chen", role_name="CEO"),
                    User(username="sales_mgr", email="sales@shopsmart.com", hashed_password=hash_password("demo123"), full_name="James Wilson", role_name="Sales Manager"),
                    User(username="marketing_mgr", email="marketing@shopsmart.com", hashed_password=hash_password("demo123"), full_name="Priya Patel", role_name="Marketing Manager"),
                    User(username="admin", email="admin@shopsmart.com", hashed_password=hash_password("admin123"), full_name="Admin User", role_name="Admin"),
                ]:
                    db.add(u)
                db.flush()
                for s in [
                    DataSource(name="Sales Database", source_type="postgresql", status="healthy", refresh_frequency="hourly", row_count=150000, data_quality_score=0.95, coverage_days=95, description="Sales transactions"),
                    DataSource(name="Marketing Database", source_type="postgresql", status="healthy", refresh_frequency="4_hours", row_count=8500, data_quality_score=0.92, coverage_days=90, description="Campaign metrics"),
                    DataSource(name="Inventory Database", source_type="postgresql", status="healthy", refresh_frequency="30_minutes", row_count=25000, data_quality_score=0.88, coverage_days=95, description="Stock levels"),
                ]:
                    db.add(s)
                for kpi_name, c in KPI_CONTRACTS.items():
                    db.add(KPIDefinition(
                        name=c["name"], description=c["description"], formula=c["formula"],
                        data_source=c["data_source"], refresh_frequency=c["refresh_frequency"],
                        threshold_percent=c["threshold_percent"], owner=c["owner"],
                        allowed_roles=c["allowed_roles"], dimensions=c["dimensions"],
                        business_meaning=c["business_meaning"], lineage=c["lineage"],
                    ))
                db.commit()
        finally:
            db.close()

        from app.main import app
        from fastapi.testclient import TestClient
        with TestClient(app) as c:
            yield c


@pytest.fixture(scope="module")
def auth_token(client):
    res = client.post("/api/auth/login", json={"username": "ceo", "password": "demo123"})
    assert res.status_code == 200, f"Login failed: {res.status_code} {res.text}"
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


class TestAuth:
    def test_login_success(self, client):
        res = client.post("/api/auth/login", json={"username": "ceo", "password": "demo123"})
        assert res.status_code == 200
        assert "access_token" in res.json()
        assert res.json()["user"]["role_name"] == "CEO"

    def test_login_failure(self, client):
        res = client.post("/api/auth/login", json={"username": "ceo", "password": "wrong"})
        assert res.status_code == 401

    def test_profile(self, client, headers):
        res = client.get("/api/user/profile", headers=headers)
        assert res.status_code == 200
        assert res.json()["username"] == "ceo"


class TestKPIs:
    def test_get_kpis(self, client, headers):
        res = client.get("/api/kpis", headers=headers)
        assert res.status_code == 200
        assert len(res.json()["kpi_cards"]) > 0

    def test_get_kpi_detail(self, client, headers):
        res = client.get("/api/kpis/revenue", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "drivers" in data
        assert "confidence" in data

    def test_get_kpi_trend(self, client, headers):
        res = client.get("/api/kpis/revenue/trend", headers=headers)
        assert res.status_code == 200
        assert len(res.json()["data_points"]) > 0

    def test_get_kpi_drivers(self, client, headers):
        res = client.get("/api/kpis/revenue/drivers", headers=headers)
        assert res.status_code == 200
        assert "drivers" in res.json()


class TestInsights:
    def test_get_insights(self, client, headers):
        res = client.get("/api/insights", headers=headers)
        assert res.status_code == 200
        assert res.json()["total"] > 0


class TestRecommendations:
    def test_get_recommendations(self, client, headers):
        res = client.get("/api/recommendations", headers=headers)
        assert res.status_code == 200


class TestDataSources:
    def test_get_data_sources(self, client, headers):
        res = client.get("/api/data-sources", headers=headers)
        assert res.status_code == 200
        assert len(res.json()["data_sources"]) == 3


class TestLineage:
    def test_get_lineage(self, client, headers):
        res = client.get("/api/lineage", headers=headers)
        assert res.status_code == 200
        assert len(res.json()["lineage"]) > 0


class TestFeedback:
    def test_submit_feedback(self, client, headers):
        res = client.post("/api/feedback", json={
            "insight_id": 1,
            "rating": "correct",
        }, headers=headers)
        assert res.status_code == 200
        assert res.json()["status"] == "success"

    def test_get_feedback_dashboard(self, client, headers):
        res = client.get("/api/feedback/dashboard", headers=headers)
        assert res.status_code == 200
        assert "total_feedback" in res.json()


class TestAssistant:
    def test_send_message(self, client, headers):
        res = client.post("/api/assistant", json={
            "message": "Why did revenue decline?",
            "persona": "CEO",
        }, headers=headers)
        assert res.status_code == 200
        assert "response" in res.json()
        assert "confidence" in res.json()


class TestTelemetry:
    def test_get_telemetry(self, client, headers):
        res = client.get("/api/telemetry", headers=headers)
        assert res.status_code == 200


class TestDemoScenarios:
    def test_list_scenarios(self, client, headers):
        res = client.get("/api/demo/scenarios", headers=headers)
        assert res.status_code == 200
        assert len(res.json()["scenarios"]) == 5

    def test_major_decline(self, client, headers):
        res = client.post("/api/demo/scenario", json={"scenario": "major_decline"}, headers=headers)
        assert res.status_code == 200
        assert "analysis" in res.json()

    def test_low_confidence(self, client, headers):
        res = client.post("/api/demo/scenario", json={"scenario": "low_confidence"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["analysis"]["abstention"]["should_abstain"] is True


class TestRoleAuthorization:
    def test_marketing_mgr_cannot_access_revenue(self, client):
        res = client.post("/api/auth/login", json={"username": "marketing_mgr", "password": "demo123"})
        token = res.json()["access_token"]
        hdrs = {"Authorization": f"Bearer {token}"}
        res = client.get("/api/kpis/revenue", headers=hdrs)
        assert res.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
