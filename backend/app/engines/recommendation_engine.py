"""
Recommendation Engine

Generates actionable recommendations based on detected drivers.
Only generates recommendations when drivers are sufficiently grounded.
"""

RECOMMENDATION_TEMPLATES = {
    "Laptop sales": {"lever": "Inventory replenishment", "action": "Replenish laptop inventory to meet demand.", "owner": "Supply Chain Manager", "monitoring_plan": "Monitor laptop stock and revenue daily for 7 days."},
    "Smartphone sales": {"lever": "Product marketing", "action": "Review smartphone pricing and promotional strategy.", "owner": "Sales Manager", "monitoring_plan": "Track smartphone sales weekly."},
    "Headphones sales": {"lever": "Promotion optimization", "action": "Evaluate headphone bundle offers.", "owner": "Sales Manager", "monitoring_plan": "Monitor headphone unit sales."},
    "Smartwatch sales": {"lever": "Product positioning", "action": "Review smartwatch market positioning.", "owner": "Sales Manager", "monitoring_plan": "Track smartwatch sales trend."},
    "Tablet sales": {"lever": "Demand generation", "action": "Launch targeted tablet campaign.", "owner": "Marketing Manager", "monitoring_plan": "Monitor tablet orders and campaign ROI."},
    "North region": {"lever": "Regional strategy", "action": "Investigate North region performance.", "owner": "Sales Director", "monitoring_plan": "Review North region KPIs daily."},
    "South region": {"lever": "Regional strategy", "action": "Investigate South region performance.", "owner": "Sales Director", "monitoring_plan": "Review South region KPIs daily."},
    "East region": {"lever": "Regional strategy", "action": "Investigate East region performance.", "owner": "Sales Director", "monitoring_plan": "Review East region KPIs daily."},
    "West region": {"lever": "Regional strategy", "action": "Investigate West region performance.", "owner": "Sales Director", "monitoring_plan": "Review West region KPIs daily."},
    "Marketing spend": {"lever": "Budget allocation", "action": "Review marketing budget and restore high-performing campaigns.", "owner": "Marketing Manager", "monitoring_plan": "Track marketing spend and conversions daily."},
    "Website traffic": {"lever": "Traffic generation", "action": "Increase digital marketing efforts.", "owner": "Marketing Manager", "monitoring_plan": "Monitor daily traffic and conversions."},
    "Laptop inventory": {"lever": "Inventory replenishment", "action": "Urgently replenish laptop inventory in North and West warehouses.", "owner": "Supply Chain Manager", "monitoring_plan": "Monitor laptop stock daily for 7 days."},
    "Seasonality": {"lever": "Seasonal planning", "action": "Adjust forecasts for seasonal patterns.", "owner": "Sales Director", "monitoring_plan": "Monitor KPI trends against baselines."},
    "Other factors": {"lever": "Investigation", "action": "Investigate additional factors.", "owner": "Analytics Team", "monitoring_plan": "Monitor for additional signals."},
}


class RecommendationEngine:
    def generate_recommendations(self, drivers, kpi_name, total_impact, confidence_level):
        recommendations = []
        for driver in drivers:
            if driver.get("contribution_percent", 0) < 5:
                continue
            template = RECOMMENDATION_TEMPLATES.get(driver["name"], {"lever": "Investigation", "action": f"Investigate {driver['name']} impact.", "owner": "Analytics Team", "monitoring_plan": f"Monitor {driver['name']}."})
            impact_value = abs(total_impact * driver["contribution_percent"] / 100)
            rec_conf = driver.get("confidence", 0.7)
            if confidence_level == "low":
                rec_conf *= 0.5
            elif confidence_level == "medium":
                rec_conf *= 0.8
            recommendations.append({
                "driver_name": driver["name"], "lever": template["lever"], "action": template["action"],
                "expected_impact": f"Potential recovery of {impact_value:,.0f}",
                "expected_impact_value": round(impact_value, 2), "owner": template["owner"],
                "confidence": round(rec_conf, 2), "monitoring_plan": template["monitoring_plan"],
                "priority": "high" if driver.get("contribution_percent", 0) > 30 else "medium", "status": "pending",
            })
        recommendations.sort(key=lambda r: r["confidence"], reverse=True)
        return recommendations
