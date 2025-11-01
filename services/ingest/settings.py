from pydantic import BaseModel
import os

class Settings(BaseModel):
    KAFKA_BROKERS: str = os.getenv("KAFKA_BROKERS", "redpanda:9092")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    QUEUE_LIMIT: int = int(os.getenv("QUEUE_LIMIT", "5000"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "500"))
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev_secret")
