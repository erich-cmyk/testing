"""Configuration — loads from environment / .env file."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def get(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


def require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Required environment variable '{key}' is not set.")
    return value


ANTHROPIC_API_KEY: str = require("ANTHROPIC_API_KEY")
CMS_TYPE: str = get("CMS_TYPE", "wordpress") or "wordpress"
CMS_BASE_URL: str | None = get("CMS_BASE_URL")
CMS_USERNAME: str | None = get("CMS_USERNAME")
CMS_APP_PASSWORD: str | None = get("CMS_APP_PASSWORD")
CMS_SEO_PLUGIN: str = get("CMS_SEO_PLUGIN", "yoast") or "yoast"

MAX_COMPETITORS: int = int(get("MAX_COMPETITORS", "5") or "5")
KEYWORD_TARGET_COUNT: int = int(get("KEYWORD_TARGET_COUNT", "30") or "30")
