"""Tests for KPI calculation engine."""
import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta, timezone
from app.engines.kpi_engine import KPIEngine


@pytest.fixture(scope="module")
def db_path():
    path = tempfile.mktemp(suffix=".db")
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            order_id TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            region TEXT NOT NULL,
            units_sold INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            revenue REAL NOT NULL
        );
        CREATE TABLE marketing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            campaign_id TEXT NOT NULL,
            campaign_name TEXT NOT NULL,
            channel TEXT NOT NULL,
            spend REAL NOT NULL,
            impressions INTEGER NOT NULL,
            clicks INTEGER NOT NULL,
            conversions INTEGER NOT NULL
        );
        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            warehouse TEXT NOT NULL,
            stock_available INTEGER NOT NULL,
            stockout INTEGER NOT NULL,
            replenishment_time INTEGER NOT NULL
        );
    """)
    now = datetime.now(timezone.utc)
    for i in range(10):
        d = (now - timedelta(days=i)).isoformat()
        cur.execute(
            "INSERT INTO sales (date, order_id, product_id, product_name, region, units_sold, unit_price, revenue) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (d, f"ORD-{i:04d}", 1, "Laptop", "North", 5, 89999.0, 5 * 89999.0),
        )
    cur.execute(
        "INSERT INTO marketing (date, campaign_id, campaign_name, channel, spend, impressions, clicks, conversions) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (now.isoformat(), "CMP-001", "Test Campaign", "Google Ads", 100000, 1000000, 50000, 2500),
    )
    cur.execute(
        "INSERT INTO inventory (date, product_id, product_name, warehouse, stock_available, stockout, replenishment_time) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (now.isoformat(), 1, "Laptop", "North_WH", 100, 0, 7),
    )
    conn.commit()
    conn.close()
    yield path
    os.unlink(path)


@pytest.fixture
def engine(db_path):
    return KPIEngine(db_path)


class TestKPIEngine:
    def test_revenue(self, engine):
        now = datetime.now(timezone.utc)
        result = engine.calculate_revenue(
            (now - timedelta(days=11)).isoformat(),
            (now + timedelta(days=1)).isoformat(),
        )
        assert result["value"] > 0
        assert result["units"] > 0
        assert result["orders"] > 0

    def test_orders(self, engine):
        now = datetime.now(timezone.utc)
        result = engine.calculate_orders(
            (now - timedelta(days=11)).isoformat(),
            (now + timedelta(days=1)).isoformat(),
        )
        assert result["value"] == 10

    def test_aov(self, engine):
        now = datetime.now(timezone.utc)
        result = engine.calculate_aov(
            (now - timedelta(days=11)).isoformat(),
            (now + timedelta(days=1)).isoformat(),
        )
        assert result["value"] > 0
        assert result["revenue"] > 0
        assert result["orders"] > 0

    def test_conversion_rate(self, engine):
        now = datetime.now(timezone.utc)
        result = engine.calculate_conversion_rate(
            (now - timedelta(days=1)).isoformat(),
            (now + timedelta(days=1)).isoformat(),
        )
        assert result["value"] > 0
        assert result["conversions"] == 2500
        assert result["clicks"] == 50000

    def test_marketing_roi(self, engine):
        now = datetime.now(timezone.utc)
        result = engine.calculate_marketing_roi(
            (now - timedelta(days=1)).isoformat(),
            (now + timedelta(days=1)).isoformat(),
        )
        assert result["value"] > 0
        assert result["revenue"] > 0
        assert result["spend"] == 100000

    def test_calculate_all_kpis(self, engine):
        now = datetime.now(timezone.utc)
        result = engine.calculate_all_kpis(
            (now - timedelta(days=1)).isoformat(),
            (now + timedelta(days=1)).isoformat(),
            (now - timedelta(days=8)).isoformat(),
            (now - timedelta(days=1)).isoformat(),
        )
        assert "revenue" in result
        assert "orders" in result
        assert "aov" in result
        assert "conversion_rate" in result
        assert "marketing_roi" in result
        assert "current" in result["revenue"]
        assert "previous" in result["revenue"]
        assert "change_percent" in result["revenue"]

    def test_daily_trend(self, engine):
        now = datetime.now(timezone.utc)
        trend = engine.get_daily_trend(
            "revenue",
            (now - timedelta(days=11)).isoformat(),
            (now + timedelta(days=1)).isoformat(),
        )
        assert len(trend) > 0
        assert "date" in trend[0]
        assert "value" in trend[0]

    def test_product_breakdown(self, engine):
        now = datetime.now(timezone.utc)
        breakdown = engine.get_product_breakdown(
            (now - timedelta(days=11)).isoformat(),
            (now + timedelta(days=1)).isoformat(),
        )
        assert len(breakdown) > 0
        assert breakdown[0]["product_name"] == "Laptop"

    def test_region_breakdown(self, engine):
        now = datetime.now(timezone.utc)
        breakdown = engine.get_region_breakdown(
            (now - timedelta(days=11)).isoformat(),
            (now + timedelta(days=1)).isoformat(),
        )
        assert len(breakdown) > 0
        assert "region" in breakdown[0]
