"""
Anomaly Detection Engine

Uses deterministic/statistical methods:
1. Rolling mean and standard deviation for baseline
2. Z-score for statistical significance
3. Historical baseline comparison
"""
import math


class AnomalyDetector:
    def __init__(self, window_size: int = 14):
        self.window_size = window_size

    @staticmethod
    def mean(values):
        return sum(values) / len(values) if values else 0.0

    @staticmethod
    def std_dev(values):
        if len(values) < 2:
            return 0.0
        m = sum(values) / len(values)
        return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))

    def z_score(self, value, values):
        m = self.mean(values)
        sd = self.std_dev(values)
        return (value - m) / sd if sd > 0 else 0.0

    def detect_anomalies(self, values, dates, threshold_z=2.0, baseline_days=14):
        if len(values) < 3:
            return []
        baseline = values[:baseline_days] if len(values) >= baseline_days else values[:len(values) // 2]
        baseline_mean = self.mean(baseline)
        baseline_std = self.std_dev(baseline)
        anomalies = []
        for val, date in zip(values, dates):
            z = (val - baseline_mean) / baseline_std if baseline_std > 0 else 0.0
            expected = baseline_mean
            deviation = ((val - expected) / expected * 100) if expected != 0 else 0
            anomalies.append({
                "date": date, "value": val, "expected_value": round(expected, 2),
                "z_score": round(z, 3), "deviation_percent": round(deviation, 2),
                "is_significant": abs(z) >= threshold_z, "detection_method": "rolling_z_score",
                "baseline_mean": round(baseline_mean, 2), "baseline_std": round(baseline_std, 2),
            })
        return anomalies

    def detect_kpi_anomaly(self, current_value, historical_values, historical_dates):
        if len(historical_values) < 5:
            return {"is_anomaly": False, "confidence": "low", "reason": "insufficient_history",
                    "historical_coverage": len(historical_values), "required_coverage": 30}
        baseline_mean = self.mean(historical_values)
        baseline_std = self.std_dev(historical_values)
        z = (current_value - baseline_mean) / baseline_std if baseline_std > 0 else 0.0
        return {
            "is_anomaly": abs(z) >= 2.0, "current_value": current_value,
            "expected_value": round(baseline_mean, 2), "z_score": round(z, 3),
            "deviation_percent": round(((current_value - baseline_mean) / baseline_mean * 100) if baseline_mean != 0 else 0, 2),
            "baseline_mean": round(baseline_mean, 2), "baseline_std": round(baseline_std, 2),
            "detection_method": "z_score",
            "confidence": "high" if len(historical_values) >= 30 else "medium" if len(historical_values) >= 14 else "low",
            "historical_coverage": len(historical_values), "required_coverage": 30,
        }
