"""
db.py
SQLAlchemy helpers for connecting to Postgres and performing bulk upserts.
We keep the SQL visible and straightforward for clarity and performance.
"""
from typing import List, Dict
from sqlalchemy import create_engine, text

_engine_cache = {}

async def init_db(dsn: str):
    # We use a synchronous engine; the worker loop is async but DB IO here is short and batched.
    if dsn not in _engine_cache:
        _engine_cache[dsn] = create_engine(dsn, future=True, pool_pre_ping=True)

def _engine(dsn: str):
    return _engine_cache[dsn]

UPSERT_SQL = """
INSERT INTO behavior_profiles (user_id, app, score, last_update)
VALUES (:user_id, :app,
        -- if new row, start with just the contribution
        :focus_weight * :delta_focus,
        NOW())
ON CONFLICT (user_id, app) DO UPDATE SET
  -- decay old score by exp(-lambda * ΔT), then add new contribution
  score = (behavior_profiles.score * EXP(-:decay_lambda * EXTRACT(EPOCH FROM (NOW() - behavior_profiles.last_update))))
          + (:focus_weight * :delta_focus),
  last_update = NOW();
"""

async def bulk_upsert_profiles(updates: List[Dict], dsn: str):
    eng = _engine(dsn)
    with eng.begin() as conn:
        conn.execute(text(UPSERT_SQL), updates)
