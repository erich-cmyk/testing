"""
Seed the database with realistic demo data for development/demo purposes.
Run: python seed.py
"""
import random
from datetime import datetime, timedelta
from sqlmodel import Session
from database import engine, create_db
from models import UsageEvent

SOURCES = ["openai", "anthropic", "copilot", "custom"]
TOOLS = {
    "openai": ["gpt-4o", "gpt-4o-mini", "o1-mini"],
    "anthropic": ["claude-sonnet-4-6", "claude-haiku-4-5", "claude-opus-4-6"],
    "copilot": ["github-copilot"],
    "custom": ["internal-summarizer", "internal-classifier"],
}
DEPARTMENTS = ["Engineering", "Marketing", "Legal", "Finance", "Sales", "HR"]
TASK_TYPES = ["code", "writing", "analysis", "summarization", "classification", "research"]

COST_PER_1K = {
    "gpt-4o": (0.0025, 0.010),
    "gpt-4o-mini": (0.00015, 0.0006),
    "o1-mini": (0.003, 0.012),
    "claude-sonnet-4-6": (0.003, 0.015),
    "claude-haiku-4-5": (0.00025, 0.00125),
    "claude-opus-4-6": (0.015, 0.075),
    "github-copilot": (0, 0),
    "internal-summarizer": (0, 0),
    "internal-classifier": (0, 0),
}


def gen_event(days_ago: int) -> UsageEvent:
    source = random.choice(SOURCES)
    tool = random.choice(TOOLS[source])
    dept = random.choice(DEPARTMENTS)
    task = random.choice(TASK_TYPES)

    inp = random.randint(200, 8000)
    out = random.randint(50, 2000)
    in_rate, out_rate = COST_PER_1K.get(tool, (0.001, 0.004))
    cost = (inp / 1000 * in_rate) + (out / 1000 * out_rate)

    if source == "copilot":
        cost = random.uniform(0.5, 2.5)  # daily seat cost fraction
        time_saved = random.uniform(15, 90)
    else:
        time_saved = random.uniform(2, 45)

    hourly = random.choice([40, 50, 60, 75, 100, 125])
    ts = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))

    return UsageEvent(
        source=source,
        tool_name=tool,
        user_id=f"user_{random.randint(1, 50)}",
        department=dept,
        task_type=task,
        input_tokens=inp,
        output_tokens=out,
        cost_usd=round(cost, 6),
        time_saved_minutes=round(time_saved, 1),
        hourly_rate_usd=hourly,
        quality_score=round(random.uniform(5, 10), 1),
        timestamp=ts,
    )


if __name__ == "__main__":
    create_db()
    with Session(engine) as session:
        events = [gen_event(d) for d in range(90) for _ in range(random.randint(5, 20))]
        for e in events:
            session.add(e)
        session.commit()
    print(f"Seeded {len(events)} events over 90 days.")
