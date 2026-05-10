import json
from aiokafka import AIOKafkaProducer
from core.config import settings


class KafkaProducerManager:
    def __init__(self, bootstrap_servers: str):
        self._bootstrap_servers = bootstrap_servers
        self._producer: AIOKafkaProducer | None = None
        self._connected = False

    async def start(self):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode(),
        )
        try:
            await self._producer.start()
            self._connected = True
        except Exception as e:
            print(f"Warning: Kafka unavailable at startup ({e}), will retry on demand")
            try:
                await self._producer.stop()
            except Exception:
                pass

    async def stop(self):
        producer = self._producer
        if producer is not None:
            try:
                await producer.stop()
            except Exception:
                pass

    async def _ensure_connected(self):
        if not self._connected and self._producer is not None:
            try:
                await self._producer.start()
                self._connected = True
            except Exception:
                raise

    async def publish(self, topic: str, value: dict, key: str | None = None):
        if not self._connected:
            await self._ensure_connected()
        try:
            if self._producer is None:
                raise RuntimeError("Kafka producer not initialized")
            await self._producer.send_and_wait(
                topic,
                value=value,
                key=key.encode() if key else None,
            )
        except Exception:
            self._connected = False
            raise

    async def publish_broadcast(self, channel_id: str, payload: dict) -> bool:
        try:
            await self.publish(
                settings.KAFKA_BROADCAST_TOPIC,
                value={"channel_id": channel_id, "payload": payload},
                key=channel_id,
            )
            return True
        except Exception:
            return False

    async def enqueue_analysis(self, message_id: str, content: str, channel_id: str):
        if not self._connected:
            try:
                await self._ensure_connected()
            except Exception:
                return
        try:
            await self.publish(
                settings.KAFKA_AI_ANALYSIS_TOPIC,
                value={
                    "message_id": message_id,
                    "content": content,
                    "channel_id": channel_id,
                },
                key=message_id,
            )
        except Exception:
            pass
