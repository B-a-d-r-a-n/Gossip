from __future__ import annotations

import asyncio
import json
from uuid import uuid4
from collections.abc import Callable
from typing import Any, Coroutine
from aiokafka import AIOKafkaConsumer
from core.config import settings

INSTANCE_ID: str = str(uuid4())


class BroadcastConsumer:
    def __init__(self, bootstrap_servers: str):
        self._bootstrap_servers = bootstrap_servers
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task | None = None
        self._on_message: Callable[[str, dict], Coroutine[Any, Any, None]] | None = None

    async def start(self, on_message: Callable[[str, dict], Coroutine[Any, Any, None]]):
        self._on_message = on_message
        for attempt in range(10):
            try:
                self._consumer = AIOKafkaConsumer(
                    settings.KAFKA_BROADCAST_TOPIC,
                    bootstrap_servers=self._bootstrap_servers,
                    group_id=f"chat-broadcast-{INSTANCE_ID}",
                    auto_offset_reset="latest",
                    enable_auto_commit=False,
                    value_deserializer=lambda v: json.loads(v.decode()),
                )
                await self._consumer.start()
                self._task = asyncio.create_task(self._poll_loop())
                return
            except Exception as e:
                wait = min(2 ** attempt, 30)
                print(f"Broadcast consumer initial connection failed (attempt {attempt + 1}/10, {e}), retrying in {wait}s...")
                if self._consumer:
                    try:
                        await self._consumer.stop()
                    except Exception:
                        pass
                    self._consumer = None
                await asyncio.sleep(wait)
        print("Broadcast consumer failed to connect after 10 attempts, starting background retry")
        asyncio.create_task(self._background_connect())

    async def _poll_loop(self):
        backoff = 1
        while True:
            try:
                consumer = self._consumer
                on_message = self._on_message
                assert consumer is not None
                assert on_message is not None
                async for msg in consumer:
                    val = msg.value
                    assert val is not None
                    payload = val["payload"]
                    channel_id = val["channel_id"]
                    asyncio.create_task(on_message(channel_id, payload))
                raise RuntimeError("consumer.listen() exhausted")
            except asyncio.CancelledError:
                return
            except Exception as e:
                print(f"Broadcast consumer error ({e}), reconnecting in {backoff}s\u2026")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
                # Attempt to reconnect: stop any existing consumer and recreate
                for attempt in range(5):
                    try:
                        # Stop old consumer if present
                        old_consumer = self._consumer
                        if old_consumer is not None:
                            try:
                                await old_consumer.stop()
                            except Exception:
                                pass
                        # Recreate a fresh consumer instance with the same config
                        self._consumer = AIOKafkaConsumer(
                            settings.KAFKA_BROADCAST_TOPIC,
                            bootstrap_servers=self._bootstrap_servers,
                            group_id=f"chat-broadcast-{INSTANCE_ID}",
                            auto_offset_reset="latest",
                            enable_auto_commit=False,
                            value_deserializer=lambda v: json.loads(v.decode()),
                        )
                        consumer = self._consumer
                        await consumer.start()
                        backoff = 1
                        break
                    except Exception as sub_err:
                        wait = min(2**attempt, 16)
                        print(f"Reconnect attempt {attempt + 1} failed ({sub_err}), retry in {wait}s")
                        await asyncio.sleep(wait)

    async def _background_connect(self):
        backoff = 1
        while True:
            try:
                self._consumer = AIOKafkaConsumer(
                    settings.KAFKA_BROADCAST_TOPIC,
                    bootstrap_servers=self._bootstrap_servers,
                    group_id=f"chat-broadcast-{INSTANCE_ID}",
                    auto_offset_reset="latest",
                    enable_auto_commit=False,
                    value_deserializer=lambda v: json.loads(v.decode()),
                )
                await self._consumer.start()
                print("Broadcast consumer connected successfully in background")
                self._task = asyncio.create_task(self._poll_loop())
                return
            except Exception as e:
                print(f"Background reconnect failed ({e}), retrying in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._consumer:
            try:
                await self._consumer.stop()
            except Exception:
                pass
