-- ============================================================
-- Migration 0004: Branded logo header (replaces the small corner
-- watermark with a logo + handle + tagline block, like a real
-- account's quote-card branding).
-- Run this in Supabase SQL Editor AFTER migration 0003.
-- ============================================================

INSERT INTO settings (key, value, description) VALUES
  ('logo_url', '',
   'Public URL of an uploaded logo/profile photo, set via Schedule Settings. Empty = no logo header, falls back to the small corner watermark text.'),
  ('watermark_tagline', '',
   'Optional second line under the handle in the logo header, e.g. a location or short tagline. Only shown when logo_url is set.')
ON CONFLICT (key) DO NOTHING;
