-- ============================================================
-- AVENIR — Supabase migration
-- Run this in the Supabase SQL Editor to add missing columns.
-- Existing tables: profiles (id, full_name, email, skills, created_at)
--                  roadmap (id, profile_id, created_at)
-- ============================================================

-- ---- Profiles: add career-navigator columns ----
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS education_level text NOT NULL DEFAULT '';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS subjects text NOT NULL DEFAULT '';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS marks text NOT NULL DEFAULT '';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS interests text NOT NULL DEFAULT '';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS career_interests text NOT NULL DEFAULT '';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS location text NOT NULL DEFAULT '';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS financial_preference text NOT NULL DEFAULT '';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS preferred_education_path text NOT NULL DEFAULT '';

-- ---- Roadmap: add data columns ----
ALTER TABLE roadmap ADD COLUMN IF NOT EXISTS mode text NOT NULL DEFAULT 'mock';
ALTER TABLE roadmap ADD COLUMN IF NOT EXISTS recommendations jsonb NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE roadmap ADD COLUMN IF NOT EXISTS skill_gaps jsonb NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE roadmap ADD COLUMN IF NOT EXISTS roadmap_data jsonb NOT NULL DEFAULT '{}'::jsonb;

-- ---- Indexes ----
CREATE INDEX IF NOT EXISTS idx_profiles_full_name ON profiles(full_name);
CREATE INDEX IF NOT EXISTS idx_roadmap_profile ON roadmap(profile_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_created ON roadmap(created_at DESC);

-- ---- Row-level security ----
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE roadmap ENABLE ROW LEVEL SECURITY;

-- Allow anon full access (demo app)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'anon_all_profiles' AND tablename = 'profiles') THEN
    CREATE POLICY anon_all_profiles ON profiles FOR ALL USING (true) WITH CHECK (true);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'anon_all_roadmap' AND tablename = 'roadmap') THEN
    CREATE POLICY anon_all_roadmap ON roadmap FOR ALL USING (true) WITH CHECK (true);
  END IF;
END $$;
