"""Pydantic models for all SEO agent data structures."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class KeywordIntent(str, Enum):
    informational = "informational"
    navigational = "navigational"
    commercial = "commercial"
    transactional = "transactional"


class Keyword(BaseModel):
    term: str
    relevance_score: float = Field(..., ge=0.0, le=10.0, description="0-10 relevance score")
    search_intent: KeywordIntent
    estimated_difficulty: str = Field(..., description="Low / Medium / High")
    rationale: str = Field(..., description="Why this keyword matters for the client")


class KeywordList(BaseModel):
    primary_keywords: list[Keyword] = Field(..., description="Top 5-10 exact-match or head terms")
    secondary_keywords: list[Keyword] = Field(..., description="Long-tail and supporting terms")
    negative_keywords: list[str] = Field(default_factory=list, description="Terms to avoid / filter out")
    research_summary: str


class Competitor(BaseModel):
    name: str
    domain: str
    strengths: list[str]
    weaknesses: list[str]
    top_keywords: list[str]
    content_gaps: list[str] = Field(description="Topics they miss that our client can own")


class CompetitorReport(BaseModel):
    competitors: list[Competitor]
    market_positioning_advice: str
    quick_win_opportunities: list[str]


class PageSEO(BaseModel):
    page_id: str | int = Field(description="CMS page/post ID")
    page_url: str
    page_type: str = Field(description="homepage / service / blog / product / location")
    current_title: str | None = None
    current_description: str | None = None
    proposed_meta_title: str = Field(..., max_length=60, description="Optimized meta title ≤60 chars")
    proposed_meta_description: str = Field(..., max_length=160, description="Optimized meta description ≤160 chars")
    target_keywords: list[str]
    schema_markup: dict[str, Any] | None = Field(default=None, description="Schema.org JSON-LD object")
    change_rationale: str


class WebsiteUpdatePlan(BaseModel):
    pages: list[PageSEO]
    global_schema: dict[str, Any] | None = Field(
        default=None, description="Site-level Organization or LocalBusiness schema"
    )
    implementation_notes: str


class ClientProfile(BaseModel):
    business_name: str
    industry: str
    location: str | None = None
    target_audience: str
    primary_services: list[str]
    unique_selling_points: list[str]
    website_url: str
    goals: str
