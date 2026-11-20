CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    recipient_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    actor_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id BIGINT,
    message VARCHAR(255) NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_notifications_recipient_created
    ON notifications(recipient_id, created_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS ix_notifications_unread
    ON notifications(recipient_id, is_read)
    WHERE is_read = FALSE;
