"""
Worker service
- Consumes from Kafka topic "activity.raw"
- Aggregates events by (user_id, app) into micro-batches
- Applies exponential decay scoring and bulk upserts into Postgres
- Exposes /metrics via a tiny HTTP server (optional for Prometheus)
"""
import asyncio
import json
import logging
import signal
import time
from collections import defaultdict
from typing import Dict, Tuple

import uvicorn
from fastapi import FastAPI
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app
from aiokafka import AIOKafkaConsumer

from settings import Settings
from db import init_db, bulk_upsert_profiles
from profiles import apply_decay_updates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

app = FastAPI(title="SoulLink Worker")
app.mount("/metrics", make_asgi_app())

# Metrics
PROCESSED_EVENTS = Counter("worker_processed_events_total", "Total events processed")
BATCH_LAT_MS = Histogram("worker_batch_latency_ms", "Batch processing latency (ms)")
CONSUMER_LAG = Gauge("worker_consumer_lag", "Consumer lag (approximate)")

settings = Settings()

@app.get("/healthz")
async def healthz():
    return {"ok": True}

async def consumer_loop():
    await init_db(settings.POSTGRES_DSN)
    consumer = AIOKafkaConsumer(
        "activity.raw",
        bootstrap_servers=settings.KAFKA_BROKERS.split(","),
        group_id=settings.CONSUMER_GROUP,
        enable_auto_commit=True,
        auto_offset_reset="earliest"
    )
    await consumer.start()
    logger.info("Kafka consumer started")
    try:
        while True:
            t0 = time.time()
            messages = await consumer.getmany(timeout_ms=200, max_records=1000)
            buffer = defaultdict(int)  # (user, app) -> total_focus_secs
            cnt = 0
            for tp, msgs in messages.items():
                for m in msgs:
                    event = json.loads(m.value)
                    # We don't rely on window or idle for the profile score
                    if not event.get("idle", False):
                        app_name = event.get("app", "unknown")
                        user_id = (m.key or b"unknown").decode()
                        buffer[(user_id, app_name)] += int(event.get("focus_secs", 0))
                        cnt += 1
            if cnt == 0:
                await asyncio.sleep(0.05)
                continue

            # Apply decay & upsert
            updates = apply_decay_updates(buffer, settings.DECAY_LAMBDA, settings.FOCUS_WEIGHT)
            await bulk_upsert_profiles(updates, settings.POSTGRES_DSN)

            PROCESSED_EVENTS.inc(cnt)
            BATCH_LAT_MS.observe((time.time() - t0) * 1000.0)
            # approximate lag metric not implemented (requires external admin client)
            await asyncio.sleep(0.01)
    finally:
        await consumer.stop()

def main():
    loop = asyncio.get_event_loop()
    loop.create_task(consumer_loop())
    # also serve /metrics and /healthz
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
