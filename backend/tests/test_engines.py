"""Tests for KPI Calculation Engine"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from app.engines.kpi_engine import KPIEngine
from app.engines.anomaly_detector import AnomalyDetector
from app.engines.materiality import MaterialityEngine
from app.engines.confidence_engine import ConfidenceEngine
from app.engines.recommendation_engine import RecommendationEngine


@pytest.fixture(scope="module")
def kpi_engine():
    from app.services.data_generator import create_database
    from pathlib import Path
    db_path = str(Path(__file__).parent.parent / "data" / "test_bi.db")
    if not os.path.exists(db_path):
        create_database(db_path)
    engine = KPIEngine(db_path)
    yield engine
    os.remove(db_path)


class TestKPIEngine:
    def test_revenue_calculation(self, kpi_engine):
        result = kpi_engine.calculate_revenue("2025-05-25T00:00:00", "2025-08-27T23:59:59")
        assert result["value"] > 0
        assert result["orders"] > 0
        assert result["units"] > 0

    def test_orders_calculation(self, kpi_engine):
        result = kpi_engine.calculate_orders("2025-05-25T00:00:00", "2025-08-27T23:59:59")
        assert result["value"] > 0

    def test_aov_calculation(self, kpi_engine):
        result = kpi_engine.calculate_aov("2025-05-25T00:00:00", "2025-08-27T23:59:59")
        assert result["value"] > 0
        assert result["orders"] > 0

    def test_conversion_rate(self, kpi_engine):
        result = kpi_engine.calculate_conversion_rate("2025-05-25T00:00:00", "2025-08-27T23:59:59")
        assert result["value"] >= 0

    def test_marketing_roi(self, kpi_engine):
        result = kpi_engine.calculate_marketing_roi("2025-05-25T00:00:00", "2025-08-27T23:59:59")
        assert result["value"] > 0

    def test_all_kpis(self, kpi_engine):
        result = kpi_engine.calculate_all_kpis(
            "2025-08-20T00:00:00", "2025-08-27T23:59:59",
            "2025-08-13T00:00:00", "2025-08-20T23:59:59"
        )
        assert "revenue" in result
        assert "orders" in result
        assert "aov" in result
        assert "conversion_rate" in result
        assert "marketing_roi" in result
        for kpi, data in result.items():
            assert "current" in data
            assert "previous" in data
            assert "change_percent" in data

    def test_product_breakdown(self, kpi_engine):
        result = kpi_engine.get_product_breakdown("2025-05-25T00:00:00", "2025-08-27T23:59:59")
        assert len(result) > 0
        total_contrib = sum(r["contribution_percent"] for r in result)
        assert 99 <= total_contrib <= 101

    def test_region_breakdown(self, kpi_engine):
        result = kpi_engine.get_region_breakdown("2025-05-25T00:00:00", "2025-08-27T23:59:59")
        assert len(result) > 0

    def test_daily_trend(self, kpi_engine):
        trend = kpi_engine.get_daily_trend("revenue", "2025-08-01T00:00:00", "2025-08-27T23:59:59")
        assert len(trend) > 0
        for point in trend:
            assert "date" in point
            assert "value" in point


class TestAnomalyDetector:
    def test_z_score(self):
        detector = AnomalyDetector()
        values = [100, 102, 98, 101, 99, 103, 97, 150]
        z = detector.z_score(150, values[:7])
        assert z > 2.0

    def test_anomaly_detection(self):
        detector = AnomalyDetector()
        values = [100 + (i % 5) * 2 for i in range(20)] + [200]
        dates = [f"2025-08-{i:02d}" for i in range(21)]
        anomalies = detector.detect_anomalies(values, dates)
        assert len(anomalies) == 21
        last = anomalies[-1]
        assert last["is_significant"] is True

    def test_insufficient_history(self):
        detector = AnomalyDetector()
        result = detector.detect_kpi_anomaly(100, [100, 101], ["2025-08-01", "2025-08-02"])
        assert result["is_anomaly"] is False
        assert result["confidence"] == "low"


class TestMaterialityEngine:
    def test_critical_priority(self):
        engine = MaterialityEngine()
        result = engine.assess_materiality("Revenue", 7500000, 10000000)
        assert result["priority"] in ("CRITICAL", "HIGH")
        assert result["is_material"] is True

    def test_low_priority(self):
        engine = MaterialityEngine()
        result = engine.assess_materiality("Revenue", 980000, 1000000)
        assert result["priority"] in ("LOW", "NONE", "MEDIUM")

    def test_priority_score(self):
        engine = MaterialityEngine()
        result = engine.calculate_priority_score(25, 2500000, 0.1, 30)
        assert result["total_score"] > 50
        assert result["priority"] in ("CRITICAL", "HIGH")


class TestConfidenceEngine:
    def test_high_confidence(self):
        engine = ConfidenceEngine()
        result = engine.calculate_confidence(
            data_sources_available=["sales", "marketing", "inventory"],
            data_sources_required=["sales", "marketing"],
            data_freshness_hours={"sales": 1, "marketing": 2},
            statistical_z_score=3.0,
            corroborating_sources=3,
            historical_days=60,
        )
        assert result["confidence_score"] >= 80
        assert result["confidence_level"] == "high"

    def test_low_confidence(self):
        engine = ConfidenceEngine()
        result = engine.calculate_confidence(
            data_sources_available=["sales"],
            data_sources_required=["sales", "marketing", "inventory"],
            data_freshness_hours={"sales": 48},
            statistical_z_score=0.5,
            corroborating_sources=1,
            historical_days=5,
        )
        assert result["confidence_score"] < 50
        assert result["confidence_level"] == "low"

    def test_abstention(self):
        engine = ConfidenceEngine()
        result = engine.should_abstain(30, ["marketing", "inventory"])
        assert result["should_abstain"] is True

    def test_no_abstention(self):
        engine = ConfidenceEngine()
        result = engine.should_abstain(85, [])
        assert result["should_abstain"] is False

    def test_contradiction_detection(self):
        engine = ConfidenceEngine()
        drivers = [
            {"name": "Sales", "type": "product", "change_percent": -20},
            {"name": "Marketing", "type": "marketing", "change_percent": 15},
        ]
        result = engine.detect_contradictions(drivers)
        assert result["has_contradictions"] is True


class TestRecommendationEngine:
    def test_recommendation_generation(self):
        engine = RecommendationEngine()
        drivers = [
            {"name": "Laptop sales", "contribution_percent": 45, "confidence": 0.9},
            {"name": "Marketing spend", "contribution_percent": 25, "confidence": 0.8},
        ]
        recs = engine.generate_recommendations(drivers, "revenue", 2500000, "high")
        assert len(recs) > 0
        for rec in recs:
            assert "action" in rec
            assert "owner" in rec
            assert "confidence" in rec

    def test_no_recommendation_for_small_drivers(self):
        engine = RecommendationEngine()
        drivers = [
            {"name": "Small factor", "contribution_percent": 2, "confidence": 0.5},
        ]
        recs = engine.generate_recommendations(drivers, "revenue", 100000, "high")
        assert len(recs) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
