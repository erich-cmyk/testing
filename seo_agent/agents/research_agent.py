"""
Research Agent — Phase 1
Gathers deep context about the client's business, industry, and market landscape
using Claude's built-in web search tool.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

from ..models.seo_data import ClientProfile

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior SEO research analyst with 15+ years of experience.
Your job is to conduct thorough research on a client's business to inform a comprehensive SEO strategy.

When researching:
- Identify industry-specific terminology and jargon people actually search for
- Understand the customer journey and search intent at each stage
- Find content gaps and underserved topics in the niche
- Note local search factors if the business serves a geographic area
- Look for seasonal trends, emerging topics, and evergreen opportunities

Always cite specific data points, search volumes (when available), and actionable insights.
Be thorough — this research will directly power keyword and schema decisions."""


def run(client: anthropic.Anthropic, profile: ClientProfile) -> dict[str, Any]:
    """
    Research the client's industry, audience, and search landscape.
    Returns a rich research dictionary consumed by downstream agents.
    """
    logger.info("Starting research agent for: %s", profile.business_name)

    research_prompt = f"""Conduct comprehensive SEO research for this client:

**Business:** {profile.business_name}
**Industry:** {profile.industry}
**Location:** {profile.location or "National / Online"}
**Target Audience:** {profile.target_audience}
**Primary Services/Products:** {", ".join(profile.primary_services)}
**Unique Selling Points:** {", ".join(profile.unique_selling_points)}
**Website:** {profile.website_url}
**Goals:** {profile.goals}

Please research the following and synthesize your findings:

1. **Industry Search Landscape**: What are people in this industry searching for? What problems are they trying to solve? What language do they use?

2. **Target Audience Search Behavior**: How does the target audience search? What devices? What intent (informational vs transactional)?

3. **Content Opportunities**: What topics are underserved? What questions aren't being answered well? What long-tail opportunities exist?

4. **Local SEO Factors** (if applicable): Are there geographic modifiers? Local intent signals? Google Business Profile optimization opportunities?

5. **Seasonal & Trend Analysis**: Are there seasonal peaks? Emerging trends? Industry shifts that affect search behavior?

6. **SERP Features**: For this industry, what SERP features appear (featured snippets, PAA boxes, local packs, shopping results)? How can we target them?

Provide a detailed research report with specific, actionable findings."""

    messages: list[dict[str, Any]] = [{"role": "user", "content": research_prompt}]
    research_text = ""

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=8000,
        thinking={"type": "adaptive"},
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        for event in stream:
            if (
                event.type == "content_block_delta"
                and hasattr(event.delta, "type")
                and event.delta.type == "text_delta"
            ):
                print(event.delta.text, end="", flush=True)

        final = stream.get_final_message()
        research_text = " ".join(
            block.text for block in final.content if block.type == "text"
        )

    print()  # newline after streaming

    return {
        "client_profile": profile.model_dump(),
        "research_report": research_text,
        "raw_response": json.loads(final.model_dump_json()),
    }
