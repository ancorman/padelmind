-- PadelMind — Switch RLS from phone claim to email claim (email OTP auth)
-- Run in Supabase SQL Editor for project ddvntjalhtdutmcknshr

-- padel_players: add email unique constraint, update policies
ALTER TABLE padel_players ADD COLUMN IF NOT EXISTS email text;
CREATE UNIQUE INDEX IF NOT EXISTS idx_padel_players_email_unique ON padel_players(email);

-- Drop old phone-based policies
DROP POLICY IF EXISTS "Players read own profile"         ON padel_players;
DROP POLICY IF EXISTS "Players read own match_players rows" ON padel_match_players;
DROP POLICY IF EXISTS "Players read matches they played in" ON padel_matches;
DROP POLICY IF EXISTS "Players read outputs for their matches" ON padel_match_outputs;

-- New email-based policies
CREATE POLICY "Players read own profile"
  ON padel_players FOR SELECT
  USING (email = (auth.jwt() ->> 'email'));

CREATE POLICY "Players can self-register"
  ON padel_players FOR INSERT
  TO authenticated
  WITH CHECK (email = (auth.jwt() ->> 'email'));

CREATE POLICY "Players can update own profile"
  ON padel_players FOR UPDATE
  TO authenticated
  USING (email = (auth.jwt() ->> 'email'))
  WITH CHECK (email = (auth.jwt() ->> 'email'));

CREATE POLICY "Players read own match_players rows"
  ON padel_match_players FOR SELECT
  USING (
    player_id = (
      SELECT id FROM padel_players
      WHERE email = (auth.jwt() ->> 'email')
    )
  );

CREATE POLICY "Players read matches they played in"
  ON padel_matches FOR SELECT
  USING (
    id IN (
      SELECT match_id FROM padel_match_players
      WHERE player_id = (
        SELECT id FROM padel_players
        WHERE email = (auth.jwt() ->> 'email')
      )
    )
  );

CREATE POLICY "Players read outputs for their matches"
  ON padel_match_outputs FOR SELECT
  USING (
    match_id IN (
      SELECT match_id FROM padel_match_players
      WHERE player_id = (
        SELECT id FROM padel_players
        WHERE email = (auth.jwt() ->> 'email')
      )
    )
  );
