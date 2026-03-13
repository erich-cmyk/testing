from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class UsageEvent(SQLModel, table=True):
    """Raw AI usage event logged by an integration or manually."""
    id: Optional[int] = Field(default=None, primary_key=True)
    source: str                        # openai | anthropic | copilot | custom
    tool_name: str                     # e.g. "gpt-4o", "claude-3-5-sonnet", "copilot"
    user_id: Optional[str] = None     # optional user/team identifier
    department: Optional[str] = None  # optional department tag
    task_type: Optional[str] = None   # e.g. "code", "writing", "analysis"

    # Cost side
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0             # actual API cost in USD

    # Value side (estimated by caller or integration)
    time_saved_minutes: float = 0.0   # human time saved
    hourly_rate_usd: float = 50.0     # fully-loaded cost of the human hour saved
    quality_score: Optional[float] = None  # 0–10 if collected

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class ApiKey(SQLModel, table=True):
    """Stored API keys for polling integrations."""
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str          # openai | anthropic | copilot
    key_value: str
    org_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
