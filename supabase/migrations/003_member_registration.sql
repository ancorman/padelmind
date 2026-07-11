-- PadelMind — Member self-registration support
-- Run in Supabase SQL Editor for project ddvntjalhtdutmcknshr

-- Add email + registration status to padel_players
ALTER TABLE padel_players
  ADD COLUMN IF NOT EXISTS email      text,
  ADD COLUMN IF NOT EXISTS status     text NOT NULL DEFAULT 'pending',
  -- pending | approved | rejected
  ADD COLUMN IF NOT EXISTS registered_at timestamptz DEFAULT now();

CREATE INDEX IF NOT EXISTS idx_padel_players_email  ON padel_players(email);
CREATE INDEX IF NOT EXISTS idx_padel_players_status ON padel_players(status);

-- Allow authenticated users to insert their own registration
CREATE POLICY IF NOT EXISTS "Players can self-register"
  ON padel_players FOR INSERT
  TO authenticated
  WITH CHECK (phone = (auth.jwt() ->> 'phone'));

-- Allow players to update their own name/email (before approval)
CREATE POLICY IF NOT EXISTS "Players can update own profile"
  ON padel_players FOR UPDATE
  TO authenticated
  USING (phone = (auth.jwt() ->> 'phone'))
  WITH CHECK (phone = (auth.jwt() ->> 'phone'));
