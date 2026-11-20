from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.modules.notifications.model import Notification
from app.modules.notifications.schema import NotificationResponse


def create_notification(
    db: Session,
    *,
    recipient_id: int,
    actor_id: int | None,
    notification_type: str,
    entity_type: str | None,
    entity_id: int | None,
    message: str,
) -> Notification | None:
    if actor_id is not None and actor_id == recipient_id:
        return None
    notification = Notification(
        recipient_id=recipient_id,
        actor_id=actor_id,
        type=notification_type,
        entity_type=entity_type,
        entity_id=entity_id,
        message=message[:255],
    )
    db.add(notification)
    return notification


def list_notifications(
    db: Session,
    *,
    recipient_id: int,
    limit: int,
    offset: int,
) -> tuple[list[Notification], int]:
    query = (
        select(Notification)
        .where(Notification.recipient_id == recipient_id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(limit)
        .offset(offset)
    )
    count_query = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.recipient_id == recipient_id)
    )
    return list(db.scalars(query).all()), db.scalar(count_query) or 0


def get_unread_count(db: Session, *, recipient_id: int) -> int:
    query = select(func.count()).select_from(Notification).where(
        Notification.recipient_id == recipient_id,
        Notification.is_read.is_(False),
    )
    return db.scalar(query) or 0


def mark_read(db: Session, *, recipient_id: int, notification_id: int) -> Notification | None:
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_id == recipient_id,
        )
    )
    if notification is None:
        return None
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, *, recipient_id: int) -> int:
    result = db.execute(
        update(Notification)
        .where(
            Notification.recipient_id == recipient_id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True)
    )
    db.commit()
    return result.rowcount or 0


def latest_notification_id(recipient_id: int) -> int:
    with SessionLocal() as db:
        return db.scalar(
            select(func.max(Notification.id)).where(Notification.recipient_id == recipient_id)
        ) or 0


def fetch_notifications_after(recipient_id: int, after_id: int) -> list[dict]:
    with SessionLocal() as db:
        rows = db.scalars(
            select(Notification)
            .where(
                Notification.recipient_id == recipient_id,
                Notification.id > after_id,
            )
            .order_by(Notification.id)
            .limit(100)
        ).all()
        return [
            NotificationResponse.model_validate(row).model_dump(mode="json", by_alias=True)
            for row in rows
        ]
