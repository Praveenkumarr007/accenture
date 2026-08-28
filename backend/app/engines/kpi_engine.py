"""KPI Calculation Engine - with support for uploaded data mappings."""
from datetime import datetime, timedelta, timezone
from typing import Optional
import sqlite3
import math
import json

from app.services.data_mapper import get_mapping_for_type


class KPIEngine:
    """Deterministic KPI calculation engine."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._mapping_cache = {}

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_table_config(self, target_type: str) -> dict:
        if target_type in self._mapping_cache:
            return self._mapping_cache[target_type]

        mapping = get_mapping_for_type(target_type, self.db_path)
        if mapping:
            table = mapping["table_name"]
            raw_cols = mapping["column_mapping"]
            cols = {}
            for uploaded_col, target_field in raw_cols.items():
                cols[target_field] = uploaded_col
            config = {"table": table, "columns": cols, "is_mapped": True}
        else:
            defaults = {
                "sales": {"table": "sales", "columns": {"date": "date", "revenue": "revenue", "units_sold": "units_sold", "order_id": "order_id", "product_name": "product_name", "region": "region"}},
                "marketing": {"table": "marketing", "columns": {"date": "date", "conversions": "conversions", "clicks": "clicks", "spend": "spend"}},
                "inventory": {"table": "inventory", "columns": {"date": "date", "product_name": "product_name", "stock_available": "stock_available", "stockout": "stockout"}},
            }
            config = defaults.get(target_type, {"table": target_type, "columns": {}, "is_mapped": False})

        self._mapping_cache[target_type] = config
        return config

    def _col(self, target_type: str, field: str) -> str:
        cfg = self._get_table_config(target_type)
        return cfg["columns"].get(field, field)

    def _table(self, target_type: str) -> str:
        return self._get_table_config(target_type)["table"]

    def get_date_range(self) -> tuple[str, str]:
        conn = self._connect()
        cur = conn.cursor()
        t = self._table("sales")
        date_col = self._col("sales", "date")
        try:
            cur.execute(f"SELECT MIN({date_col}), MAX({date_col}) FROM [{t}]")
            row = cur.fetchone()
            conn.close()
            if row and row[0]:
                return str(row[0]), str(row[1])
        except Exception:
            pass
        conn.close()
        now = datetime.now(timezone.utc)
        return (now - timedelta(days=90)).isoformat(), now.isoformat()

    def calculate_revenue(self, start_date: str, end_date: str, product: Optional[str] = None, region: Optional[str] = None) -> dict:
        conn = self._connect()
        cur = conn.cursor()
        t = self._table("sales")
        date_col = self._col("sales", "date")
        rev_col = self._col("sales", "revenue")
        units_col = self._col("sales", "units_sold")
        order_col = self._col("sales", "order_id")
        prod_col = self._col("sales", "product_name")
        reg_col = self._col("sales", "region")

        where = f"WHERE [{date_col}] >= ? AND [{date_col}] <= ?"
        params: list = [start_date, end_date]
        if product and prod_col:
            where += f" AND [{prod_col}] = ?"
            params.append(product)
        if region and reg_col:
            where += f" AND [{reg_col}] = ?"
            params.append(region)

        cur.execute(f"SELECT SUM([{rev_col}]) as total, SUM([{units_col}]) as units, COUNT(DISTINCT [{order_col}]) as orders FROM [{t}] {where}", params)
        row = cur.fetchone()
        conn.close()
        return {"value": row["total"] or 0, "units": row["units"] or 0, "orders": row["orders"] or 0}

    def calculate_orders(self, start_date: str, end_date: str, product: Optional[str] = None, region: Optional[str] = None) -> dict:
        conn = self._connect()
        cur = conn.cursor()
        t = self._table("sales")
        date_col = self._col("sales", "date")
        order_col = self._col("sales", "order_id")
        units_col = self._col("sales", "units_sold")
        prod_col = self._col("sales", "product_name")
        reg_col = self._col("sales", "region")

        where = f"WHERE [{date_col}] >= ? AND [{date_col}] <= ?"
        params: list = [start_date, end_date]
        if product and prod_col:
            where += f" AND [{prod_col}] = ?"
            params.append(product)
        if region and reg_col:
            where += f" AND [{reg_col}] = ?"
            params.append(region)

        cur.execute(f"SELECT COUNT(DISTINCT [{order_col}]) as orders, SUM([{units_col}]) as units FROM [{t}] {where}", params)
        row = cur.fetchone()
        conn.close()
        return {"value": row["orders"] or 0, "units": row["units"] or 0}

    def calculate_aov(self, start_date: str, end_date: str) -> dict:
        rev = self.calculate_revenue(start_date, end_date)
        orders = self.calculate_orders(start_date, end_date)
        aov = rev["value"] / orders["value"] if orders["value"] > 0 else 0
        return {"value": round(aov, 2), "revenue": rev["value"], "orders": orders["value"]}

    def calculate_conversion_rate(self, start_date: str, end_date: str) -> dict:
        conn = self._connect()
        cur = conn.cursor()
        t = self._table("marketing")
        date_col = self._col("marketing", "date")
        conv_col = self._col("marketing", "conversions")
        click_col = self._col("marketing", "clicks")

        cur.execute(f"SELECT SUM([{conv_col}]) as conv, SUM([{click_col}]) as clicks FROM [{t}] WHERE [{date_col}] >= ? AND [{date_col}] <= ?", [start_date, end_date])
        row = cur.fetchone()
        conn.close()
        clicks = row["clicks"] or 0
        conv = row["conv"] or 0
        rate = (conv / clicks * 100) if clicks > 0 else 0
        return {"value": round(rate, 2), "conversions": conv, "clicks": clicks}

    def calculate_marketing_roi(self, start_date: str, end_date: str) -> dict:
        rev = self.calculate_revenue(start_date, end_date)
        conn = self._connect()
        cur = conn.cursor()
        t = self._table("marketing")
        date_col = self._col("marketing", "date")
        spend_col = self._col("marketing", "spend")

        cur.execute(f"SELECT SUM([{spend_col}]) as total_spend FROM [{t}] WHERE [{date_col}] >= ? AND [{date_col}] <= ?", [start_date, end_date])
        row = cur.fetchone()
        conn.close()
        spend = row["total_spend"] or 0
        roi = rev["value"] / spend if spend > 0 else 0
        return {"value": round(roi, 2), "revenue": rev["value"], "spend": spend}

    def calculate_all_kpis(self, current_start: str, current_end: str, previous_start: str, previous_end: str) -> dict:
        calculators = {
            "revenue": self.calculate_revenue,
            "orders": self.calculate_orders,
            "aov": self.calculate_aov,
            "conversion_rate": self.calculate_conversion_rate,
            "marketing_roi": self.calculate_marketing_roi,
        }
        results = {}
        for name, fn in calculators.items():
            current = fn(current_start, current_end)
            previous = fn(previous_start, previous_end)
            curr_val = current["value"]
            prev_val = previous["value"]
            change = ((curr_val - prev_val) / prev_val * 100) if prev_val != 0 else (None if curr_val != 0 else 0)
            results[name] = {"current": curr_val, "previous": prev_val, "change_percent": round(change, 2) if change is not None else None, "details": current}
        return results

    def get_daily_trend(self, kpi_name: str, start_date: str, end_date: str) -> list[dict]:
        conn = self._connect()
        cur = conn.cursor()
        t = self._table("sales")
        date_col = self._col("sales", "date")
        cur.execute(f"SELECT DISTINCT date([{date_col}]) as d FROM [{t}] WHERE [{date_col}] >= ? AND [{date_col}] <= ? ORDER BY d", [start_date, end_date])
        dates = [row["d"] for row in cur.fetchall()]
        conn.close()
        trend = []
        for d in dates:
            d_key = str(d)
            if kpi_name == "revenue":
                val = self.calculate_revenue(d_key, d_key)["value"]
            elif kpi_name == "orders":
                val = self.calculate_orders(d_key, d_key)["value"]
            elif kpi_name == "aov":
                val = self.calculate_aov(d_key, d_key)["value"]
            elif kpi_name == "conversion_rate":
                val = self.calculate_conversion_rate(d_key, d_key)["value"]
            elif kpi_name == "marketing_roi":
                val = self.calculate_marketing_roi(d_key, d_key)["value"]
            else:
                val = 0
            trend.append({"date": d_key, "value": round(val, 2)})
        return trend

    def get_product_breakdown(self, start_date: str, end_date: str) -> list[dict]:
        conn = self._connect()
        cur = conn.cursor()
        t = self._table("sales")
        date_col = self._col("sales", "date")
        prod_col = self._col("sales", "product_name")
        rev_col = self._col("sales", "revenue")
        units_col = self._col("sales", "units_sold")
        order_col = self._col("sales", "order_id")

        cur.execute(
            f"SELECT [{prod_col}] as product_name, SUM([{rev_col}]) as revenue, SUM([{units_col}]) as units, COUNT(DISTINCT [{order_col}]) as orders "
            f"FROM [{t}] WHERE [{date_col}] >= ? AND [{date_col}] <= ? GROUP BY [{prod_col}] ORDER BY revenue DESC",
            [start_date, end_date],
        )
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        total = sum(r["revenue"] for r in rows) or 1
        for r in rows:
            r["contribution_percent"] = round(r["revenue"] / total * 100, 1)
        return rows

    def get_region_breakdown(self, start_date: str, end_date: str) -> list[dict]:
        conn = self._connect()
        cur = conn.cursor()
        t = self._table("sales")
        date_col = self._col("sales", "date")
        reg_col = self._col("sales", "region")
        rev_col = self._col("sales", "revenue")
        units_col = self._col("sales", "units_sold")
        order_col = self._col("sales", "order_id")

        cur.execute(
            f"SELECT [{reg_col}] as region, SUM([{rev_col}]) as revenue, SUM([{units_col}]) as units, COUNT(DISTINCT [{order_col}]) as orders "
            f"FROM [{t}] WHERE [{date_col}] >= ? AND [{date_col}] <= ? GROUP BY [{reg_col}] ORDER BY revenue DESC",
            [start_date, end_date],
        )
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        total = sum(r["revenue"] for r in rows) or 1
        for r in rows:
            r["contribution_percent"] = round(r["revenue"] / total * 100, 1)
        return rows
