"""
Main Analysis Orchestrator

Ties together all engines into a single analysis pipeline:
1. Calculate KPIs
2. Detect anomalies
3. Assess materiality
4. Analyze drivers
5. Collect evidence
6. Calculate confidence
7. Detect contradictions
8. Generate recommendations
9. Build persona-specific narratives
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.engines.kpi_engine import KPIEngine
from app.engines.anomaly_detector import AnomalyDetector
from app.engines.materiality import MaterialityEngine
from app.engines.driver_analyzer import DriverAnalyzer
from app.engines.confidence_engine import ConfidenceEngine
from app.engines.evidence_engine import EvidenceEngine
from app.engines.recommendation_engine import RecommendationEngine
from app.core.kpi_contracts import KPI_CONTRACTS, PERSONA_FOCUS, ROLE_KPI_ACCESS


class AnalysisOrchestrator:
    """Main orchestration service for KPI analysis."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.kpi_engine = KPIEngine(db_path)
        self.anomaly_detector = AnomalyDetector()
        self.materiality_engine = MaterialityEngine()
        self.driver_analyzer = DriverAnalyzer(db_path)
        self.confidence_engine = ConfidenceEngine()
        self.evidence_engine = EvidenceEngine()
        self.recommendation_engine = RecommendationEngine()

    def run_full_analysis(
        self,
        kpi_name: str,
        current_start: str,
        current_end: str,
        previous_start: str,
        previous_end: str,
        persona: str = "CEO",
        user_role: str = "CEO",
    ) -> dict:
        """Run complete analysis pipeline for a KPI."""
        contract = KPI_CONTRACTS.get(kpi_name)
        if not contract:
            return {"error": f"Unknown KPI: {kpi_name}"}

        if user_role not in contract.get("allowed_roles", []):
            return {
                "error": "access_restricted",
                "message": f"Access restricted. You do not have permission to view {kpi_name}.",
                "required_roles": contract.get("allowed_roles", []),
            }

        current = self.kpi_engine.calculate_all_kpis(current_start, current_end, previous_start, previous_end)
        kpi_data = current.get(kpi_name, {})
        current_value = kpi_data.get("current", 0)
        previous_value = kpi_data.get("previous", 0)
        change_percent = kpi_data.get("change_percent", 0)

        materiality = self.materiality_engine.assess_materiality(
            kpi_name=kpi_name,
            current_value=current_value,
            previous_value=previous_value,
            threshold_percent=contract.get("threshold_percent", 10.0),
        )

        daily_trend = self.kpi_engine.get_daily_trend(kpi_name, previous_start, current_end)
        trend_values = [d["value"] for d in daily_trend]
        trend_dates = [d["date"] for d in daily_trend]

        anomaly = self.anomaly_detector.detect_kpi_anomaly(
            current_value=current_value,
            historical_values=trend_values[:-1] if trend_values else [],
            historical_dates=trend_dates[:-1] if trend_dates else [],
        )

        driver_result = self.driver_analyzer.analyze_drivers(
            current_start=current_start,
            current_end=current_end,
            previous_start=previous_start,
            previous_end=previous_end,
            total_change=current_value - previous_value,
            daily_values=trend_values,
        )

        contradiction_result = self.confidence_engine.detect_contradictions(driver_result["drivers"])

        available_sources = ["sales", "marketing", "inventory"]
        required_sources = ["sales", "marketing"]
        missing = [s for s in required_sources if s not in available_sources]

        freshness = {
            "sales": 1.0,
            "marketing": 4.0,
            "inventory": 0.5,
        }

        confidence_result = self.confidence_engine.calculate_confidence(
            data_sources_available=available_sources,
            data_sources_required=required_sources,
            data_freshness_hours=freshness,
            statistical_z_score=anomaly.get("z_score", 0),
            corroborating_sources=len(available_sources),
            historical_days=len(trend_values),
            has_contradictions=contradiction_result["has_contradictions"],
            contradiction_severity=contradiction_result["severity"],
        )

        abstention = self.confidence_engine.should_abstain(
            confidence_score=confidence_result["confidence_score"],
            data_sources_missing=confidence_result.get("data_sources_missing", []),
        )

        evidence = self.evidence_engine.collect_evidence(
            kpi_name=kpi_name,
            current_data={
                "sales": self.kpi_engine.calculate_revenue(current_start, current_end),
                "marketing": self.kpi_engine.calculate_conversion_rate(current_start, current_end),
                "inventory": {"avg_stock": 500},
                "timestamp": current_end,
            },
            previous_data={
                "sales": self.kpi_engine.calculate_revenue(previous_start, previous_end),
                "marketing": self.kpi_engine.calculate_conversion_rate(previous_start, previous_end),
                "inventory": {"avg_stock": 1200},
                "timestamp": previous_end,
            },
            drivers=driver_result["drivers"],
            data_sources_info={"sales": True, "marketing": True, "inventory": True},
        )

        recommendations = []
        if not abstention["should_abstain"]:
            recommendations = self.recommendation_engine.generate_recommendations(
                drivers=driver_result["drivers"],
                kpi_name=kpi_name,
                total_impact=abs(current_value - previous_value),
                confidence_level=confidence_result["confidence_level"],
            )

        persona_focus = PERSONA_FOCUS.get(persona, PERSONA_FOCUS["CEO"])

        narrative = self._build_narrative(
            kpi_name=kpi_name,
            contract=contract,
            current_value=current_value,
            previous_value=previous_value,
            change_percent=change_percent,
            materiality=materiality,
            drivers=driver_result["drivers"],
            confidence=confidence_result,
            abstention=abstention,
            persona=persona,
            persona_focus=persona_focus,
        )

        return {
            "kpi_name": kpi_name,
            "kpi_description": contract["description"],
            "current_value": current_value,
            "previous_value": previous_value,
            "change_percent": change_percent,
            "materiality": materiality,
            "anomaly": anomaly,
            "drivers": driver_result["drivers"],
            "total_drivers": driver_result["total_drivers"],
            "explained_percent": driver_result["explained_percent"],
            "evidence": evidence,
            "confidence": confidence_result,
            "abstention": abstention,
            "contradictions": contradiction_result,
            "recommendations": recommendations,
            "narrative": narrative,
            "persona": persona,
            "data_sources": available_sources,
            "date_range": {
                "current": f"{current_start} to {current_end}",
                "previous": f"{previous_start} to {previous_end}",
            },
            "product_breakdown": self.kpi_engine.get_product_breakdown(current_start, current_end),
            "region_breakdown": self.kpi_engine.get_region_breakdown(current_start, current_end),
            "trend": daily_trend,
        }

    def _build_narrative(
        self,
        kpi_name: str,
        contract: dict,
        current_value: float,
        previous_value: float,
        change_percent: float,
        materiality: dict,
        drivers: list[dict],
        confidence: dict,
        abstention: dict,
        persona: str,
        persona_focus: dict,
    ) -> str:
        """Build persona-specific narrative.

        This is the ONLY part where the LLM should be used.
        For this demo, we generate deterministic narratives.
        """
        direction = "increased" if change_percent > 0 else "decreased"
        abs_change = abs(change_percent)
        priority = materiality.get("priority", "LOW")

        if abstention["should_abstain"]:
            missing = confidence.get("data_sources_missing", [])
            narrative = (
                f"⚠ {kpi_name} {direction} {abs_change:.1f}%, but the available evidence is insufficient "
                f"to determine the underlying root cause with high confidence.\n\n"
                f"Confidence: {confidence['confidence_score']}%\n"
                f"Status: INSUFFICIENT EVIDENCE\n\n"
            )
            if missing:
                narrative += f"Missing data sources: {', '.join(missing)}\n"
            narrative += "\nSuggested actions: Request additional data or continue monitoring."
            return narrative

        top_drivers = [d for d in drivers if d.get("contribution_percent", 0) >= 5][:3]

        if persona == "CEO":
            narrative = f"**{kpi_name} {direction} {abs_change:.1f}%** (Priority: {priority})\n\n"
            narrative += "Key drivers:\n"
            for d in top_drivers:
                narrative += f"- {d['name']}: {d['contribution_percent']}% contribution\n"
            narrative += f"\nConfidence: {confidence['confidence_score']}%\n"
            if recommendations := self.recommendation_engine.generate_recommendations(
                drivers, kpi_name, abs(current_value - previous_value), confidence["confidence_level"]
            ):
                narrative += f"\nTop action: {recommendations[0]['action']}\n"
                narrative += f"Owner: {recommendations[0]['owner']}\n"
                narrative += f"Expected impact: {recommendations[0]['expected_impact']}\n"
        else:
            narrative = f"**{kpi_name} {direction} {abs_change:.1f}%**\n\n"
            narrative += "Detailed driver breakdown:\n"
            for d in drivers[:5]:
                narrative += f"- {d['name']}: {d['contribution_percent']}% ({d.get('change_percent', 0):.1f}% change)\n"
            narrative += f"\nConfidence: {confidence['confidence_score']}%\n"

        return narrative

    def get_overview(self, persona: str = "CEO", user_role: str = "CEO") -> dict:
        """Get overview dashboard data."""
        now = datetime(2025, 8, 27, tzinfo=timezone.utc)
        current_start = (now - timedelta(days=7)).isoformat()
        current_end = now.isoformat()
        previous_start = (now - timedelta(days=14)).isoformat()
        previous_end = (now - timedelta(days=7)).isoformat()

        allowed_kpis = ROLE_KPI_ACCESS.get(user_role, [])
        kpi_cards = []

        for kpi_name, contract in KPI_CONTRACTS.items():
            if kpi_name not in allowed_kpis:
                continue

            data = self.kpi_engine.calculate_all_kpis(current_start, current_end, previous_start, previous_end)
            kpi = data.get(kpi_name, {})

            materiality = self.materiality_engine.assess_materiality(
                kpi_name=kpi_name,
                current_value=kpi.get("current", 0),
                previous_value=kpi.get("previous", 0),
                threshold_percent=contract.get("threshold_percent", 10.0),
            )

            trend = self.kpi_engine.get_daily_trend(kpi_name, previous_start, current_end)
            trend_values = [d["value"] for d in trend]

            kpi_cards.append({
                "id": kpi_name,
                "name": contract["name"],
                "value": kpi.get("current", 0),
                "previous_value": kpi.get("previous", 0),
                "change_percent": kpi.get("change_percent", 0),
                "priority": materiality["priority"],
                "status": "material" if materiality["is_material"] else "normal",
                "trend": trend_values[-14:],
            })

        primary_insight = None
        for card in kpi_cards:
            if card["priority"] in ("CRITICAL", "HIGH"):
                analysis = self.run_full_analysis(
                    kpi_name=card["id"],
                    current_start=current_start,
                    current_end=current_end,
                    previous_start=previous_start,
                    previous_end=previous_end,
                    persona=persona,
                    user_role=user_role,
                )
                primary_insight = analysis
                break

        return {
            "kpi_cards": kpi_cards,
            "primary_insight": primary_insight,
            "persona": persona,
            "date_range": {
                "current": f"{current_start[:10]} to {current_end[:10]}",
                "previous": f"{previous_start[:10]} to {previous_end[:10]}",
            },
        }
