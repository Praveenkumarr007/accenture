"""LLM Service - Natural language explanation only.

GUARDRAILS:
- Never invent numbers
- Never invent evidence
- Never invent data sources
- Never calculate KPI values
- Never claim certainty when confidence is low
- Only use provided evidence
- Explicitly state uncertainty
"""

import json
import time
from typing import Dict, Optional
from datetime import datetime, timezone
from app.core.config import get_settings

settings = get_settings()

_llm_cache = {}


def _get_cache_key(request_type: str, context_hash: str) -> str:
    return f"{request_type}:{context_hash}"


def _check_cache(cache_key: str) -> Optional[Dict]:
    if cache_key in _llm_cache:
        entry = _llm_cache[cache_key]
        age = (datetime.now(timezone.utc) - entry["timestamp"]).seconds
        if age < settings.LLM_CACHE_TTL:
            entry["cached"] = True
            return entry["data"]
        del _llm_cache[cache_key]
    return None


def _store_cache(cache_key: str, data: Dict):
    _llm_cache[cache_key] = {
        "data": data,
        "timestamp": datetime.now(timezone.utc),
    }


def generate_insight_narrative(context: Dict) -> Dict:
    if not settings.ENABLE_LLM or settings.OPENAI_API_KEY == "sk-placeholder":
        return _generate_fallback_narrative(context)

    cache_key = _get_cache_key("narrative", str(hash(json.dumps(context, default=str, sort_keys=True))))
    cached = _check_cache(cache_key)
    if cached:
        return cached

    try:
        import openai
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        system_prompt = """You are a business intelligence narrator. You explain KPI movements using ONLY the data provided.

RULES:
1. Never invent numbers - use only provided values
2. Never invent evidence - use only provided evidence items
3. Never invent data sources - reference only provided sources
4. When confidence is low, explicitly state uncertainty
5. Be concise and business-focused
6. Tailor language to the specified persona
7. Always reference specific evidence
8. Never claim certainty when the data doesn't support it

Respond with JSON: {"narrative": "...", "key_points": ["..."]}"""

        user_prompt = f"""Explain this KPI movement:

KPI: {context['kpi_name']}
Current Value: {context['current_value']:,.0f}
Previous Value: {context['previous_value']:,.0f}
Change: {context['change_percent']:.1f}%
Priority: {context['priority_level']}
Confidence: {context['confidence']:.0f}%

Top Drivers:
{json.dumps(context.get('drivers', [])[:3], indent=2)}

Evidence:
{json.dumps(context.get('evidence', [])[:5], indent=2)}

Persona: {context.get('persona', 'CEO')}

Generate a clear, evidence-based narrative."""

        start_time = time.time()
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=settings.OPENAI_MAX_TOKENS,
            response_format={"type": "json_object"},
        )
        latency_ms = (time.time() - start_time) * 1000

        result = json.loads(response.choices[0].message.content)
        tokens_used = response.usage.total_tokens if response.usage else 0
        estimated_cost = tokens_used * 0.00003

        _store_cache(cache_key, result)

        return {
            "narrative": result.get("narrative", ""),
            "key_points": result.get("key_points", []),
            "tokens_used": tokens_used,
            "estimated_cost": estimated_cost,
            "latency_ms": latency_ms,
            "cached": False,
        }

    except Exception as e:
        return _generate_fallback_narrative(context, error=str(e))


def generate_assistant_response(message: str, context: Dict, persona: str = "CEO") -> Dict:
    if not settings.ENABLE_LLM or settings.OPENAI_API_KEY == "sk-placeholder":
        return _generate_fallback_assistant(message, context, persona)

    cache_key = _get_cache_key("assistant", str(hash(message + str(context.get("kpi_name", "")))))
    cached = _check_cache(cache_key)
    if cached:
        return cached

    try:
        import openai
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        system_prompt = f"""You are a business intelligence assistant for a {persona}.
Answer questions using ONLY the provided data and evidence.

RULES:
1. Never invent data or numbers
2. Reference specific evidence items
3. State confidence levels
4. Be concise and actionable
5. If you cannot answer from available data, say so
6. Tailor response complexity to the persona"""

        user_prompt = f"""Question: {message}

Available Context:
KPI: {context.get('kpi_name', 'N/A')}
Current Value: {context.get('current_value', 0):,.0f}
Change: {context.get('change_percent', 0):.1f}%
Confidence: {context.get('confidence', 0):.0f}%

Drivers: {json.dumps(context.get('drivers', [])[:5], indent=2)}
Evidence: {json.dumps(context.get('evidence', [])[:5], indent=2)}

Provide a clear, evidence-based answer."""

        start_time = time.time()
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=settings.OPENAI_MAX_TOKENS,
        )
        latency_ms = (time.time() - start_time) * 1000

        result_text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else 0
        estimated_cost = tokens_used * 0.00003

        result = {
            "response": result_text,
            "tokens_used": tokens_used,
            "estimated_cost": estimated_cost,
            "latency_ms": latency_ms,
            "cached": False,
        }
        _store_cache(cache_key, result)
        return result

    except Exception as e:
        return _generate_fallback_assistant(message, context, persona, error=str(e))


def _generate_fallback_narrative(context: Dict, error: Optional[str] = None) -> Dict:
    kpi_name = context.get("kpi_name", "KPI")
    change = context.get("change_percent", 0)
    direction = "declined" if change < 0 else "increased"
    drivers = context.get("drivers", [])
    confidence = context.get("confidence", 0)

    parts = [f"{kpi_name} {direction} {abs(change):.1f}% over the past week."]

    if drivers:
        top = drivers[0] if drivers else None
        if top:
            parts.append(
                f"The primary driver is {top.get('name', 'unknown')} "
                f"contributing {top.get('contribution_percent', 0):.0f}% to the movement."
            )

    if isinstance(confidence, dict):
        conf_val = confidence.get("confidence", 0)
    else:
        conf_val = confidence

    if conf_val < 50:
        parts.append("Confidence is low. Additional data may be needed for a definitive conclusion.")
    else:
        parts.append(f"Confidence level: {conf_val:.0f}%.")

    if error:
        parts.append(f"[AI narrative service unavailable: {error}]")

    return {
        "narrative": " ".join(parts),
        "key_points": [f"{kpi_name} {direction} {abs(change):.1f}%"],
        "tokens_used": 0,
        "estimated_cost": 0,
        "latency_ms": 0,
        "cached": False,
        "fallback": True,
    }


def _generate_fallback_assistant(message: str, context: Dict, persona: str, error: Optional[str] = None) -> Dict:
    kpi_name = context.get("kpi_name", "KPI")
    change = context.get("change_percent", 0)
    drivers = context.get("drivers", [])
    evidence = context.get("evidence", [])

    msg_lower = message.lower()

    if "why" in msg_lower or "cause" in msg_lower or "reason" in msg_lower:
        if drivers:
            top_drivers = drivers[:3]
            driver_text = "\n".join(
                f"- {d['name']}: {d['contribution_percent']:.0f}% contribution"
                for d in top_drivers
            )
            response = f"Based on the analysis, {kpi_name} changed {abs(change):.1f}% due to:\n{driver_text}"
        else:
            response = f"The system detected a {abs(change):.1f}% change in {kpi_name} but no specific drivers were identified."
    elif "action" in msg_lower or "do" in msg_lower:
        response = f"The recommended primary action is to address the top contributing factor to the {kpi_name} movement."
    elif "evidence" in msg_lower:
        if evidence:
            ev_text = "\n".join(f"- {e['source']}: {e['detail']}" for e in evidence[:3])
            response = f"Available evidence:\n{ev_text}"
        else:
            response = "Limited evidence is currently available."
    elif "confidence" in msg_lower:
        conf = context.get("confidence", 0)
        if isinstance(conf, dict):
            conf = conf.get("confidence", 0)
        response = f"Current confidence level: {conf:.0f}%."
    else:
        response = f"{kpi_name} has changed {abs(change):.1f}%. Ask me why, what actions to take, or for evidence details."

    return {
        "response": response,
        "evidence_used": [e["source"] for e in evidence[:5]],
        "confidence": context.get("confidence", 0) if isinstance(context.get("confidence", 0), float) else 0,
    }
