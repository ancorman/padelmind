-- PadelMind — P0 Bookings table
-- Run in Supabase SQL Editor for project ddvntjalhtdutmcknshr

CREATE TABLE padel_bookings (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  court_id     uuid NOT NULL REFERENCES padel_courts(id),
  player_id    uuid NOT NULL REFERENCES padel_players(id),
  slot_time    timestamptz NOT NULL,
  duration_min integer NOT NULL DEFAULT 30,
  status       text NOT NULL DEFAULT 'confirmed', -- confirmed | cancelled
  amount       integer NOT NULL DEFAULT 400,
  created_at   timestamptz DEFAULT now(),
  UNIQUE(court_id, slot_time)
);

CREATE INDEX idx_padel_bookings_court_slot ON padel_bookings(court_id, slot_time);
CREATE INDEX idx_padel_bookings_player    ON padel_bookings(player_id);

ALTER TABLE padel_bookings ENABLE ROW LEVEL SECURITY;

-- All authenticated users can see all bookings (needed for availability grid)
CREATE POLICY "Read all bookings for availability"
  ON padel_bookings FOR SELECT
  TO authenticated
  USING (true);

-- Players can only book as themselves
CREATE POLICY "Players insert own bookings"
  ON padel_bookings FOR INSERT
  TO authenticated
  WITH CHECK (
    player_id = (
      SELECT id FROM padel_players
      WHERE phone = (auth.jwt() ->> 'phone')
    )
  );
