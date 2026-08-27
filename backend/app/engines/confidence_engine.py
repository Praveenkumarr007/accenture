"""
Confidence Engine

Calculates confidence score for insights based on:
1. Data completeness (are all sources available?)
2. Data freshness (how recent is the data?)
3. Statistical strength (how significant is the signal?)
4. Number of corroborating sources
5. Consistency between sources
6. Historical coverage
7. Contradiction level

Never present low-confidence explanations as facts.
"""


class ConfidenceEngine:
    COMPONENT_WEIGHTS = {
        "data_completeness": 0.25,
        "data_freshness": 0.15,
        "statistical_strength": 0.20,
        "source_corroboration": 0.15,
        "historical_coverage": 0.15,
        "contradiction_penalty": 0.10,
    }

    def calculate_confidence(self, data_sources_available, data_sources_required, data_freshness_hours,
                             statistical_z_score, corroborating_sources, historical_days,
                             historical_required=30, has_contradictions=False, contradiction_severity=0.0):
        completeness = len(data_sources_available) / max(len(data_sources_required), 1)
        freshness_scores = []
        for source, hours in data_freshness_hours.items():
            if source in data_sources_available:
                if hours <= 1:
                    freshness_scores.append(1.0)
                elif hours <= 4:
                    freshness_scores.append(0.9)
                elif hours <= 24:
                    freshness_scores.append(0.7)
                else:
                    freshness_scores.append(0.3)
        freshness = sum(freshness_scores) / len(freshness_scores) if freshness_scores else 0.0
        stat_strength = min(abs(statistical_z_score) / 3.0, 1.0) if statistical_z_score else 0.5
        max_corroboration = len(data_sources_required) or 1
        corroboration = min(corroborating_sources / max_corroboration, 1.0)
        history_coverage = min(historical_days / historical_required, 1.0)
        contradiction = 1.0 - contradiction_severity if has_contradictions else 1.0
        scores = {
            "data_completeness": completeness, "data_freshness": freshness,
            "statistical_strength": stat_strength, "source_corroboration": corroboration,
            "historical_coverage": history_coverage, "contradiction_penalty": contradiction,
        }
        weighted = sum(scores[c] * w for c, w in self.COMPONENT_WEIGHTS.items())
        score = round(weighted * 100, 1)
        level = "high" if score >= 80 else "medium" if score >= 50 else "low"
        return {
            "confidence_score": score, "confidence_level": level,
            "components": {k: round(v * 100, 1) for k, v in scores.items()},
            "weights": self.COMPONENT_WEIGHTS,
            "data_sources_available": data_sources_available,
            "data_sources_required": data_sources_required,
            "data_sources_missing": [s for s in data_sources_required if s not in data_sources_available],
        }

    def should_abstain(self, confidence_score, data_sources_missing):
        should = confidence_score < 40 or len(data_sources_missing) > 1
        reasons = []
        if confidence_score < 40:
            reasons.append(f"Confidence too low ({confidence_score}%)")
        if data_sources_missing:
            reasons.append(f"Missing data: {', '.join(data_sources_missing)}")
        return {"should_abstain": should, "reasons": reasons,
                "suggested_actions": ["Connect missing data sources" if data_sources_missing else None, "Wait for next data refresh", "Continue monitoring"]}

    def detect_contradictions(self, driver_findings):
        contradictions = []
        for i, d1 in enumerate(driver_findings):
            for d2 in driver_findings[i + 1:]:
                if d1.get("type") == "product" and d2.get("type") == "marketing":
                    if d1.get("change_percent", 0) * d2.get("change_percent", 0) < 0:
                        d1_dir = "up" if d1.get("change_percent", 0) > 0 else "down"
                        d2_dir = "up" if d2.get("change_percent", 0) > 0 else "down"
                        contradictions.append({
                            "factor_1": d1["name"], "factor_2": d2["name"],
                            "detail": f"{d1['name']} is {d1_dir} while {d2['name']} is {d2_dir}",
                            "severity": 0.3,
                        })
        return {
            "has_contradictions": len(contradictions) > 0,
            "contradictions": contradictions,
            "severity": max((c["severity"] for c in contradictions), default=0.0),
            "alternative_hypotheses": [{"hypothesis": c["detail"], "plausibility": "medium"} for c in contradictions],
        }
