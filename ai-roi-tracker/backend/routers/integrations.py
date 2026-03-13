"""Integration pull endpoints — fetch usage from external providers and persist."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from database import get_session
from models import UsageEvent, ApiKey
from integrations.openai_integration import fetch_usage as openai_fetch
from integrations.anthropic_integration import fetch_usage as anthropic_fetch
from integrations.copilot_integration import fetch_usage as copilot_fetch
from integrations.custom_integration import CustomEventPayload, payload_to_event
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/integrations", tags=["integrations"])


class SyncRequest(BaseModel):
    api_key: str
    org: Optional[str] = None   # required for Copilot
    days: int = 1


@router.post("/openai/sync")
async def sync_openai(req: SyncRequest, session: Session = Depends(get_session)):
    try:
        events = await openai_fetch(req.api_key)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    saved = []
    for e in events:
        obj = UsageEvent(**e)
        session.add(obj)
        saved.append(obj)
    session.commit()
    return {"synced": len(saved)}


@router.post("/anthropic/sync")
async def sync_anthropic(req: SyncRequest, session: Session = Depends(get_session)):
    try:
        events = await anthropic_fetch(req.api_key)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    saved = []
    for e in events:
        obj = UsageEvent(**e)
        session.add(obj)
        saved.append(obj)
    session.commit()
    return {"synced": len(saved)}


@router.post("/copilot/sync")
async def sync_copilot(req: SyncRequest, session: Session = Depends(get_session)):
    if not req.org:
        raise HTTPException(status_code=400, detail="org is required for Copilot sync")
    try:
        events = await copilot_fetch(req.api_key, req.org, req.days)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    saved = []
    for e in events:
        obj = UsageEvent(**e)
        session.add(obj)
        saved.append(obj)
    session.commit()
    return {"synced": len(saved)}


@router.post("/custom/webhook")
def custom_webhook(payload: CustomEventPayload, session: Session = Depends(get_session)):
    """Webhook endpoint for any custom/internal AI system to push usage data."""
    event_data = payload_to_event(payload)
    obj = UsageEvent(**event_data)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj
