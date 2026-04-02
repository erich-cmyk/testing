"""
Competitor Agent — Phase 2
Analyzes top competitors, their keyword strategy, content strengths/gaps,
and positioning to find opportunities for the client.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import anthropic
from pydantic import ValidationError

from ..models.seo_data import ClientProfile, CompetitorReport

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a competitive intelligence specialist focused on SEO and digital marketing.
Your job is to analyze competitors systematically to find strategic opportunities.

When analyzing competitors:
- Look at their top-ranking pages and the keywords they target
- Identify content gaps — topics they haven't covered well
- Assess their domain authority signals and backlink profile
- Evaluate their on-page SEO quality (title tags, meta descriptions, schema)
- Find weaknesses where our client can outperform them

Always return structured, actionable intelligence that directly informs strategy."""

COMPETITOR_SCHEMA = {
    "name": "competitor_report",
    "description": "Structured competitive analysis report",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "competitors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "domain": {"type": "string"},
                        "strengths": {"type": "array", "items": {"type": "string"}},
                        "weaknesses": {"type": "array", "items": {"type": "string"}},
                        "top_keywords": {"type": "array", "items": {"type": "string"}},
                        "content_gaps": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["name", "domain", "strengths", "weaknesses", "top_keywords", "content_gaps"],
                    "additionalProperties": False,
                },
            },
            "market_positioning_advice": {"type": "string"},
            "quick_win_opportunities": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["competitors", "market_positioning_advice", "quick_win_opportunities"],
        "additionalProperties": False,
    },
}


def run(
    client: anthropic.Anthropic,
    profile: ClientProfile,
    research_data: dict[str, Any],
    max_competitors: int = 5,
) -> CompetitorReport:
    logger.info("Starting competitor analysis for: %s", profile.business_name)

    prompt = f"""Perform a detailed competitive analysis for:

**Client:** {profile.business_name} ({profile.website_url})
**Industry:** {profile.industry}
**Location:** {profile.location or "National / Online"}
**Services:** {", ".join(profile.primary_services)}

**Research Context:**
{research_data.get("research_report", "")[:3000]}

Steps:
1. Search for the top {max_competitors} competitors in this space
2. For each competitor, analyze their website and SEO strategy
3. Identify their strongest keywords and ranking pages
4. Find content topics they haven't addressed well (gaps our client can fill)
5. Assess their meta titles and descriptions quality
6. Note any schema markup they use

Then call the `competitor_report` tool with your structured findings.

Focus on actionable insights — where can our client realistically compete and win?"""

    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
    report_data: dict[str, Any] | None = None

    # Agentic loop — runs until Claude delivers the structured report
    max_iterations = 10
    for iteration in range(max_iterations):
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=6000,
            thinking={"type": "adaptive"},
            tools=[
                {"type": "web_search_20260209", "name": "web_search"},
                COMPETITOR_SCHEMA,
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
                if block.name == "competitor_report":
                    report_data = block.input
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Report received. Thank you.",
                    })
                else:
                    # web_search — handled server-side, no client execution needed
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Search completed.",
                    })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        if report_data is not None:
            break

    if report_data is None:
        # Fallback: extract any text and return a minimal report
        last_text = next(
            (b.text for b in response.content if b.type == "text"), ""
        )
        logger.warning("competitor_report tool not called; using fallback text.")
        return CompetitorReport(
            competitors=[],
            market_positioning_advice=last_text[:500] if last_text else "Analysis incomplete.",
            quick_win_opportunities=[],
        )

    try:
        return CompetitorReport(**report_data)
    except ValidationError as exc:
        logger.error("Validation error building CompetitorReport: %s", exc)
        return CompetitorReport(
            competitors=[],
            market_positioning_advice="Validation error — see logs.",
            quick_win_opportunities=[],
        )
