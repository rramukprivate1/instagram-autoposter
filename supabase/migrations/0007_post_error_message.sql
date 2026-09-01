-- ============================================================
-- Migration 0007: Store the actual failure reason on the post.
-- Run this in Supabase SQL Editor AFTER migration 0006.
--
-- Paired with the graph_request() fix in publish_post.py, which now
-- surfaces Meta's real error detail instead of a generic HTTP status
-- line. Without a place to put it, that detail only lived in GitHub
-- Actions logs - now it's visible right on the post itself.
-- ============================================================

ALTER TABLE posts ADD COLUMN IF NOT EXISTS error_message TEXT;
