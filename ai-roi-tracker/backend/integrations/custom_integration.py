"""
Custom / internal model integration.
Accepts webhook payloads from any self-hosted or internal AI system.

Expected payload shape:
{
  "tool_name": "my-internal-model",
  "user_id": "optional",
  "department": "optional",
  "task_type": "optional",
  "input_tokens": 100,
  "output_tokens": 200,
  "cost_usd": 0.001,          # if known; otherwise set to 0
  "time_saved_minutes": 10,
  "hourly_rate_usd": 50,
  "quality_score": 8.5,
  "notes": "optional"
}
"""
from pydantic import BaseModel
from typing import Optional


class CustomEventPayload(BaseModel):
    tool_name: str
    user_id: Optional[str] = None
    department: Optional[str] = None
    task_type: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    time_saved_minutes: float = 0.0
    hourly_rate_usd: float = 50.0
    quality_score: Optional[float] = None
    notes: Optional[str] = None


def payload_to_event(payload: CustomEventPayload) -> dict:
    return {
        "source": "custom",
        **payload.model_dump(),
    }
