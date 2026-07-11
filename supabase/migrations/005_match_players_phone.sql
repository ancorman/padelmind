-- PadelMind — Record schema drift: player_phone on padel_match_players
-- This column was added directly in the Supabase SQL Editor (project ddvntjalhtdutmcknshr)
-- during the PWA Staff match-flow build on 2026-07-11. This file documents it so
-- migrations match the live schema. Safe to re-run (IF NOT EXISTS).
--
-- NOTE: The PWA Staff page also inserts into padel_matches and padel_match_players
-- as an authenticated user, so INSERT RLS policies for those tables exist in the
-- live DB but are not yet captured in a migration file. Export them with:
--   select * from pg_policies where tablename in ('padel_matches','padel_match_players');

ALTER TABLE padel_match_players
  ADD COLUMN IF NOT EXISTS player_phone text;

CREATE INDEX IF NOT EXISTS idx_padel_match_players_phone
  ON padel_match_players(player_phone);
