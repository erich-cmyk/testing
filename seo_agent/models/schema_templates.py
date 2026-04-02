"""Schema.org JSON-LD template builders."""
from __future__ import annotations

from typing import Any


def organization_schema(
    name: str,
    url: str,
    logo_url: str | None = None,
    description: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    social_profiles: list[str] | None = None,
) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": name,
        "url": url,
    }
    if logo_url:
        schema["logo"] = {"@type": "ImageObject", "url": logo_url}
    if description:
        schema["description"] = description
    if phone:
        schema["telephone"] = phone
    if email:
        schema["email"] = email
    if social_profiles:
        schema["sameAs"] = social_profiles
    return schema


def local_business_schema(
    name: str,
    url: str,
    business_type: str,
    address: dict[str, str],
    phone: str | None = None,
    price_range: str | None = None,
    opening_hours: list[str] | None = None,
    geo: dict[str, float] | None = None,
    rating: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    address: {"streetAddress": ..., "addressLocality": ..., "addressRegion": ...,
               "postalCode": ..., "addressCountry": ...}
    geo: {"latitude": float, "longitude": float}
    rating: {"ratingValue": float, "reviewCount": int}
    """
    schema: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": business_type,
        "name": name,
        "url": url,
        "address": {
            "@type": "PostalAddress",
            **address,
        },
    }
    if phone:
        schema["telephone"] = phone
    if price_range:
        schema["priceRange"] = price_range
    if opening_hours:
        schema["openingHours"] = opening_hours
    if geo:
        schema["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
        }
    if rating:
        schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": rating["ratingValue"],
            "reviewCount": rating["reviewCount"],
        }
    return schema


def webpage_schema(
    name: str,
    url: str,
    description: str,
    breadcrumb: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": name,
        "url": url,
        "description": description,
    }
    if breadcrumb:
        schema["breadcrumb"] = {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i + 1,
                    "name": item["name"],
                    "item": item["url"],
                }
                for i, item in enumerate(breadcrumb)
            ],
        }
    return schema


def faq_schema(faq_items: list[dict[str, str]]) -> dict[str, Any]:
    """faq_items: list of {"question": ..., "answer": ...}"""
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item["answer"],
                },
            }
            for item in faq_items
        ],
    }


def service_schema(
    name: str,
    description: str,
    provider_name: str,
    provider_url: str,
    service_area: str | None = None,
    price_range: str | None = None,
) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": name,
        "description": description,
        "provider": {
            "@type": "Organization",
            "name": provider_name,
            "url": provider_url,
        },
    }
    if service_area:
        schema["areaServed"] = service_area
    if price_range:
        schema["offers"] = {"@type": "Offer", "priceSpecification": price_range}
    return schema
