"""CMS connector — WordPress REST API with extensible base class."""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from base64 import b64encode
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class CMSConnector(ABC):
    """Abstract base — swap out for any headless CMS."""

    @abstractmethod
    def get_pages(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def update_seo_fields(
        self,
        page_id: str | int,
        meta_title: str,
        meta_description: str,
        schema_markup: dict[str, Any] | None = None,
    ) -> bool:
        ...

    @abstractmethod
    def get_page_details(self, page_id: str | int) -> dict[str, Any]:
        ...


class WordPressCMSConnector(CMSConnector):
    """
    WordPress REST API connector.

    Supports both Yoast SEO and Rank Math meta field naming.
    Uses Application Passwords for authentication (WP 5.6+).
    """

    YOAST_TITLE_KEY = "_yoast_wpseo_title"
    YOAST_DESC_KEY = "_yoast_wpseo_metadesc"
    RANKMATH_TITLE_KEY = "rank_math_title"
    RANKMATH_DESC_KEY = "rank_math_description"
    SCHEMA_KEY = "_custom_schema_markup"

    def __init__(
        self,
        base_url: str,
        username: str,
        app_password: str,
        seo_plugin: str = "yoast",
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.seo_plugin = seo_plugin.lower()
        credentials = b64encode(f"{username}:{app_password}".encode()).decode()
        self._headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        }
        self._client = httpx.Client(timeout=timeout, follow_redirects=True)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_pages(self) -> list[dict[str, Any]]:
        """Return all published pages and posts."""
        pages = self._paginate(f"{self.base_url}/wp-json/wp/v2/pages", {"status": "publish"})
        posts = self._paginate(f"{self.base_url}/wp-json/wp/v2/posts", {"status": "publish"})
        return pages + posts

    def get_page_details(self, page_id: str | int) -> dict[str, Any]:
        for endpoint in ("pages", "posts"):
            try:
                resp = self._client.get(
                    f"{self.base_url}/wp-json/wp/v2/{endpoint}/{page_id}",
                    headers=self._headers,
                    params={"context": "edit"},
                )
                if resp.status_code == 200:
                    return resp.json()
            except httpx.HTTPError:
                pass
        return {}

    def update_seo_fields(
        self,
        page_id: str | int,
        meta_title: str,
        meta_description: str,
        schema_markup: dict[str, Any] | None = None,
    ) -> bool:
        meta = self._build_meta(meta_title, meta_description, schema_markup)
        payload = {"meta": meta, "yoast_head_json": None}

        # Try pages first, then posts
        for endpoint in ("pages", "posts"):
            url = f"{self.base_url}/wp-json/wp/v2/{endpoint}/{page_id}"
            try:
                resp = self._client.post(url, headers=self._headers, json=payload)
                if resp.status_code in (200, 201):
                    logger.info("Updated SEO for %s/%s", endpoint, page_id)
                    return True
            except httpx.HTTPError as exc:
                logger.warning("HTTP error updating %s/%s: %s", endpoint, page_id, exc)

        return False

    def update_global_schema(self, schema: dict[str, Any]) -> bool:
        """Store site-wide schema as a WP option via a custom REST endpoint or theme option."""
        try:
            resp = self._client.post(
                f"{self.base_url}/wp-json/seo-agent/v1/global-schema",
                headers=self._headers,
                json={"schema": schema},
            )
            return resp.status_code in (200, 201)
        except httpx.HTTPError:
            # Fallback: store in a custom option via the Settings API if the
            # site has a custom endpoint registered.
            logger.warning("Custom schema endpoint not available; skipping global schema push.")
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_meta(
        self,
        meta_title: str,
        meta_description: str,
        schema_markup: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if self.seo_plugin == "rankmath":
            meta = {
                self.RANKMATH_TITLE_KEY: meta_title,
                self.RANKMATH_DESC_KEY: meta_description,
            }
        else:  # default to yoast
            meta = {
                self.YOAST_TITLE_KEY: meta_title,
                self.YOAST_DESC_KEY: meta_description,
            }

        if schema_markup:
            meta[self.SCHEMA_KEY] = json.dumps(schema_markup, indent=2)

        return meta

    def _paginate(self, url: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        results = []
        page = 1
        while True:
            try:
                resp = self._client.get(
                    url,
                    headers=self._headers,
                    params={**params, "per_page": 100, "page": page, "context": "edit"},
                )
                if resp.status_code == 400:
                    break
                resp.raise_for_status()
                batch = resp.json()
                if not batch:
                    break
                results.extend(batch)
                if len(batch) < 100:
                    break
                page += 1
            except httpx.HTTPError as exc:
                logger.error("Pagination error on %s page %d: %s", url, page, exc)
                break
        return results


class DryRunCMSConnector(CMSConnector):
    """
    Simulates CMS updates without making real API calls.
    Use for testing / previewing the update plan.
    """

    def __init__(self) -> None:
        self._log: list[dict[str, Any]] = []

    def get_pages(self) -> list[dict[str, Any]]:
        return [
            {"id": 1, "link": "https://example.com/", "title": {"rendered": "Home"}, "type": "page"},
            {"id": 2, "link": "https://example.com/services/", "title": {"rendered": "Services"}, "type": "page"},
            {"id": 3, "link": "https://example.com/about/", "title": {"rendered": "About"}, "type": "page"},
        ]

    def get_page_details(self, page_id: str | int) -> dict[str, Any]:
        return {"id": page_id, "meta": {}}

    def update_seo_fields(
        self,
        page_id: str | int,
        meta_title: str,
        meta_description: str,
        schema_markup: dict[str, Any] | None = None,
    ) -> bool:
        entry = {
            "page_id": page_id,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "has_schema": schema_markup is not None,
        }
        self._log.append(entry)
        logger.info("[DRY RUN] Would update page %s: %s", page_id, meta_title)
        return True

    @property
    def update_log(self) -> list[dict[str, Any]]:
        return self._log
