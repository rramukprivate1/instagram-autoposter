-- ============================================================
-- Migration 0005: Storage policy for the logo upload feature.
-- Run this in Supabase SQL Editor AFTER migration 0004.
--
-- Every image upload until now happened server-side using the
-- service_role key (in main.py), which bypasses Row Level Security
-- entirely - so this was never needed before. The logo upload in the
-- admin panel is the first thing that writes to Storage directly from
-- the browser as a logged-in user, and Storage enforces its own
-- policies on storage.objects, completely separate from table RLS.
-- Without this, uploads fail with "new row violates row-level
-- security policy" even though you're correctly logged in.
-- ============================================================

CREATE POLICY "Authenticated users can upload to post-images"
ON storage.objects FOR INSERT TO authenticated
WITH CHECK (bucket_id = 'post-images');

CREATE POLICY "Authenticated users can update post-images"
ON storage.objects FOR UPDATE TO authenticated
USING (bucket_id = 'post-images');

CREATE POLICY "Authenticated users can delete from post-images"
ON storage.objects FOR DELETE TO authenticated
USING (bucket_id = 'post-images');
