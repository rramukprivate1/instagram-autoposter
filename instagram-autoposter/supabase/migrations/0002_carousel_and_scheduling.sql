-- ============================================================
-- Migration 0002: Carousel/sequence posts + admin-controlled
-- posting time windows.
-- Run this in Supabase SQL Editor AFTER supabase/schema.sql.
-- ============================================================

-- ------------------------------------------------------------
-- Carousels: a post can now be 'single' (existing behavior,
-- uses posts.image_url) or 'carousel' (uses post_slides below).
-- ------------------------------------------------------------
ALTER TABLE posts
  ADD COLUMN IF NOT EXISTS post_format TEXT DEFAULT 'single'
    CHECK (post_format IN ('single', 'carousel'));

CREATE TABLE IF NOT EXISTS post_slides (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  post_id     UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  slide_index INT NOT NULL,
  slide_text  TEXT NOT NULL,
  image_url   TEXT,
  UNIQUE (post_id, slide_index)
);

ALTER TABLE post_slides ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow authenticated access" ON post_slides
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- Let admins turn carousels off for specific topics if they want
-- (e.g. a very short/punchy topic that never suits a multi-slide series)
ALTER TABLE topics
  ADD COLUMN IF NOT EXISTS allow_carousel BOOLEAN DEFAULT true;

-- ------------------------------------------------------------
-- Posting time windows: lets the owner control WHEN posts go
-- out from the admin panel, without editing any cron/YAML.
-- The generate_and_queue workflow now runs every 15 min and
-- checks these settings each time (see main.py / get_current_slot).
-- ------------------------------------------------------------
INSERT INTO settings (key, value, description) VALUES
  ('posting_windows', '["08:00","12:30","16:00","19:30","21:30"]',
   'JSON array of HH:MM times (24h) in `timezone` below - one post-eligible slot each'),
  ('timezone', 'Asia/Kolkata',
   'IANA timezone name used to interpret posting_windows'),
  ('slot_tolerance_minutes', '10',
   'How close to a configured time counts as "this slot" (matches the 15-min check interval with margin)'),
  ('carousel_probability', '0.25',
   'Chance (0-1) that an eligible generation run creates a carousel instead of a single post'),
  ('carousel_min_slides', '3', 'Minimum slides when a carousel is generated'),
  ('carousel_max_slides', '6', 'Maximum slides when a carousel is generated'),
  ('cta_text', '', 'Optional line appended to every caption, e.g. "Link in bio for more"')
ON CONFLICT (key) DO NOTHING;

-- Tracks which slots have already fired today, so the 15-min checker
-- doesn't double-post if a slot gets matched on two consecutive runs.
CREATE TABLE IF NOT EXISTS slot_runs (
  slot_date  DATE NOT NULL,
  slot_time  TEXT NOT NULL,
  ran_at     TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (slot_date, slot_time)
);

ALTER TABLE slot_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow authenticated access" ON slot_runs
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
