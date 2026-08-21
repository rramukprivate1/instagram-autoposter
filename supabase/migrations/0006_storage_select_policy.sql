-- ============================================================
-- Migration 0006: SELECT policy for storage.objects.
-- Run this in Supabase SQL Editor AFTER migration 0005.
--
-- Belt-and-suspenders fix alongside removing upsert:true from the
-- logo upload call. If INSERT/UPDATE/DELETE policies existed but the
-- upload still failed, an internal existence-check requiring SELECT
-- access is the most likely explanation - this closes that gap.
-- ============================================================

CREATE POLICY "Authenticated users can view post-images"
ON storage.objects FOR SELECT TO authenticated
USING (bucket_id = 'post-images');
