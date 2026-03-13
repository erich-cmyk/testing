"""Aggregated ROI metrics for the dashboard."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func
from database import get_session
from models import UsageEvent

router = APIRouter(prefix="/metrics", tags=["metrics"])


def _base_query(session, days: int, source: Optional[str], department: Optional[str]):
    cutoff = datetime.utcnow() - timedelta(days=days)
    stmt = select(UsageEvent).where(UsageEvent.timestamp >= cutoff)
    if source:
        stmt = stmt.where(UsageEvent.source == source)
    if department:
        stmt = stmt.where(UsageEvent.department == department)
    return session.exec(stmt).all()


@router.get("/summary")
def summary(
    days: int = Query(30, ge=1, le=365),
    source: Optional[str] = None,
    department: Optional[str] = None,
    session: Session = Depends(get_session),
):
    events = _base_query(session, days, source, department)

    total_cost = sum(e.cost_usd for e in events)
    total_time_saved_hrs = sum(e.time_saved_minutes for e in events) / 60
    total_value = sum((e.time_saved_minutes / 60) * e.hourly_rate_usd for e in events)
    net_roi = total_value - total_cost
    roi_pct = ((net_roi / total_cost) * 100) if total_cost > 0 else 0
    total_tokens = sum(e.input_tokens + e.output_tokens for e in events)

    by_source: dict[str, dict] = {}
    for e in events:
        s = by_source.setdefault(e.source, {"cost": 0.0, "value": 0.0, "events": 0})
        s["cost"] += e.cost_usd
        s["value"] += (e.time_saved_minutes / 60) * e.hourly_rate_usd
        s["events"] += 1

    return {
        "period_days": days,
        "total_events": len(events),
        "total_cost_usd": round(total_cost, 4),
        "total_value_usd": round(total_value, 2),
        "net_roi_usd": round(net_roi, 2),
        "roi_percent": round(roi_pct, 1),
        "total_time_saved_hours": round(total_time_saved_hrs, 1),
        "total_tokens": total_tokens,
        "by_source": {
            k: {
                "cost_usd": round(v["cost"], 4),
                "value_usd": round(v["value"], 2),
                "roi_usd": round(v["value"] - v["cost"], 2),
                "events": v["events"],
            }
            for k, v in by_source.items()
        },
    }


@router.get("/daily")
def daily_breakdown(
    days: int = Query(30, ge=1, le=90),
    source: Optional[str] = None,
    department: Optional[str] = None,
    session: Session = Depends(get_session),
):
    events = _base_query(session, days, source, department)

    daily: dict[str, dict] = {}
    for e in events:
        day = e.timestamp.strftime("%Y-%m-%d")
        d = daily.setdefault(day, {"cost": 0.0, "value": 0.0, "events": 0, "tokens": 0})
        d["cost"] += e.cost_usd
        d["value"] += (e.time_saved_minutes / 60) * e.hourly_rate_usd
        d["events"] += 1
        d["tokens"] += e.input_tokens + e.output_tokens

    return [
        {
            "date": day,
            "cost_usd": round(v["cost"], 4),
            "value_usd": round(v["value"], 2),
            "roi_usd": round(v["value"] - v["cost"], 2),
            "events": v["events"],
            "tokens": v["tokens"],
        }
        for day, v in sorted(daily.items())
    ]


@router.get("/by-department")
def by_department(
    days: int = Query(30),
    session: Session = Depends(get_session),
):
    events = _base_query(session, days, None, None)
    dept: dict[str, dict] = {}
    for e in events:
        key = e.department or "Unassigned"
        d = dept.setdefault(key, {"cost": 0.0, "value": 0.0, "events": 0})
        d["cost"] += e.cost_usd
        d["value"] += (e.time_saved_minutes / 60) * e.hourly_rate_usd
        d["events"] += 1
    return [
        {
            "department": k,
            "cost_usd": round(v["cost"], 4),
            "value_usd": round(v["value"], 2),
            "roi_usd": round(v["value"] - v["cost"], 2),
            "events": v["events"],
        }
        for k, v in sorted(dept.items(), key=lambda x: -x[1]["value"])
    ]


@router.get("/by-task-type")
def by_task_type(
    days: int = Query(30),
    session: Session = Depends(get_session),
):
    events = _base_query(session, days, None, None)
    tasks: dict[str, dict] = {}
    for e in events:
        key = e.task_type or "Other"
        t = tasks.setdefault(key, {"cost": 0.0, "value": 0.0, "events": 0})
        t["cost"] += e.cost_usd
        t["value"] += (e.time_saved_minutes / 60) * e.hourly_rate_usd
        t["events"] += 1
    return [
        {
            "task_type": k,
            "cost_usd": round(v["cost"], 4),
            "value_usd": round(v["value"], 2),
            "roi_usd": round(v["value"] - v["cost"], 2),
            "events": v["events"],
        }
        for k, v in sorted(tasks.items(), key=lambda x: -x[1]["value"])
    ]
