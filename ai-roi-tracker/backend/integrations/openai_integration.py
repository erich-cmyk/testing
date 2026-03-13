"""
OpenAI usage integration.
Fetches usage data from the OpenAI API and converts it to UsageEvents.

Pricing reference (per 1M tokens, update as needed):
https://openai.com/pricing
"""
import httpx
from datetime import datetime, timedelta
from typing import Optional

# USD per 1K tokens (input, output) — update to current pricing
OPENAI_PRICING = {
    "gpt-4o":            (0.0025, 0.010),
    "gpt-4o-mini":       (0.00015, 0.0006),
    "gpt-4-turbo":       (0.010,  0.030),
    "gpt-4":             (0.030,  0.060),
    "gpt-3.5-turbo":     (0.0005, 0.0015),
    "o1":                (0.015,  0.060),
    "o1-mini":           (0.003,  0.012),
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    key = next((k for k in OPENAI_PRICING if model.startswith(k)), None)
    if not key:
        return 0.0
    in_rate, out_rate = OPENAI_PRICING[key]
    return (input_tokens / 1000 * in_rate) + (output_tokens / 1000 * out_rate)


async def fetch_usage(api_key: str, date: Optional[datetime] = None) -> list[dict]:
    """
    Fetch per-model usage from the OpenAI usage endpoint for a given date.
    Returns a list of dicts ready to be turned into UsageEvents.
    """
    target = (date or datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://api.openai.com/v1/usage?date={target}"
    headers = {"Authorization": f"Bearer {api_key}"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

    events = []
    for item in data.get("data", []):
        model = item.get("snapshot_id", "unknown")
        n_context = item.get("n_context_tokens_total", 0)
        n_generated = item.get("n_generated_tokens_total", 0)
        cost = estimate_cost(model, n_context, n_generated)
        events.append({
            "source": "openai",
            "tool_name": model,
            "input_tokens": n_context,
            "output_tokens": n_generated,
            "cost_usd": cost,
            "timestamp": target,
        })
    return events
