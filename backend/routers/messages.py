"""
routers/messages.py
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from schemas import (
    MessageAnalyzeRequest, MessageAnalyzeResponse,
    MessageLinkRequest, MessageLinkResponse,
    MessageMapContext,
)
from database import get_db
from data_loader import get_data
from services.message_service import (
    analyze_message,
    link_message_to_investigation,
    get_message_map_context,
)

router = APIRouter(prefix="/api/messages", tags=["Messages"])

VALID_TARGET_TYPES = {"INCIDENT", "ACTOR", "ROUTE", "LOCATION"}


# ── /api/messages/channels ────────────────────────────────────────────────────

@router.get(
    "/channels",
    summary="List distinct message channels / chat groups",
)
def list_channels():
    """
    Returns a list of channel objects derived from the messages dataset.
    The frontend SignalWatch page uses this to populate the channel sidebar.
    """
    d = get_data()
    if d.messages.empty:
        return []

    # Group by chat_group
    groups: dict[str, dict] = {}
    for _, row in d.messages.iterrows():
        group = str(row.get("chat_group", "unknown"))
        if group not in groups:
            groups[group] = {"count": 0, "last_ts": ""}
        groups[group]["count"] += 1
        ts = str(row.get("timestamp", ""))
        if ts > groups[group]["last_ts"]:
            groups[group]["last_ts"] = ts

    channels = []
    for i, (group, meta) in enumerate(sorted(groups.items())):
        channels.append({
            "id":           group,
            "name":         group.replace("_", " ").title(),
            "memberCount":  meta["count"],
            "lastActivity": meta["last_ts"][:10] if meta["last_ts"] else "Unknown",
        })

    return channels


# ── /api/messages ─────────────────────────────────────────────────────────────

@router.get(
    "",
    summary="List messages, optionally filtered by channel",
)
def list_messages(channel: str = None):
    """
    Returns messages from the dataset. If ?channel= is provided, filters
    to that chat_group. The frontend SignalWatch page calls this.
    """
    from typing import Optional
    from fastapi import Query
    d = get_data()
    if d.messages.empty:
        return []

    rows = d.messages.to_dict("records")
    if channel:
        rows = [r for r in rows if str(r.get("chat_group", "")) == channel]

    result = []
    for r in rows[:100]:
        text = str(r.get("message_text", ""))
        slang = str(r.get("contains_slang", "")).lower() == "true"
        # Derive flagged terms
        from services.message_service import KNOWN_SLANG
        flagged = [
            {"term": t, "confidence": 75}
            for t in KNOWN_SLANG if t in text.lower()
        ]
        result.append({
            "id":                   str(r.get("message_id", "")),
            "sender":               str(r.get("sender_actor", "")),
            "receiver":             str(r.get("receiver_actor", "")),
            "text":                 text,
            "timestamp":            str(r.get("timestamp", "")),
            "channelId":            str(r.get("chat_group", "")),
            "containsSlang":        slang,
            "flaggedTerms":         flagged,
            "locationMention":      None,
            "addedToInvestigation": False,
        })

    return result


@router.post(
    "/analyze",
    response_model=MessageAnalyzeResponse,
    summary="Analyse a message for linguistic intelligence signals",
)
def analyze(body: MessageAnalyzeRequest):
    d = get_data()
    result = analyze_message(body.sender, body.receiver, body.message, d)
    return result


@router.post(
    "/link",
    response_model=MessageLinkResponse,
    summary="Link a message to an investigation target",
)
def link_message(body: MessageLinkRequest, db: Session = Depends(get_db)):
    if body.target_type.upper() not in VALID_TARGET_TYPES:
        raise HTTPException(status_code=400, detail={
            "error": True,
            "message": f"Invalid target type '{body.target_type}'",
            "code": "INVALID_TARGET_TYPE",
        })
    d = get_data()
    return link_message_to_investigation(body.message_id, body.target_type, body.target_id, d, db)


@router.get(
    "/{message_id}/map-context",
    response_model=MessageMapContext,
    summary="Geographic context for a message — enables 'View on Map'",
)
def message_map_context(message_id: str):
    d = get_data()
    result = get_message_map_context(message_id, d)
    if not result:
        raise HTTPException(status_code=404, detail={
            "error": True, "message": "Message not found", "code": "MESSAGE_NOT_FOUND"
        })
    return result
