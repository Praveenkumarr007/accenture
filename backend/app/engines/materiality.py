"""
Materiality Engine

Determines whether a KPI movement is material.
Uses composite scoring: percentage change + business impact + statistical significance.
"""


class MaterialityEngine:
    def calculate_priority_score(self, change_percent, absolute_impact, historical_volatility=0.1, data_points=30):
        abs_change = abs(change_percent)
        pct_score = min(abs_change / 30.0, 1.0) * 40
        if absolute_impact >= 1000000:
            impact_score = 30
        elif absolute_impact >= 500000:
            impact_score = 20
        elif absolute_impact >= 100000:
            impact_score = 10
        else:
            impact_score = 5
        stat_score = 20 if data_points >= 30 and abs_change > historical_volatility * 2 else 10 if data_points >= 14 else 3
        total = pct_score + impact_score + stat_score
        priority = "CRITICAL" if total >= 70 else "HIGH" if total >= 50 else "MEDIUM" if total >= 30 else "LOW" if total >= 15 else "NONE"
        return {
            "priority": priority, "total_score": round(total, 1),
            "percentage_score": round(pct_score, 1), "impact_score": round(impact_score, 1),
            "statistical_score": round(stat_score, 1), "is_material": priority in ("CRITICAL", "HIGH", "MEDIUM"),
            "change_percent": change_percent, "absolute_impact": absolute_impact,
            "historical_volatility": historical_volatility,
        }

    def assess_materiality(self, kpi_name, current_value, previous_value, threshold_percent=10.0,
                           historical_volatility=0.1, data_points=30):
        change_percent = ((current_value - previous_value) / previous_value * 100) if previous_value != 0 else 0
        absolute_impact = abs(current_value - previous_value)
        result = self.calculate_priority_score(change_percent, absolute_impact, historical_volatility, data_points)
        return {
            "kpi_name": kpi_name, "current_value": current_value, "previous_value": previous_value,
            "change_percent": round(change_percent, 2), "absolute_impact": round(absolute_impact, 2),
            "threshold_percent": threshold_percent, "passes_threshold": abs(change_percent) >= threshold_percent,
            **result,
        }
