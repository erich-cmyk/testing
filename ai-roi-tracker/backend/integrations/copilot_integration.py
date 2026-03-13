"""
GitHub Copilot usage integration.
Uses the GitHub Copilot Usage API (org-level) to fetch seat and suggestion metrics.

Docs: https://docs.github.com/en/rest/copilot/copilot-usage
"""
import httpx
from datetime import datetime, timedelta
from typing import Optional

# Copilot Business: $19/seat/month = ~$0.63/seat/day
COPILOT_COST_PER_SEAT_DAY = 19.0 / 30


async def fetch_usage(token: str, org: str, days: int = 7) -> list[dict]:
    """
    Fetch Copilot usage metrics for an org.
    Returns list of event dicts (one per day).
    """
    url = f"https://api.github.com/orgs/{org}/copilot/usage"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

    events = []
    for day in data:
        date_str = day.get("day", "")
        active_users = day.get("total_active_users", 0)
        suggestions = day.get("total_suggestions_count", 0)
        acceptances = day.get("total_acceptances_count", 0)
        lines_accepted = day.get("total_lines_accepted", 0)

        # Cost: active users × daily seat cost
        cost = active_users * COPILOT_COST_PER_SEAT_DAY

        # Time saved: ~2 min per accepted suggestion (conservative estimate)
        time_saved_minutes = acceptances * 2.0

        events.append({
            "source": "copilot",
            "tool_name": "github-copilot",
            "input_tokens": 0,
            "output_tokens": lines_accepted * 10,  # rough token proxy
            "cost_usd": cost,
            "time_saved_minutes": time_saved_minutes,
            "notes": f"{suggestions} suggestions, {acceptances} accepted, {active_users} active users",
            "timestamp": date_str,
        })
    return events
