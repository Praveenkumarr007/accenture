from typing import Dict, List, Optional
import json
from datetime import datetime
import os

from sqlalchemy.orm import Session

from ..models.database_models import LLMLog
from ..core.config import settings


class LLMService:
    def __init__(self, db: Session):
        self.db = db
        self.client = None
        self._init_client()

    def _init_client(self):
        if settings.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception:
                self.client = None

    def generate_narrative(
        self, structured_context: Dict, persona: str = "CEO"
    ) -> Dict:
        start_time = datetime.utcnow()

        if not self.client:
            narrative = self._fallback_narrative(structured_context, persona)
            self._log_usage(
                "narrative_fallback", 0, 0, 0.0,
                ((datetime.utcnow() - start_time).total_seconds() * 1000),
                False, "fallback"
            )
            return narrative

        try:
            system_prompt = self._get_system_prompt(persona)
            user_prompt = self._build_user_prompt(structured_context, persona)

            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            tokens_in = response.usage.prompt_tokens if response.usage else 0
            tokens_out = response.usage.completion_tokens if response.usage else 0
            cost = self._estimate_cost(tokens_in, tokens_out)

            self._log_usage(
                "narrative_generation", tokens_in, tokens_out, cost, latency,
                True, settings.OPENAI_MODEL
            )

            return result

        except Exception as e:
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._log_usage(
                "narrative_generation", 0, 0, 0.0, latency,
                False, settings.OPENAI_MODEL
            )
            return self._fallback_narrative(structured_context, persona)

    def generate_assistant_response(
        self, question: str, context: Dict
    ) -> Dict:
        if not self.client:
            return {
                "response": self._fallback_assistant(question, context),
                "model": "fallback",
                "tokens_used": 0,
                "cost": 0,
            }

        try:
            system = (
                "You are a business intelligence assistant for ShopSmart. "
                "Answer questions using ONLY the provided evidence and data. "
                "Never invent numbers or data sources. "
                "If evidence is insufficient, say so clearly. "
                "Always cite your sources."
            )

            prompt = (
                f"Context: {json.dumps(context, default=str)}\n\n"
                f"Question: {question}\n\n"
                f"Provide a concise, evidence-based response."
            )

            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
                temperature=0.3,
            )

            result_text = response.choices[0].message.content
            tokens_in = response.usage.prompt_tokens if response.usage else 0
            tokens_out = response.usage.completion_tokens if response.usage else 0
            cost = self._estimate_cost(tokens_in, tokens_out)

            self._log_usage(
                "assistant_chat", tokens_in, tokens_out, cost, 0,
                True, settings.OPENAI_MODEL
            )

            return {
                "response": result_text,
                "model": settings.OPENAI_MODEL,
                "tokens_used": tokens_in + tokens_out,
                "cost": cost,
            }

        except Exception:
            return {
                "response": self._fallback_assistant(question, context),
                "model": "fallback",
                "tokens_used": 0,
                "cost": 0,
            }

    def _get_system_prompt(self, persona: str) -> str:
        base = (
            "You are a business intelligence analyst for ShopSmart, an online retail company. "
            "Generate concise, data-driven narratives based on the provided evidence. "
            "NEVER invent numbers or data. Use ONLY the values provided in the context. "
            "Clearly state uncertainty when confidence is low."
        )

        if persona == "CEO":
            return (
                base + "\n\n"
                "You are addressing the CEO. Focus on:\n"
                "- Business impact and revenue implications\n"
                "- Major drivers and their contribution\n"
                "- Recommended actions with expected ROI\n"
                "- Strategic implications\n"
                "Keep the narrative executive-level and concise."
            )
        elif persona == "Marketing Manager":
            return (
                base + "\n\n"
                "You are addressing the Marketing Manager. Focus on:\n"
                "- Campaign performance and channel analysis\n"
                "- Traffic, conversions, and marketing spend\n"
                "- Channel-specific recommendations\n"
                "- Marketing ROI implications\n"
                "Provide tactical, marketing-focused insights."
            )
        return base

    def _build_user_prompt(self, context: Dict, persona: str) -> str:
        return (
            f"Based on the following analysis, generate a {persona}-specific narrative.\n\n"
            f"KPI: {context.get('kpi_name', 'Unknown')}\n"
            f"Current Value: {context.get('current_value', 0)}\n"
            f"Previous Value: {context.get('previous_value', 0)}\n"
            f"Change: {context.get('change_percent', 0)}%\n"
            f"Priority: {context.get('priority', 'Unknown')}\n"
            f"Confidence: {context.get('confidence', 0)}%\n\n"
            f"Top Drivers:\n"
        ) + "\n".join(
            f"- {d['name']}: {d['contribution_percent']}% contribution"
            for d in context.get("drivers", [])[:5]
        ) + (
            f"\n\nEvidence:\n"
        ) + "\n".join(
            f"- [{e['source']}] {e['metric']}: {e['description']}"
            for e in context.get("evidence", [])[:6]
        ) + (
            f"\n\nRespond in JSON format:\n"
            f'{{"narrative": "...", "key_points": ["..."], "urgency": "high/medium/low"}}'
        )

    def _fallback_narrative(self, context: Dict, persona: str) -> Dict:
        kpi = context.get("kpi_name", "KPI")
        change = context.get("change_percent", 0)
        direction = "declined" if change < 0 else "increased"
        abs_change = abs(change)

        drivers = context.get("drivers", [])
        driver_text = ""
        if drivers:
            top = drivers[0]
            driver_text = f"The primary driver is {top['name']}, contributing {top['contribution_percent']}%."

        confidence = context.get("confidence", 0)
        confidence_note = ""
        if confidence < 50:
            confidence_note = " Note: Confidence is low due to limited available evidence."

        narrative = (
            f"{kpi} has {direction} by {abs_change:.1f}%. "
            f"{driver_text}"
            f"{confidence_note}"
        )

        if persona == "Marketing Manager":
            narrative += " Focus on marketing-related factors and campaign performance."

        return {
            "narrative": narrative,
            "key_points": [
                f"{kpi} {direction} {abs_change:.1f}%",
                f"Primary driver: {drivers[0]['name']}" if drivers else "No clear driver identified",
                f"Confidence: {confidence}%",
            ],
            "urgency": "high" if abs_change > 20 else "medium" if abs_change > 10 else "low",
            "source": "fallback",
        }

    def _fallback_assistant(self, question: str, context: Dict) -> str:
        q_lower = question.lower()

        if "why" in q_lower and "revenue" in q_lower:
            change = context.get("change_percent", 0)
            drivers = context.get("drivers", [])
            if drivers:
                top = drivers[0]
                return (
                    f"Revenue declined by {abs(change):.1f}%. "
                    f"The primary driver is {top['name']} with {top['contribution_percent']}% contribution. "
                    f"This is based on deterministic analysis of sales, marketing, and inventory data."
                )
            return f"Revenue changed by {change:.1f}%. Additional data analysis may be needed to identify the root cause."

        if "what" in q_lower and ("action" in q_lower or "do" in q_lower):
            return "Based on the analysis, the recommended actions are focused on addressing the primary drivers. Please check the Recommendations section for detailed action items."

        return "I can help analyze KPI movements and their drivers. Please ask a specific question about a KPI change or its causes."

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        if settings.OPENAI_MODEL == "gpt-4o-mini":
            return (input_tokens * 0.00015 + output_tokens * 0.0006) / 1000
        return (input_tokens * 0.005 + output_tokens * 0.0015) / 1000

    def _log_usage(
        self, request_type: str, input_tokens: int, output_tokens: int,
        cost: float, latency_ms: float, success: bool, model: str
    ):
        log = LLMLog(
            request_type=request_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=cost,
            latency_ms=latency_ms,
            success=success,
            model=model,
        )
        self.db.add(log)
        self.db.commit()
