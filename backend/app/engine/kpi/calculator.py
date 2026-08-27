"""
KPI Calculator Engine

All KPI calculations are DETERMINISTIC - no LLM involvement.
This engine computes KPI values from raw data using SQL/Python.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.sales import SalesRecord
from app.models.marketing import MarketingRecord
from app.models.kpi import KPIDefinition, KPIValue
import logging

logger = logging.getLogger(__name__)


class KPICalculator:
    """
    Deterministic KPI calculator.
    
    All calculations are performed using pandas/numpy.
    The LLM is NEVER involved in computing these values.
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_all_kpis(self, reference_date: datetime = None) -> Dict[str, dict]:
        """Calculate all KPIs for the given reference date."""
        if reference_date is None:
            reference_date = datetime.utcnow()

        kpis = {}
        kpis["revenue"] = self.calculate_revenue(reference_date)
        kpis["orders"] = self.calculate_orders(reference_date)
        kpis["aov"] = self.calculate_aov(reference_date)
        kpis["conversion_rate"] = self.calculate_conversion_rate(reference_date)
        kpis["marketing_roi"] = self.calculate_marketing_roi(reference_date)

        return kpis

    def calculate_revenue(self, reference_date: datetime) -> dict:
        """
        Revenue = SUM(units_sold * unit_price)
        Deterministic calculation from sales data.
        """
        current_start = reference_date - timedelta(days=7)
        previous_start = current_start - timedelta(days=7)

        current_data = self.db.query(SalesRecord).filter(
            SalesRecord.date >= current_start,
            SalesRecord.date <= reference_date,
        ).all()

        previous_data = self.db.query(SalesRecord).filter(
            SalesRecord.date >= previous_start,
            SalesRecord.date < current_start,
        ).all()

        current_revenue = sum(r.revenue for r in current_data)
        previous_revenue = sum(r.revenue for r in previous_data)

        change_percent = (
            ((current_revenue - previous_revenue) / previous_revenue * 100)
            if previous_revenue > 0 else 0
        )

        # Historical daily revenue for baseline
        historical_data = self.db.query(SalesRecord).filter(
            SalesRecord.date >= reference_date - timedelta(days=90),
            SalesRecord.date < current_start,
        ).all()

        daily_revenue = {}
        for r in historical_data:
            day = r.date.date()
            daily_revenue[day] = daily_revenue.get(day, 0) + r.revenue

        avg_daily = np.mean(list(daily_revenue.values())) if daily_revenue else 0
        std_daily = np.std(list(daily_revenue.values())) if daily_revenue else 0

        return {
            "name": "Revenue",
            "current_value": round(current_revenue, 2),
            "previous_value": round(previous_revenue, 2),
            "change_percent": round(change_percent, 2),
            "baseline_mean": round(avg_daily * 7, 2),
            "baseline_std": round(std_daily * 7, 2),
            "data_points": len(historical_data),
            "period_days": 7,
        }

    def calculate_orders(self, reference_date: datetime) -> dict:
        """
        Orders = COUNT(DISTINCT order_id)
        """
        current_start = reference_date - timedelta(days=7)
        previous_start = current_start - timedelta(days=7)

        current_orders = self.db.query(SalesRecord.order_id).filter(
            SalesRecord.date >= current_start,
            SalesRecord.date <= reference_date,
        ).distinct().count()

        previous_orders = self.db.query(SalesRecord.order_id).filter(
            SalesRecord.date >= previous_start,
            SalesRecord.date < current_start,
        ).distinct().count()

        change_percent = (
            ((current_orders - previous_orders) / previous_orders * 100)
            if previous_orders > 0 else 0
        )

        return {
            "name": "Orders",
            "current_value": current_orders,
            "previous_value": previous_orders,
            "change_percent": round(change_percent, 2),
            "baseline_mean": previous_orders,
            "data_points": current_orders,
            "period_days": 7,
        }

    def calculate_aov(self, reference_date: datetime) -> dict:
        """
        AOV = Revenue / Orders
        """
        revenue_data = self.calculate_revenue(reference_date)
        orders_data = self.calculate_orders(reference_date)

        current_aov = (
            revenue_data["current_value"] / orders_data["current_value"]
            if orders_data["current_value"] > 0 else 0
        )
        previous_aov = (
            revenue_data["previous_value"] / orders_data["previous_value"]
            if orders_data["previous_value"] > 0 else 0
        )

        change_percent = (
            ((current_aov - previous_aov) / previous_aov * 100)
            if previous_aov > 0 else 0
        )

        return {
            "name": "Average Order Value",
            "current_value": round(current_aov, 2),
            "previous_value": round(previous_aov, 2),
            "change_percent": round(change_percent, 2),
            "baseline_mean": round(previous_aov, 2),
            "period_days": 7,
        }

    def calculate_conversion_rate(self, reference_date: datetime) -> dict:
        """
        Conversion Rate = (Conversions / Clicks) * 100
        """
        current_start = reference_date - timedelta(days=7)
        previous_start = current_start - timedelta(days=7)

        current_data = self.db.query(MarketingRecord).filter(
            MarketingRecord.date >= current_start,
            MarketingRecord.date <= reference_date,
        ).all()

        previous_data = self.db.query(MarketingRecord).filter(
            MarketingRecord.date >= previous_start,
            MarketingRecord.date < current_start,
        ).all()

        current_clicks = sum(r.clicks for r in current_data)
        current_conversions = sum(r.conversions for r in current_data)
        current_cvr = (current_conversions / current_clicks * 100) if current_clicks > 0 else 0

        previous_clicks = sum(r.clicks for r in previous_data)
        previous_conversions = sum(r.conversions for r in previous_data)
        previous_cvr = (previous_conversions / previous_clicks * 100) if previous_clicks > 0 else 0

        change_percent = (
            ((current_cvr - previous_cvr) / previous_cvr * 100)
            if previous_cvr > 0 else 0
        )

        return {
            "name": "Conversion Rate",
            "current_value": round(current_cvr, 2),
            "previous_value": round(previous_cvr, 2),
            "change_percent": round(change_percent, 2),
            "baseline_mean": round(previous_cvr, 2),
            "current_clicks": current_clicks,
            "current_conversions": current_conversions,
            "period_days": 7,
        }

    def calculate_marketing_roi(self, reference_date: datetime) -> dict:
        """
        Marketing ROI = Revenue / Marketing Spend
        """
        revenue_data = self.calculate_revenue(reference_date)

        current_start = reference_date - timedelta(days=7)
        previous_start = current_start - timedelta(days=7)

        current_spend = self.db.query(
            func.sum(MarketingRecord.spend)
        ).filter(
            MarketingRecord.date >= current_start,
            MarketingRecord.date <= reference_date,
        ).scalar() or 0

        previous_spend = self.db.query(
            func.sum(MarketingRecord.spend)
        ).filter(
            MarketingRecord.date >= previous_start,
            MarketingRecord.date < current_start,
        ).scalar() or 0

        current_roi = (
            revenue_data["current_value"] / current_spend
            if current_spend > 0 else 0
        )
        previous_roi = (
            revenue_data["previous_value"] / previous_spend
            if previous_spend > 0 else 0
        )

        change_percent = (
            ((current_roi - previous_roi) / previous_roi * 100)
            if previous_roi > 0 else 0
        )

        return {
            "name": "Marketing ROI",
            "current_value": round(current_roi, 2),
            "previous_value": round(previous_roi, 2),
            "change_percent": round(change_percent, 2),
            "baseline_mean": round(previous_roi, 2),
            "current_spend": round(current_spend, 2),
            "period_days": 7,
        }

    def get_kpi_trend(self, kpi_name: str, days: int = 30) -> List[dict]:
        """Get daily KPI trend for the last N days."""
        end_date = datetime.utcnow()
        trend = []

        for i in range(days):
            day = end_date - timedelta(days=days - i)
            day_start = day.replace(hour=0, minute=0, second=0)
            day_end = day_start + timedelta(days=1)

            if kpi_name in ["Revenue", "revenue"]:
                value = self.db.query(func.sum(SalesRecord.revenue)).filter(
                    SalesRecord.date >= day_start, SalesRecord.date < day_end
                ).scalar() or 0
            elif kpi_name in ["Orders", "orders"]:
                value = self.db.query(func.count(SalesRecord.order_id.distinct())).filter(
                    SalesRecord.date >= day_start, SalesRecord.date < day_end
                ).scalar() or 0
            elif kpi_name in ["Conversion Rate", "conversion_rate"]:
                clicks = self.db.query(func.sum(MarketingRecord.clicks)).filter(
                    MarketingRecord.date >= day_start, MarketingRecord.date < day_end
                ).scalar() or 0
                conv = self.db.query(func.sum(MarketingRecord.conversions)).filter(
                    MarketingRecord.date >= day_start, MarketingRecord.date < day_end
                ).scalar() or 0
                value = (conv / clicks * 100) if clicks > 0 else 0
            else:
                value = 0

            trend.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "value": round(float(value), 2),
            })

        return trend
