"""
Ingest service (FastAPI)
- POST /v1/events: validate and enqueue events into Redis (burst buffer)
- Background drain loop: pop batches from Redis and publish to Kafka
- /metrics: Prometheus exposition endpoint
- Backpressure: if queue length exceeds QUEUE_LIMIT, respond 429
"""
import asyncio
import json
import logging
import time
from typing import List

from fastapi import FastAPI, HTTPException, Query
from prometheus_client import Counter, Histogram, make_asgi_app
from redis import asyncio as aioredis
from aiokafka import AIOKafkaProducer

from settings import Settings
from models import Event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest")

app = FastAPI(title="SoulLink Ingest")
app.mount("/metrics", make_asgi_app())

# Prometheus metrics
INGEST_BATCH_SIZE = Histogram("ingest_batch_size", "Size of batches drained to Kafka")
INGEST_LAT_MS = Histogram("ingest_latency_ms", "Latency to drain a batch (ms)")
BACKPRESSURE_429 = Counter("ingest_backpressure_429_total", "Number of 429 responses due to queue limit")

settings = Settings()

redis = None  # type: aioredis.Redis
producer = None  # type: AIOKafkaProducer
qkey_prefix = "ingest:pending:"
topic_raw = "activity.raw"

@app.on_event("startup")
async def startup():
    global redis, producer
    redis = aioredis.from_url(settings.REDIS_URL)
    producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BROKERS.split(","))
    await producer.start()
    asyncio.create_task(drain_loop())
    logger.info("Startup complete: Redis + Kafka producer ready.")

@app.on_event("shutdown")
async def shutdown():
    if producer:
        await producer.stop()
    if redis:
        await redis.close()

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.post("/v1/events")
async def post_events(
    events: List[Event],
    user_id: str = Query(..., description="User identifier associated with this device/batch"),
):
    """
    Validate the event list and enqueue to Redis.
    If the queue grows beyond QUEUE_LIMIT, return 429 (backpressure) to throttle senders.
    """
    qkey = f"{qkey_prefix}{user_id}"
    # push serialized events to redis list
    payloads = [e.model_dump_json() for e in events]
    length = await redis.rpush(qkey, *payloads)
    if length > settings.QUEUE_LIMIT:
        BACKPRESSURE_429.inc()
        # Optionally trim to prevent unbounded growth
        await redis.ltrim(qkey, -settings.QUEUE_LIMIT, -1)
        raise HTTPException(status_code=429, detail="backpressure")
    return {"queued": len(events), "queue_len": length}

async def drain_loop():
    """
    Drain loop:
    - iterate all user queues (keys pattern)
    - pop up to BATCH_SIZE items from each and publish to Kafka
    - simple cooperative scheduling with small sleep
    """
    await asyncio.sleep(1.0)  # small grace period
    while True:
        try:
            # iterate per-user queues
            keys = await redis.keys(f"{qkey_prefix}*")
            if not keys:
                await asyncio.sleep(0.05)
                continue
            for qkey in keys:
                # Pop up to BATCH_SIZE from the left (oldest first)
                t0 = time.time()
                batch = []
                for _ in range(settings.BATCH_SIZE):
                    data = await redis.lpop(qkey)
                    if data is None:
                        break
                    batch.append(json.loads(data))
                if not batch:
                    continue

                # Publish to Kafka (keyed by user_id for ordering)
                # Extract user_id from qkey: ingest:pending:{user}
                user_id = qkey.decode().split(":")[-1] if isinstance(qkey, bytes) else str(qkey).split(":")[-1]
                for item in batch:
                    await producer.send_and_wait(topic_raw, json.dumps(item).encode("utf-8"), key=user_id.encode())

                INGEST_BATCH_SIZE.observe(len(batch))
                INGEST_LAT_MS.observe((time.time() - t0) * 1000.0)
            await asyncio.sleep(0.01)
        except Exception as e:
            logger.exception("drain_loop error: %s", e)
            await asyncio.sleep(0.5)
