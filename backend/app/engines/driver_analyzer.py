"""
Driver Analysis Engine

The most important analytical component.
When a KPI changes, this engine determines WHY.

All calculations are deterministic.
The LLM does NOT determine contribution percentages.
"""
import sqlite3
from typing import Optional
from app.engines.kpi_engine import KPIEngine


class DriverAnalyzer:
    def __init__(self, db_path: str, kpi_engine: Optional[KPIEngine] = None):
        self.db_path = db_path
        self.kpi_engine = kpi_engine or KPIEngine(db_path)

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _col(self, target_type: str, field: str) -> str:
        return self.kpi_engine._col(target_type, field)

    def _table(self, target_type: str) -> str:
        return self.kpi_engine._table(target_type)

    def _calculate_product_drivers(self, current_start, current_end, previous_start, previous_end) -> list:
        conn = self._connect()
        cur = conn.cursor()
        t = self._table("sales")
        date_col = self._col("sales", "date")
        prod_col = self._col("sales", "product_name")
        rev_col = self._col("sales", "revenue")
        units_col = self._col("sales", "units_sold")

        cur.execute(f"SELECT [{prod_col}] as product_name, SUM([{rev_col}]) as revenue, SUM([{units_col}]) as units FROM [{t}] WHERE [{date_col}] >= ? AND [{date_col}] <= ? GROUP BY [{prod_col}]", [current_start, current_end])
        current = {row["product_name"]: dict(row) for row in cur.fetchall()}
        cur.execute(f"SELECT [{prod_col}] as product_name, SUM([{rev_col}]) as revenue, SUM([{units_col}]) as units FROM [{t}] WHERE [{date_col}] >= ? AND [{date_col}] <= ? GROUP BY [{prod_col}]", [previous_start, previous_end])
        previous = {row["product_name"]: dict(row) for row in cur.fetchall()}
        conn.close()
        total_change = sum(c["revenue"] for c in current.values()) - sum(p["revenue"] for p in previous.values())
        if total_change == 0:
            return []
        drivers = []
        for product in set(list(current.keys()) + list(previous.keys())):
            curr_rev = current.get(product, {}).get("revenue", 0)
            prev_rev = previous.get(product, {}).get("revenue", 0)
            change = curr_rev - prev_rev
            contribution = (change / total_change * 100) if total_change != 0 else 0
            change_pct = ((curr_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
            drivers.append({
                "name": f"{product} sales", "type": "product",
                "contribution_percent": round(contribution, 1),
                "revenue_change": round(change, 2), "change_percent": round(change_pct, 2),
                "supporting_data": {"current_revenue": round(curr_rev, 2), "previous_revenue": round(prev_rev, 2)},
                "data_source": "sales", "confidence": 0.9,
            })
        drivers.sort(key=lambda d: abs(d["contribution_percent"]), reverse=True)
        for i, d in enumerate(drivers):
            d["rank"] = i + 1
            d["is_primary"] = i == 0
        return drivers

    def _calculate_region_drivers(self, current_start, current_end, previous_start, previous_end) -> list:
        conn = self._connect()
        cur = conn.cursor()
        t = self._table("sales")
        date_col = self._col("sales", "date")
        reg_col = self._col("sales", "region")
        rev_col = self._col("sales", "revenue")

        cur.execute(f"SELECT [{reg_col}] as region, SUM([{rev_col}]) as revenue FROM [{t}] WHERE [{date_col}] >= ? AND [{date_col}] <= ? GROUP BY [{reg_col}]", [current_start, current_end])
        current = {row["region"]: row["revenue"] for row in cur.fetchall()}
        cur.execute(f"SELECT [{reg_col}] as region, SUM([{rev_col}]) as revenue FROM [{t}] WHERE [{date_col}] >= ? AND [{date_col}] <= ? GROUP BY [{reg_col}]", [previous_start, previous_end])
        previous = {row["region"]: row["revenue"] for row in cur.fetchall()}
        conn.close()
        total_change = sum(current.values()) - sum(previous.values())
        if total_change == 0:
            return []
        drivers = []
        for region in set(list(current.keys()) + list(previous.keys())):
            curr = current.get(region, 0)
            prev = previous.get(region, 0)
            change = curr - prev
            contribution = (change / total_change * 100) if total_change != 0 else 0
            drivers.append({
                "name": f"{region} region", "type": "region",
                "contribution_percent": round(contribution, 1),
                "revenue_change": round(change, 2),
                "change_percent": round(((curr - prev) / prev * 100) if prev > 0 else 0, 2),
                "supporting_data": {"current_revenue": round(curr, 2), "previous_revenue": round(prev, 2)},
                "data_source": "sales", "confidence": 0.85,
            })
        drivers.sort(key=lambda d: abs(d["contribution_percent"]), reverse=True)
        for i, d in enumerate(drivers):
            d["rank"] = i + 1
            d["is_primary"] = i == 0
        return drivers

    def _calculate_marketing_drivers(self, current_start, current_end, previous_start, previous_end) -> list:
        conn = self._connect()
        cur = conn.cursor()
        t = self._table("marketing")
        date_col = self._col("marketing", "date")
        spend_col = self._col("marketing", "spend")
        click_col = self._col("marketing", "clicks")
        conv_col = self._col("marketing", "conversions")

        cur.execute(f"SELECT SUM([{spend_col}]) as spend, SUM([{click_col}]) as clicks, SUM([{conv_col}]) as conv FROM [{t}] WHERE [{date_col}] >= ? AND [{date_col}] <= ?", [current_start, current_end])
        current = dict(cur.fetchone())
        cur.execute(f"SELECT SUM([{spend_col}]) as spend, SUM([{click_col}]) as clicks, SUM([{conv_col}]) as conv FROM [{t}] WHERE [{date_col}] >= ? AND [{date_col}] <= ?", [previous_start, previous_end])
        previous = dict(cur.fetchone())
        conn.close()
        curr_spend = current.get("spend", 0) or 0
        prev_spend = previous.get("spend", 0) or 0
        curr_clicks = current.get("clicks", 0) or 0
        prev_clicks = previous.get("clicks", 0) or 0
        drivers = []
        if prev_spend > 0:
            drivers.append({"name": "Marketing spend", "type": "marketing", "contribution_percent": 0,
                           "spend_change": round(curr_spend - prev_spend, 2),
                           "change_percent": round((curr_spend - prev_spend) / prev_spend * 100, 2),
                           "supporting_data": {"current_spend": round(curr_spend, 2), "previous_spend": round(prev_spend, 2)},
                           "data_source": "marketing", "confidence": 0.88})
        if prev_clicks > 0:
            drivers.append({"name": "Website traffic", "type": "traffic", "contribution_percent": 0,
                           "traffic_change": round(curr_clicks - prev_clicks, 0),
                           "change_percent": round((curr_clicks - prev_clicks) / prev_clicks * 100, 2),
                           "supporting_data": {"current_clicks": curr_clicks, "previous_clicks": prev_clicks},
                           "data_source": "marketing", "confidence": 0.82})
        return drivers

    def _calculate_inventory_drivers(self, current_start, current_end, previous_start, previous_end) -> list:
        conn = self._connect()
        cur = conn.cursor()
        t = self._table("inventory")
        date_col = self._col("inventory", "date")
        prod_col = self._col("inventory", "product_name")
        stock_col = self._col("inventory", "stock_available")

        cur.execute(f"SELECT [{prod_col}] as product_name, AVG([{stock_col}]) as avg_stock FROM [{t}] WHERE [{date_col}] >= ? AND [{date_col}] <= ? GROUP BY [{prod_col}]", [current_start, current_end])
        current = {row["product_name"]: row["avg_stock"] or 0 for row in cur.fetchall()}
        cur.execute(f"SELECT [{prod_col}] as product_name, AVG([{stock_col}]) as avg_stock FROM [{t}] WHERE [{date_col}] >= ? AND [{date_col}] <= ? GROUP BY [{prod_col}]", [previous_start, previous_end])
        previous = {row["product_name"]: row["avg_stock"] or 0 for row in cur.fetchall()}
        conn.close()
        drivers = []
        for product in set(list(current.keys()) + list(previous.keys())):
            curr_stock = current.get(product, 0)
            prev_stock = previous.get(product, 0)
            stock_change_pct = ((curr_stock - prev_stock) / prev_stock * 100) if prev_stock > 0 else 0
            if abs(stock_change_pct) > 5:
                drivers.append({"name": f"{product} inventory", "type": "inventory", "contribution_percent": 0,
                               "stock_change": round(curr_stock - prev_stock, 0), "change_percent": round(stock_change_pct, 2),
                               "supporting_data": {"current_avg_stock": round(curr_stock, 0), "previous_avg_stock": round(prev_stock, 0)},
                               "data_source": "inventory", "confidence": 0.92})
        return drivers

    def _calculate_seasonality(self, values, current_idx):
        if len(values) < 14:
            return {"name": "Seasonality", "type": "seasonality", "contribution_percent": 0, "change_percent": 0, "confidence": 0.3}
        weekly_avgs = [sum(values[i:i+7])/7 for i in range(0, len(values)-6, 7)]
        overall_avg = sum(weekly_avgs) / len(weekly_avgs) if weekly_avgs else 0
        current_week_avg = sum(values[max(0, current_idx-6):current_idx+1]) / 7 if current_idx >= 6 else 0
        effect = ((current_week_avg - overall_avg) / overall_avg * 100) if overall_avg > 0 else 0
        return {"name": "Seasonality", "type": "seasonality", "contribution_percent": 0,
                "change_percent": round(effect, 2), "supporting_data": {"overall_weekly_avg": round(overall_avg, 2)},
                "data_source": "calculated", "confidence": 0.6}

    def analyze_drivers(self, current_start, current_end, previous_start, previous_end, total_change, daily_values=None):
        all_drivers = (
            self._calculate_product_drivers(current_start, current_end, previous_start, previous_end) +
            self._calculate_region_drivers(current_start, current_end, previous_start, previous_end) +
            self._calculate_marketing_drivers(current_start, current_end, previous_start, previous_end) +
            self._calculate_inventory_drivers(current_start, current_end, previous_start, previous_end)
        )
        if daily_values and len(daily_values) >= 14:
            all_drivers.append(self._calculate_seasonality(daily_values, len(daily_values) - 1))
        if total_change != 0:
            raw = []
            for d in all_drivers:
                if d["type"] == "product":
                    raw.append(d["revenue_change"])
                elif d["type"] == "region":
                    raw.append(d["revenue_change"])
                elif d["type"] == "marketing":
                    raw.append(d.get("spend_change", 0))
                elif d["type"] == "inventory":
                    raw.append(d.get("stock_change", 0) * -100)
                elif d["type"] == "seasonality":
                    raw.append(d.get("change_percent", 0))
                else:
                    raw.append(0)
            total_raw = sum(abs(c) for c in raw) or 1
            for d, r in zip(all_drivers, raw):
                d["contribution_percent"] = round(abs(r) / total_raw * 100, 1)
        all_drivers.sort(key=lambda d: abs(d["contribution_percent"]), reverse=True)
        for i, d in enumerate(all_drivers):
            d["rank"] = i + 1
            d["is_primary"] = i == 0
        explained = sum(d["contribution_percent"] for d in all_drivers)
        remaining = max(0, 100 - explained)
        if remaining > 1:
            all_drivers.append({"name": "Other factors", "type": "other", "contribution_percent": round(remaining, 1),
                               "supporting_data": {}, "data_source": "calculated", "confidence": 0.4,
                               "rank": len(all_drivers) + 1, "is_primary": False})
        return {"drivers": all_drivers[:8], "total_drivers": len(all_drivers), "explained_percent": round(min(100, explained), 1)}