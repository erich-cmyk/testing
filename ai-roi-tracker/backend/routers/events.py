"""CRUD for usage events — manual logging + webhook ingestion."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from database import get_session
from models import UsageEvent

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=UsageEvent)
def log_event(event: UsageEvent, session: Session = Depends(get_session)):
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


@router.get("/", response_model=list[UsageEvent])
def list_events(
    source: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    session: Session = Depends(get_session),
):
    cutoff = datetime.utcnow() - timedelta(days=days)
    stmt = select(UsageEvent).where(UsageEvent.timestamp >= cutoff)
    if source:
        stmt = stmt.where(UsageEvent.source == source)
    if department:
        stmt = stmt.where(UsageEvent.department == department)
    return session.exec(stmt.order_by(UsageEvent.timestamp.desc())).all()


@router.delete("/{event_id}")
def delete_event(event_id: int, session: Session = Depends(get_session)):
    event = session.get(UsageEvent, event_id)
    if event:
        session.delete(event)
        session.commit()
    return {"ok": True}
