"""
Anthropic usage integration.
Fetches token usage from the Anthropic API and estimates cost.

Pricing reference (per 1M tokens):
https://www.anthropic.com/pricing
"""
import httpx
from datetime import datetime, timedelta
from typing import Optional

# USD per 1K tokens (input, output)
ANTHROPIC_PRICING = {
    "claude-opus-4-6":             (0.015,  0.075),
    "claude-sonnet-4-6":           (0.003,  0.015),
    "claude-haiku-4-5":            (0.00025, 0.00125),
    "claude-3-5-sonnet":           (0.003,  0.015),
    "claude-3-5-haiku":            (0.001,  0.005),
    "claude-3-opus":               (0.015,  0.075),
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    key = next((k for k in ANTHROPIC_PRICING if model.startswith(k)), None)
    if not key:
        return 0.0
    in_rate, out_rate = ANTHROPIC_PRICING[key]
    return (input_tokens / 1000 * in_rate) + (output_tokens / 1000 * out_rate)


async def fetch_usage(api_key: str, start_date: Optional[datetime] = None) -> list[dict]:
    """
    Fetch usage from Anthropic's usage API.
    Returns a list of event dicts.
    """
    start = (start_date or datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    url = "https://api.anthropic.com/v1/usage"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    params = {"start_date": start}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

    events = []
    for item in data.get("data", []):
        model = item.get("model", "unknown")
        input_tokens = item.get("input_tokens", 0)
        output_tokens = item.get("output_tokens", 0)
        cost = estimate_cost(model, input_tokens, output_tokens)
        events.append({
            "source": "anthropic",
            "tool_name": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
        })
    return events
