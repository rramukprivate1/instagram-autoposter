-- ============================================================
-- Instagram Auto-Poster: Supabase Database Schema
-- Run this in Supabase SQL Editor (Dashboard > SQL Editor)
-- ============================================================

-- Enable pgvector extension for semantic duplicate checking
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- TOPICS: Categories of posts (e.g. Self Motivation, Discipline)
-- ============================================================
CREATE TABLE IF NOT EXISTS topics (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name        TEXT NOT NULL UNIQUE,
  description TEXT,
  emoji       TEXT DEFAULT '💡',
  is_active   BOOLEAN DEFAULT TRUE,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TONES: Emotional tone/context for post generation
-- ============================================================
CREATE TABLE IF NOT EXISTS tones (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name        TEXT NOT NULL UNIQUE,
  description TEXT,
  example     TEXT,
  is_active   BOOLEAN DEFAULT TRUE,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- POSTS: The generated post queue
-- ============================================================
CREATE TABLE IF NOT EXISTS posts (
  id              UUID PRIMARY KEY,
  quote           TEXT NOT NULL,
  caption         TEXT,
  hashtags        TEXT[] DEFAULT '{}',
  topic_id        UUID REFERENCES topics(id) ON DELETE SET NULL,
  tone_id         UUID REFERENCES tones(id) ON DELETE SET NULL,
  image_url       TEXT,
  status          TEXT DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','published','publish_failed')),
  approval_token  UUID DEFAULT gen_random_uuid(),
  ig_post_id      TEXT,
  embedding       vector(384),  -- all-MiniLM-L6-v2 outputs 384 dimensions
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  published_at    TIMESTAMPTZ
);

-- Index for fast vector similarity search
CREATE INDEX IF NOT EXISTS posts_embedding_idx
  ON posts USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Index for status-based queries (used by publisher workflow)
CREATE INDEX IF NOT EXISTS posts_status_idx ON posts (status);

-- ============================================================
-- SETTINGS: Global app configuration (key-value store)
-- ============================================================
CREATE TABLE IF NOT EXISTS settings (
  key         TEXT PRIMARY KEY,
  value       TEXT,
  description TEXT,
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- LOGS: Automation run logs
-- ============================================================
CREATE TABLE IF NOT EXISTS logs (
  id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  run_type   TEXT,   -- 'generate', 'publish', 'cleanup'
  status     TEXT,   -- 'success', 'error'
  message    TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- RPC FUNCTION: Find semantically similar posts (for deduplication)
-- Called by duplicate_check.py
-- ============================================================
CREATE OR REPLACE FUNCTION find_similar_posts(
  query_embedding   vector(384),
  lookback_days     INT DEFAULT 30,
  match_threshold   FLOAT DEFAULT 0.85,
  match_count       INT DEFAULT 5
)
RETURNS TABLE (
  id         UUID,
  quote      TEXT,
  distance   FLOAT
)
LANGUAGE SQL STABLE
AS $$
  SELECT
    p.id,
    p.quote,
    (p.embedding <=> query_embedding) AS distance
  FROM posts p
  WHERE
    p.embedding IS NOT NULL
    AND p.created_at >= NOW() - (lookback_days || ' days')::INTERVAL
    AND (p.embedding <=> query_embedding) < (1 - match_threshold)
  ORDER BY p.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- Enable RLS on all tables for security
-- ============================================================
ALTER TABLE topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE tones ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;

-- Policy: Allow authenticated users (admin panel) to do everything
CREATE POLICY "Allow authenticated access" ON topics
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Allow authenticated access" ON tones
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Allow authenticated access" ON posts
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Allow authenticated access" ON settings
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Allow authenticated access" ON logs
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- Policy: Allow service role (GitHub Actions) to bypass RLS
-- (service role key bypasses RLS by default in Supabase — no extra policy needed)
