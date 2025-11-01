-- Minimal schema for SoulLink
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY
);

-- Optional raw log table (useful for audits)
CREATE TABLE IF NOT EXISTS activity_events (
  user_id TEXT NOT NULL,
  ts TIMESTAMPTZ NOT NULL,
  app TEXT NOT NULL,
  window TEXT,
  focus_secs INT NOT NULL,
  idle BOOLEAN NOT NULL,
  PRIMARY KEY (user_id, ts)
);

-- Aggregated, time-weighted behavior profile per (user, app)
CREATE TABLE IF NOT EXISTS behavior_profiles (
  user_id TEXT NOT NULL,
  app TEXT NOT NULL,
  score DOUBLE PRECISION NOT NULL DEFAULT 0,
  last_update TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, app)
);

CREATE INDEX IF NOT EXISTS idx_activity_user_ts ON activity_events (user_id, ts DESC);
