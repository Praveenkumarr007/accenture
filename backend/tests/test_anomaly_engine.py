"""Tests for materiality engine, anomaly detection, and confidence engine."""
import pytest
from app.engines.materiality import MaterialityEngine
from app.engines.anomaly_detector import AnomalyDetector
from app.engines.confidence_engine import ConfidenceEngine


@pytest.fixture
def materiality():
    return MaterialityEngine()


@pytest.fixture
def anomaly_detector():
    return AnomalyDetector()


@pytest.fixture
def confidence_engine():
    return ConfidenceEngine()


class TestMaterialityEngine:
    def test_critical_priority(self, materiality):
        result = materiality.calculate_priority_score(25.0, 500000, 5.0, True)
        assert result["priority"] in ("CRITICAL", "HIGH")
        assert result["is_material"] is True

    def test_low_priority(self, materiality):
        result = materiality.calculate_priority_score(3.0, 10000, 2.0, False)
        assert result["priority"] in ("LOW", "NONE")
        assert result["is_material"] is False

    def test_medium_priority(self, materiality):
        result = materiality.calculate_priority_score(12.0, 500000, 5.0, 30)
        assert result["priority"] in ("MEDIUM", "HIGH", "CRITICAL")

    def test_assess_materiality(self, materiality):
        result = materiality.assess_materiality("revenue", 750000, 1000000, threshold_percent=10.0)
        assert result["kpi_name"] == "revenue"
        assert result["change_percent"] < 0
        assert result["passes_threshold"] is True
        assert "priority" in result


class TestAnomalyDetector:
    def test_rolling_mean(self, anomaly_detector):
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        m = anomaly_detector.mean(values)
        assert m == 5.5

    def test_std_dev(self, anomaly_detector):
        values = [1, 1, 1, 1, 1]
        sd = anomaly_detector.std_dev(values)
        assert sd == 0.0

    def test_z_score_normal(self, anomaly_detector):
        values = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
        z = anomaly_detector.z_score(10, values)
        assert z == 0.0

    def test_z_score_anomaly(self, anomaly_detector):
        values = [10, 11, 9, 12, 8, 10, 11, 9, 10, 11]
        z = anomaly_detector.z_score(30, values)
        assert z > 3.0

    def test_detect_anomalies(self, anomaly_detector):
        import random
        random.seed(42)
        values = [100 + random.gauss(0, 5) for _ in range(14)] + [50] + [100 + random.gauss(0, 5) for _ in range(5)]
        dates = [f"2025-01-{i:02d}" for i in range(20)]
        results = anomaly_detector.detect_anomalies(values, dates)
        assert len(results) == 20
        assert any(r["is_significant"] for r in results)

    def test_detect_kpi_anomaly_insufficient_history(self, anomaly_detector):
        result = anomaly_detector.detect_kpi_anomaly(
            current_value=100,
            historical_values=[100, 100, 100],
            historical_dates=["d1", "d2", "d3"],
        )
        assert result["is_anomaly"] is False
        assert result["reason"] == "insufficient_history"

    def test_detect_kpi_anomaly_with_data(self, anomaly_detector):
        historical = [100, 105, 98, 102, 100, 103, 99, 101, 100, 104, 97, 100, 102, 101, 98, 100]
        result = anomaly_detector.detect_kpi_anomaly(
            current_value=60,
            historical_values=historical,
            historical_dates=[f"d{i}" for i in range(len(historical))],
        )
        assert result["is_anomaly"] is True
        assert result["z_score"] < -2.0


class TestConfidenceEngine:
    def test_high_confidence(self, confidence_engine):
        result = confidence_engine.calculate_confidence(
            data_sources_available=["sales", "marketing", "inventory"],
            data_sources_required=["sales", "marketing", "inventory"],
            data_freshness_hours={"sales": 1, "marketing": 3, "inventory": 0.5},
            statistical_z_score=2.5,
            corroborating_sources=3,
            historical_days=90,
            has_contradictions=False,
            contradiction_severity=0.0,
        )
        assert result["confidence_score"] >= 60
        assert result["confidence_level"] in ("high", "medium")

    def test_low_confidence(self, confidence_engine):
        result = confidence_engine.calculate_confidence(
            data_sources_available=["sales"],
            data_sources_required=["sales", "marketing", "inventory"],
            data_freshness_hours={"sales": 48},
            statistical_z_score=0.5,
            corroborating_sources=1,
            historical_days=10,
            has_contradictions=True,
            contradiction_severity=0.5,
        )
        assert result["confidence_score"] < 50
        assert result["confidence_level"] == "low"

    def test_abstain_when_low(self, confidence_engine):
        result = confidence_engine.should_abstain(30, ["inventory"])
        assert result["should_abstain"] is True

    def test_no_abstain_when_high(self, confidence_engine):
        result = confidence_engine.should_abstain(85, [])
        assert result["should_abstain"] is False

    def test_contradiction_detection(self, confidence_engine):
        drivers = [
            {"name": "Sales", "type": "product", "change_percent": -20},
            {"name": "Marketing", "type": "marketing", "change_percent": 15},
        ]
        result = confidence_engine.detect_contradictions(drivers)
        assert result["has_contradictions"] is True
        assert result["severity"] > 0

    def test_no_contradiction(self, confidence_engine):
        drivers = [
            {"name": "Sales", "type": "product", "change_percent": -20},
            {"name": "More Sales", "type": "product", "change_percent": -10},
        ]
        result = confidence_engine.detect_contradictions(drivers)
        assert result["has_contradictions"] is False
