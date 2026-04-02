"""
Keyword Agent — Phase 3
Synthesizes research and competitor data into a curated, prioritized keyword list.
Uses adaptive thinking for deep analysis and structured output for reliability.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import anthropic
from pydantic import ValidationError

from ..models.seo_data import ClientProfile, CompetitorReport, Keyword, KeywordList

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior SEO keyword strategist.
Your job is to synthesize research and competitive data into a precise, actionable keyword list.

Keyword selection principles:
- Balance search volume potential with realistic ranking difficulty
- Prioritize commercial and transactional intent for revenue-driving pages
- Include informational keywords for content marketing / top-of-funnel
- Cluster related terms to inform page architecture
- Think beyond obvious head terms — long-tail keywords often convert better
- Consider local modifiers if the business is location-based
- Flag negative keywords that would attract irrelevant traffic

Every keyword must be justified with a clear rationale tied to the client's goals."""

KEYWORD_SCHEMA = {
    "name": "keyword_list",
    "description": "Final curated keyword strategy",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "primary_keywords": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "term": {"type": "string"},
                        "relevance_score": {"type": "number"},
                        "search_intent": {
                            "type": "string",
                            "enum": ["informational", "navigational", "commercial", "transactional"],
                        },
                        "estimated_difficulty": {
                            "type": "string",
                            "enum": ["Low", "Medium", "High"],
                        },
                        "rationale": {"type": "string"},
                    },
                    "required": ["term", "relevance_score", "search_intent", "estimated_difficulty", "rationale"],
                    "additionalProperties": False,
                },
            },
            "secondary_keywords": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "term": {"type": "string"},
                        "relevance_score": {"type": "number"},
                        "search_intent": {
                            "type": "string",
                            "enum": ["informational", "navigational", "commercial", "transactional"],
                        },
                        "estimated_difficulty": {
                            "type": "string",
                            "enum": ["Low", "Medium", "High"],
                        },
                        "rationale": {"type": "string"},
                    },
                    "required": ["term", "relevance_score", "search_intent", "estimated_difficulty", "rationale"],
                    "additionalProperties": False,
                },
            },
            "negative_keywords": {"type": "array", "items": {"type": "string"}},
            "research_summary": {"type": "string"},
        },
        "required": ["primary_keywords", "secondary_keywords", "negative_keywords", "research_summary"],
        "additionalProperties": False,
    },
}


def run(
    client: anthropic.Anthropic,
    profile: ClientProfile,
    research_data: dict[str, Any],
    competitor_report: CompetitorReport,
    target_count: int = 30,
) -> KeywordList:
    logger.info("Building keyword strategy for: %s", profile.business_name)

    competitor_summary = _format_competitor_summary(competitor_report)

    prompt = f"""Build a comprehensive keyword strategy for:

**Client:** {profile.business_name}
**Industry:** {profile.industry}
**Location:** {profile.location or "National / Online"}
**Services:** {", ".join(profile.primary_services)}
**USPs:** {", ".join(profile.unique_selling_points)}
**Goals:** {profile.goals}

---
**Research Findings:**
{research_data.get("research_report", "")[:3000]}

---
**Competitive Intelligence:**
{competitor_summary}

---
**Task:**
Create a keyword strategy with:
- **5-10 primary keywords** (head terms, high-intent, directly tied to services)
- **{target_count - 10}+ secondary keywords** (long-tail, informational, supporting)
- **Negative keywords** to exclude irrelevant traffic
- A **research summary** explaining the strategic logic

For each keyword provide:
- Relevance score (0-10)
- Search intent (informational/navigational/commercial/transactional)
- Estimated difficulty (Low/Medium/High)
- Clear rationale

Use additional web searches if needed to validate search demand for specific terms.
Then call `keyword_list` with your final answer."""

    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
    keyword_data: dict[str, Any] | None = None

    max_iterations = 8
    for _ in range(max_iterations):
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8000,
            thinking={"type": "adaptive"},
            tools=[
                {"type": "web_search_20260209", "name": "web_search"},
                KEYWORD_SCHEMA,
            ],
            system=SYSTEM_PROMPT,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                if block.name == "keyword_list":
                    keyword_data = block.input
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Keyword list received.",
                    })
                else:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Search completed.",
                    })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        if keyword_data is not None:
            break

    if keyword_data is None:
        logger.error("keyword_list tool was never called.")
        raise RuntimeError("Keyword agent failed to produce a keyword list.")

    try:
        return KeywordList(**keyword_data)
    except ValidationError as exc:
        logger.error("KeywordList validation error: %s", exc)
        raise


def _format_competitor_summary(report: CompetitorReport) -> str:
    if not report.competitors:
        return "No competitor data available."
    lines = []
    for comp in report.competitors:
        lines.append(f"**{comp.name}** ({comp.domain})")
        lines.append(f"  Top keywords: {', '.join(comp.top_keywords[:5])}")
        lines.append(f"  Content gaps: {', '.join(comp.content_gaps[:3])}")
    lines.append(f"\nPositioning advice: {report.market_positioning_advice}")
    lines.append(f"Quick wins: {', '.join(report.quick_win_opportunities[:5])}")
    return "\n".join(lines)
