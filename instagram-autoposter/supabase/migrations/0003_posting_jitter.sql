-- ============================================================
-- Migration 0003: Posting-time jitter.
-- Run this in Supabase SQL Editor AFTER migration 0002.
-- ============================================================

INSERT INTO settings (key, value, description) VALUES
  ('posting_time_jitter_minutes', '20',
   'Randomizes each Posting Time by up to this many minutes, differently each day, so posts don''t fire at the exact same clock-minute every day. Set to 0 to disable and post at exact configured times.')
ON CONFLICT (key) DO NOTHING;
