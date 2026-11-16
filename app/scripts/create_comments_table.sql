CREATE TABLE IF NOT EXISTS comments (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id BIGINT REFERENCES comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_comments_post_id ON comments(post_id);
CREATE INDEX IF NOT EXISTS ix_comments_author_id ON comments(author_id);
CREATE INDEX IF NOT EXISTS ix_comments_parent_created
    ON comments(parent_id, created_at, id)
    WHERE deleted_at IS NULL;

-- Backfill comments created before updated_at was populated, then enforce it.
UPDATE comments
SET updated_at = COALESCE(updated_at, created_at, NOW())
WHERE updated_at IS NULL;

ALTER TABLE comments
    ALTER COLUMN updated_at SET DEFAULT NOW();

ALTER TABLE comments
    ALTER COLUMN updated_at SET NOT NULL;
