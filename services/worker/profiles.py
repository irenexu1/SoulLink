"""
profiles.py
Implements the decay update rule for time-weighted profiles.

score := score * exp(-λ * ΔT) + w_focus * focus_secs

This module computes the *new score contribution* to be applied per (user, app).
We treat ΔT as the elapsed time from last_update to now; in this simplified worker
we let Postgres compute ΔT using NOW() - last_update at upsert time.
"""
from typing import Dict, Tuple

def apply_decay_updates(buffer: Dict[Tuple[str, str], int], decay_lambda: float, focus_weight: float):
    """
    Convert a micro-batch of accumulated focus seconds into upsert rows:
    returns list of dicts with keys: user_id, app, delta_focus, decay_lambda, focus_weight
    The actual decay math is executed in SQL for atomicity.
    """
    updates = []
    for (user_id, app), focus_secs in buffer.items():
        updates.append({
            "user_id": user_id,
            "app": app,
            "delta_focus": float(focus_secs),
            "decay_lambda": float(decay_lambda),
            "focus_weight": float(focus_weight),
        })
    return updates
