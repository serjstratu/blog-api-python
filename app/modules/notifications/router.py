import asyncio
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.auth.dependencies import get_current_user, get_current_user_from_access_cookie
from app.modules.notifications import service
from app.modules.notifications.schema import (
    NotificationResponse,
    NotificationsPage,
    ReadAllResponse,
    UnreadCountResponse,
)
from app.modules.users.model import User


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationsPage)
def list_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notifications, total_items = service.list_notifications(
        db,
        recipient_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    total_pages = (total_items + limit - 1) // limit
    return NotificationsPage(
        data=notifications,
        pagination={
            "currentPage": offset // limit + 1,
            "perPage": limit,
            "totalItems": total_items,
            "totalPages": total_pages,
            "hasNextPage": offset + len(notifications) < total_items,
            "hasPreviousPage": offset > 0 and total_items > 0,
        },
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return UnreadCountResponse(
        unread_count=service.get_unread_count(db, recipient_id=current_user.id)
    )


@router.patch("/read-all", response_model=ReadAllResponse)
def read_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = service.mark_all_read(db, recipient_id=current_user.id)
    return ReadAllResponse(updated_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = service.mark_read(
        db,
        recipient_id=current_user.id,
        notification_id=notification_id,
    )
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.get("/stream")
async def notification_stream(
    request: Request,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    current_user: User = Depends(get_current_user_from_access_cookie),
):
    try:
        last_id = max(0, int(last_event_id)) if last_event_id is not None else 0
    except ValueError:
        last_id = 0
    if last_id == 0:
        last_id = service.latest_notification_id(current_user.id)

    async def event_generator():
        nonlocal last_id
        heartbeat_counter = 0
        while not await request.is_disconnected():
            events = await asyncio.to_thread(
                service.fetch_notifications_after,
                current_user.id,
                last_id,
            )
            for event_data in events:
                last_id = max(last_id, int(event_data["id"]))
                yield (
                    f"id: {last_id}\n"
                    "event: notification\n"
                    f"data: {json.dumps(event_data, separators=(',', ':'))}\n\n"
                )
            heartbeat_counter += 1
            if heartbeat_counter >= 15:
                yield ": keep-alive\n\n"
                heartbeat_counter = 0
            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
