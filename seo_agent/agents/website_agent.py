"""
Website Agent — Phase 4
Generates optimized meta titles, meta descriptions, and Schema.org markup
for each page, then applies the changes via the CMS connector.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import anthropic
from pydantic import ValidationError

from ..models.seo_data import ClientProfile, KeywordList, PageSEO, WebsiteUpdatePlan
from ..tools.cms_connector import CMSConnector

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a technical SEO specialist with deep expertise in on-page optimization
and structured data (Schema.org).

Meta title rules:
- 50-60 characters (absolute max 60)
- Include primary keyword near the front
- Include brand name at the end after a pipe: | Brand
- Be specific and compelling — this is the ad for the page

Meta description rules:
- 140-160 characters (max 160)
- Include primary keyword naturally
- Include a clear value proposition or call to action
- Be human-readable and click-worthy

Schema.org rules:
- Use the most specific type applicable (@type)
- Include all required and recommended properties
- For local businesses use LocalBusiness (or a subtype like Restaurant, MedicalBusiness, etc.)
- For service pages use Service with a provider reference
- For FAQs use FAQPage
- Always set @context to https://schema.org

Every decision must be grounded in the keyword strategy and competitive research."""

UPDATE_PLAN_SCHEMA = {
    "name": "website_update_plan",
    "description": "Complete SEO update plan for all pages",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "pages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "page_id": {"type": "string"},
                        "page_url": {"type": "string"},
                        "page_type": {"type": "string"},
                        "current_title": {"type": "string"},
                        "current_description": {"type": "string"},
                        "proposed_meta_title": {"type": "string"},
                        "proposed_meta_description": {"type": "string"},
                        "target_keywords": {"type": "array", "items": {"type": "string"}},
                        "schema_markup": {
                            "type": "object",
                            "additionalProperties": True,
                        },
                        "change_rationale": {"type": "string"},
                    },
                    "required": [
                        "page_id", "page_url", "page_type",
                        "proposed_meta_title", "proposed_meta_description",
                        "target_keywords", "change_rationale",
                    ],
                    "additionalProperties": False,
                },
            },
            "global_schema": {
                "type": "object",
                "additionalProperties": True,
            },
            "implementation_notes": {"type": "string"},
        },
        "required": ["pages", "implementation_notes"],
        "additionalProperties": False,
    },
}


def run(
    client: anthropic.Anthropic,
    profile: ClientProfile,
    keyword_list: KeywordList,
    cms: CMSConnector,
    dry_run: bool = False,
) -> dict[str, Any]:
    logger.info("Starting website agent for: %s (dry_run=%s)", profile.business_name, dry_run)

    # Fetch current pages from CMS
    pages = cms.get_pages()
    if not pages:
        logger.warning("No pages returned from CMS; using empty list.")

    pages_summary = _format_pages_summary(pages)
    keywords_summary = _format_keywords_summary(keyword_list)

    prompt = f"""Generate a complete SEO update plan for every page on this website.

**Client:** {profile.business_name} ({profile.website_url})
**Industry:** {profile.industry}
**Location:** {profile.location or "National / Online"}
**Services:** {", ".join(profile.primary_services)}

---
**Current Website Pages:**
{pages_summary}

---
**Keyword Strategy:**
{keywords_summary}

---
**Instructions:**
For EACH page:
1. Write an optimized meta title (≤60 chars, keyword-first, | {profile.business_name} at end)
2. Write an optimized meta description (≤160 chars, compelling, keyword-rich)
3. Select 2-4 target keywords from our strategy
4. Generate appropriate Schema.org JSON-LD markup for the page type
5. Explain the rationale for your choices

Additionally, create a global Organization or LocalBusiness schema for the site.

Assign page types as: homepage / service / about / contact / blog / location / product

Call `website_update_plan` with your complete plan."""

    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
    update_plan_data: dict[str, Any] | None = None

    max_iterations = 6
    for _ in range(max_iterations):
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8000,
            thinking={"type": "adaptive"},
            tools=[UPDATE_PLAN_SCHEMA],
            system=SYSTEM_PROMPT,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "website_update_plan":
                update_plan_data = block.input
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": "Update plan received.",
                })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        if update_plan_data is not None:
            break

    if update_plan_data is None:
        raise RuntimeError("Website agent failed to produce an update plan.")

    # Apply updates via CMS
    update_results = _apply_updates(cms, update_plan_data, dry_run)

    return {
        "update_plan": update_plan_data,
        "update_results": update_results,
        "pages_processed": len(update_plan_data.get("pages", [])),
        "dry_run": dry_run,
    }


def _apply_updates(
    cms: CMSConnector,
    plan: dict[str, Any],
    dry_run: bool,
) -> list[dict[str, Any]]:
    results = []
    for page in plan.get("pages", []):
        page_id = page.get("page_id", "")
        schema = page.get("schema_markup")

        if dry_run:
            logger.info("[DRY RUN] Would update page %s: %s", page_id, page.get("proposed_meta_title"))
            results.append({"page_id": page_id, "status": "dry_run", "title": page.get("proposed_meta_title")})
            continue

        success = cms.update_seo_fields(
            page_id=page_id,
            meta_title=page["proposed_meta_title"],
            meta_description=page["proposed_meta_description"],
            schema_markup=schema,
        )
        results.append({
            "page_id": page_id,
            "status": "success" if success else "failed",
            "title": page.get("proposed_meta_title"),
        })
        if not success:
            logger.error("Failed to update page %s", page_id)

    # Apply global schema
    global_schema = plan.get("global_schema")
    if global_schema and not dry_run:
        if hasattr(cms, "update_global_schema"):
            cms.update_global_schema(global_schema)

    return results


def _format_pages_summary(pages: list[dict[str, Any]]) -> str:
    if not pages:
        return "No pages found."
    lines = []
    for p in pages[:50]:  # cap at 50 to avoid huge prompts
        page_id = p.get("id", "?")
        url = p.get("link", p.get("slug", ""))
        title = p.get("title", {}).get("rendered", p.get("title", ""))
        meta = p.get("meta", {})
        current_title = (
            meta.get("_yoast_wpseo_title")
            or meta.get("rank_math_title")
            or title
        )
        lines.append(f"- ID:{page_id} | {url} | Current title: {current_title}")
    return "\n".join(lines)


def _format_keywords_summary(kw_list: KeywordList) -> str:
    lines = [f"**Summary:** {kw_list.research_summary}", "", "**Primary Keywords:**"]
    for kw in kw_list.primary_keywords:
        lines.append(f"- {kw.term} (score:{kw.relevance_score}, intent:{kw.search_intent}, difficulty:{kw.estimated_difficulty})")
    lines.append("\n**Secondary Keywords:**")
    for kw in kw_list.secondary_keywords[:20]:
        lines.append(f"- {kw.term} (score:{kw.relevance_score}, intent:{kw.search_intent})")
    if kw_list.negative_keywords:
        lines.append(f"\n**Negative Keywords:** {', '.join(kw_list.negative_keywords)}")
    return "\n".join(lines)
