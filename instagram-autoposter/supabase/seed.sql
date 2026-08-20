-- ============================================================
-- Instagram Auto-Poster: Seed Data
-- Run this AFTER schema.sql in Supabase SQL Editor
-- ============================================================

-- Default Topics
INSERT INTO topics (name, description, emoji, is_active) VALUES
  ('Self Motivation',    'Quotes that inspire internal drive, self-belief, and personal growth',  '🔥', TRUE),
  ('Life Quotes',        'Timeless wisdom about the journey of life, choices, and meaning',       '🌱', TRUE),
  ('Discipline',         'The power of consistent action, habits, and showing up every day',      '💪', TRUE),
  ('Consistency',        'Why showing up daily beats talent — small steps add up to big results', '📈', TRUE),
  ('Heart Maintenance',  'Emotional wellness, self-love, healing, and mental peace',              '❤️', TRUE),
  ('Thoughts & Mindset', 'Shifting perspective, mindset resets, and the power of your thinking',  '🧠', TRUE),
  ('Body Maintenance',   'Health, fitness, rest, nutrition, and caring for your physical self',   '🏃', TRUE),
  ('Courage & Fears',    'Facing fears, taking risks, and the freedom that comes from bravery',   '🦅', TRUE),
  ('Friendship & Trust', 'The value of genuine connections, loyalty, and meaningful bonds',       '🤝', TRUE),
  ('Purpose & Goals',    'Finding direction, chasing dreams, and staying true to your why',       '🎯', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Default Tones
INSERT INTO tones (name, description, example, is_active) VALUES
  ('Friend',
   'Warm, casual, supportive — like advice from a close friend who genuinely cares',
   'Hey, you okay? You have been through worse than this. You got it.',
   TRUE),
  ('Teacher',
   'Wise, instructive, patient — like a great mentor guiding a student',
   'Remember: growth does not happen in comfort. Push past that edge.',
   TRUE),
  ('Parent',
   'Loving, firm, protective — like a parent who believes in you unconditionally',
   'I see you working hard. I am proud of you. Keep going.',
   TRUE),
  ('Raw & Direct',
   'No fluff, straight truth — hard love that cuts through the noise',
   'Stop waiting. Nobody is coming to save you. Start now.',
   TRUE),
  ('Calm & Poetic',
   'Gentle, reflective, almost meditative — like reading a poem at sunrise',
   'Stillness speaks. Sometimes the quietest move is the most powerful.',
   TRUE),
  ('Advisor',
   'Professional, confident, strategic — like a life coach giving you a framework',
   'Define your non-negotiables. Build your day around them. Protect them.',
   TRUE)
ON CONFLICT (name) DO NOTHING;

-- Default Settings
INSERT INTO settings (key, value, description) VALUES
  ('posts_per_day',       '2',              'Number of posts to generate per day (start low to warm up account)'),
  ('auto_post',           'false',          'If true, approved posts are published without manual email approval'),
  ('custom_context',      '',               'Custom context/instruction injected into every AI generation prompt'),
  ('ig_handle',           '@yourhandle',    'Your Instagram handle shown as watermark on quote cards'),
  ('cleanup_after_days',  '7',              'Delete hosted images from storage after this many days post-publish'),
  ('duplicate_threshold', '0.85',           'Cosine similarity threshold above which a post is considered a duplicate')
ON CONFLICT (key) DO NOTHING;
