"""Tests for recommendation engine."""
import pytest
from app.engines.recommendation_engine import RecommendationEngine


@pytest.fixture
def engine():
    return RecommendationEngine()


class TestRecommendationEngine:
    def test_generation(self, engine):
        drivers = [
            {
                "name": "Laptop sales",
                "contribution_percent": 45,
                "confidence": 0.88,
                "type": "product",
                "category": "inventory",
                "absolute_change": -100000,
            },
            {
                "name": "Marketing spend",
                "contribution_percent": 25,
                "confidence": 0.78,
                "type": "marketing",
                "category": "marketing",
                "absolute_change": -50000,
            },
        ]
        recs = engine.generate_recommendations(drivers, "revenue", 250000, "high")
        assert len(recs) > 0
        assert recs[0]["driver_name"] in ("Laptop sales", "Marketing spend")
        assert "owner" in recs[0]
        assert "priority" in recs[0]

    def test_excludes_minor_drivers(self, engine):
        drivers = [
            {
                "name": "Minor factor",
                "contribution_percent": 3,
                "confidence": 0.4,
                "type": "other",
                "category": "other",
                "absolute_change": -5000,
            },
        ]
        recs = engine.generate_recommendations(drivers, "revenue", 10000, "high")
        assert len(recs) == 0

    def test_low_confidence_reduces_score(self, engine):
        drivers = [
            {
                "name": "Laptop sales",
                "contribution_percent": 40,
                "confidence": 0.88,
                "type": "product",
                "category": "inventory",
                "absolute_change": -100000,
            },
        ]
        recs_high = engine.generate_recommendations(drivers, "revenue", 250000, "high")
        recs_low = engine.generate_recommendations(drivers, "revenue", 250000, "low")
        assert len(recs_high) > 0
        assert len(recs_low) > 0
        assert recs_low[0]["confidence"] < recs_high[0]["confidence"]
