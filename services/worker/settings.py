from pydantic import BaseModel
import os

class Settings(BaseModel):
    KAFKA_BROKERS: str = os.getenv("KAFKA_BROKERS", "redpanda:9092")
    POSTGRES_DSN: str = os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@postgres:5432/soulink")
    DECAY_LAMBDA: float = float(os.getenv("DECAY_LAMBDA", "0.0002"))
    FOCUS_WEIGHT: float = float(os.getenv("FOCUS_WEIGHT", "1.0"))
    CONSUMER_GROUP: str = os.getenv("CONSUMER_GROUP", "soulink-worker")
