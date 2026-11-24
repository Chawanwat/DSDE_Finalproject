"""Thin Kafka helpers (confluent-kafka) shared by producers and consumers.

The broker address comes from KAFKA_BOOTSTRAP_SERVERS:
  - inside docker compose: kafka:29092 (set automatically)
  - on your machine:       localhost:9092 (default)

Smoke test (sends one message and reads it back):
  python -m bkk_cctv.stream.kafka_io
"""
import json
import os
import time
import uuid

from confluent_kafka import Consumer, Producer

from bkk_cctv.log import get_logger

log = get_logger(__name__)


def bootstrap_servers() -> str:
    return os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


def get_producer(**overrides) -> Producer:
    return Producer({"bootstrap.servers": bootstrap_servers(), **overrides})


def get_consumer(group_id: str, topics: list[str], **overrides) -> Consumer:
    consumer = Consumer(
        {
            "bootstrap.servers": bootstrap_servers(),
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            **overrides,
        }
    )
    consumer.subscribe(topics)
    return consumer


def send_json(producer: Producer, topic: str, value: dict, key: str | None = None) -> None:
    producer.produce(topic, key=key, value=json.dumps(value, default=str).encode())


def smoke_test(topic: str = "healthcheck") -> None:
    token = str(uuid.uuid4())
    producer = get_producer()
    send_json(producer, topic, {"token": token})
    producer.flush(10)

    consumer = get_consumer(group_id=f"smoke-{token}", topics=[topic])
    try:
        # Time-based (not message-count) loop: the topic keeps old smoke-test messages
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            msg = consumer.poll(1.0)
            if msg is None or msg.error():
                continue
            if json.loads(msg.value()).get("token") == token:
                log.info("Kafka OK at %s (topic=%s)", bootstrap_servers(), topic)
                return
        raise RuntimeError(f"No message received from Kafka at {bootstrap_servers()}")
    finally:
        consumer.close()


if __name__ == "__main__":
    smoke_test()
