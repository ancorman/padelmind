-- PadelMind — P0-A Initial Schema
-- Run this in Supabase SQL Editor for project ddvntjalhtdutmcknshr
-- manoj@quitlosing.in account

-- ─────────────────────────────────────────
-- TABLES
-- ─────────────────────────────────────────

CREATE TABLE padel_clubs (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name         text NOT NULL,
  city         text NOT NULL,
  wa_number    text NOT NULL UNIQUE,   -- E.164: +91XXXXXXXXXX, sends PADEL commands
  active       boolean DEFAULT true,
  created_at   timestamptz DEFAULT now()
);

CREATE TABLE padel_courts (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  club_id           uuid NOT NULL REFERENCES padel_clubs(id) ON DELETE CASCADE,
  name              text NOT NULL,           -- "Court 1", "Court A"
  pi_webhook_url    text,                    -- Pi daemon URL for START/END signals
  pi_secret         text,                    -- shared secret for Pi webhook auth
  camera_keypoints  jsonb,                   -- 12 pixel coords from calibration tool
  active            boolean DEFAULT true,
  created_at        timestamptz DEFAULT now(),
  UNIQUE(club_id, name)
);

CREATE TABLE padel_players (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  phone      text NOT NULL UNIQUE,           -- E.164: +91XXXXXXXXXX
  name       text,
  club_id    uuid REFERENCES padel_clubs(id),
  created_at timestamptz DEFAULT now()
);

CREATE TABLE padel_matches (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  court_id       uuid NOT NULL REFERENCES padel_courts(id),
  started_at     timestamptz,
  ended_at       timestamptz,
  status         text NOT NULL DEFAULT 'recording',
  -- recording | uploaded | queued | processing | done | failed
  video_r2_key   text,                       -- raw match MP4 in R2
  duration_sec   integer,
  created_at     timestamptz DEFAULT now()
);

CREATE TABLE padel_match_players (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id        uuid NOT NULL REFERENCES padel_matches(id) ON DELETE CASCADE,
  player_id       uuid NOT NULL REFERENCES padel_players(id),
  player_slot     integer NOT NULL CHECK (player_slot BETWEEN 1 AND 4),
  heatmap_r2_key  text,                      -- per-player heatmap PNG in R2
  wa_delivered    boolean DEFAULT false,
  delivered_at    timestamptz,
  UNIQUE(match_id, player_id),
  UNIQUE(match_id, player_slot)
);

CREATE TABLE padel_match_outputs (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id          uuid NOT NULL REFERENCES padel_matches(id) ON DELETE CASCADE UNIQUE,
  highlight_r2_key  text,                    -- shared highlight MP4 in R2
  positions_r2_key  text,                    -- positions JSON (Phase 2 input)
  rally_count       integer,
  rally_windows     jsonb,                   -- [{start_sec, end_sec, duration}]
  zones_summary     jsonb,                   -- {player_1: {back_left, ...}, ...}
  created_at        timestamptz DEFAULT now()
);

CREATE TABLE padel_jobs (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id       uuid NOT NULL REFERENCES padel_matches(id) ON DELETE CASCADE UNIQUE,
  runpod_job_id  text,
  status         text NOT NULL DEFAULT 'queued',
  -- queued | dispatched | processing | done | failed
  queued_at      timestamptz DEFAULT now(),
  started_at     timestamptz,
  completed_at   timestamptz,
  error_message  text
);

-- ─────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────

CREATE INDEX idx_padel_matches_court_id   ON padel_matches(court_id);
CREATE INDEX idx_padel_matches_status     ON padel_matches(status);
CREATE INDEX idx_padel_match_players_match ON padel_match_players(match_id);
CREATE INDEX idx_padel_match_players_player ON padel_match_players(player_id);
CREATE INDEX idx_padel_jobs_status        ON padel_jobs(status);
CREATE INDEX idx_padel_players_phone      ON padel_players(phone);
CREATE INDEX idx_padel_clubs_wa_number    ON padel_clubs(wa_number);

-- ─────────────────────────────────────────
-- ROW LEVEL SECURITY
-- ─────────────────────────────────────────

ALTER TABLE padel_clubs          ENABLE ROW LEVEL SECURITY;
ALTER TABLE padel_courts         ENABLE ROW LEVEL SECURITY;
ALTER TABLE padel_players        ENABLE ROW LEVEL SECURITY;
ALTER TABLE padel_matches        ENABLE ROW LEVEL SECURITY;
ALTER TABLE padel_match_players  ENABLE ROW LEVEL SECURITY;
ALTER TABLE padel_match_outputs  ENABLE ROW LEVEL SECURITY;
ALTER TABLE padel_jobs           ENABLE ROW LEVEL SECURITY;

-- Service role bypasses RLS — Workers use service role key
-- Players read their own data via phone claim in JWT

CREATE POLICY "Players read own profile"
  ON padel_players FOR SELECT
  USING (phone = (auth.jwt() ->> 'phone'));

CREATE POLICY "Players read own match_players rows"
  ON padel_match_players FOR SELECT
  USING (
    player_id = (
      SELECT id FROM padel_players
      WHERE phone = (auth.jwt() ->> 'phone')
    )
  );

CREATE POLICY "Players read matches they played in"
  ON padel_matches FOR SELECT
  USING (
    id IN (
      SELECT match_id FROM padel_match_players
      WHERE player_id = (
        SELECT id FROM padel_players
        WHERE phone = (auth.jwt() ->> 'phone')
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
        WHERE phone = (auth.jwt() ->> 'phone')
      )
    )
  );

-- ─────────────────────────────────────────
-- SEED: PILOT CLUB (update before going live)
-- ─────────────────────────────────────────

INSERT INTO padel_clubs (name, city, wa_number) VALUES
  ('Pilot Club', 'Mumbai', '+910000000000')  -- replace with real club WA number
ON CONFLICT DO NOTHING;
