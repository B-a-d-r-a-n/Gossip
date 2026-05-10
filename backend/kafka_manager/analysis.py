from __future__ import annotations

import asyncio
import json
from uuid import UUID
import httpx
from aiokafka import AIOKafkaConsumer
from core.config import settings
from core.db import AsyncSessionLocal
from services.ai_proxy_service import AIProxyService


class AnalysisConsumer:
    def __init__(self, bootstrap_servers: str, http_client: httpx.AsyncClient):
        self._bootstrap_servers = bootstrap_servers
        self._http_client = http_client
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task | None = None

    async def start(self):
        for attempt in range(10):
            try:
                self._consumer = AIOKafkaConsumer(
                    settings.KAFKA_AI_ANALYSIS_TOPIC,
                    bootstrap_servers=self._bootstrap_servers,
                    group_id="ai-analysis-workers",
                    auto_offset_reset="earliest",
                    enable_auto_commit=False,
                    value_deserializer=lambda v: json.loads(v.decode()),
                    max_poll_interval_ms=300000,
                    request_timeout_ms=30000,
                    retry_backoff_ms=1000,
                    session_timeout_ms=30000,
                    heartbeat_interval_ms=10000,
                )
                await self._consumer.start()
                self._task = asyncio.create_task(self._poll_loop())
                return
            except Exception as e:
                wait = min(2 ** attempt, 30)
                print(f"Analysis consumer initial connection failed (attempt {attempt + 1}/10, {e}), retrying in {wait}s...")
                if self._consumer:
                    try:
                        await self._consumer.stop()
                    except Exception:
                        pass
                    self._consumer = None
                await asyncio.sleep(wait)
        print("Analysis consumer failed to connect after 10 attempts, starting background retry")
        asyncio.create_task(self._background_connect())

    async def _poll_loop(self):
        backoff = 1
        while True:
            try:
                consumer = self._consumer
                assert consumer is not None
                async for msg in consumer:
                    await self._process(msg)
                    await consumer.commit()
                raise RuntimeError("consumer.listen() exhausted")
            except asyncio.CancelledError:
                return
            except Exception as e:
                print(f"Analysis consumer error ({e}), reconnecting in {backoff}s\u2026")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
                for attempt in range(5):
                    try:
                        old_consumer = self._consumer
                        if old_consumer is not None:
                            try:
                                await old_consumer.stop()
                            except Exception:
                                pass
                        self._consumer = AIOKafkaConsumer(
                            settings.KAFKA_AI_ANALYSIS_TOPIC,
                            bootstrap_servers=self._bootstrap_servers,
                            group_id="ai-analysis-workers",
                            auto_offset_reset="earliest",
                            enable_auto_commit=False,
                            value_deserializer=lambda v: json.loads(v.decode()),
                            max_poll_interval_ms=300000,
                            request_timeout_ms=30000,
                            retry_backoff_ms=1000,
                            session_timeout_ms=30000,
                            heartbeat_interval_ms=10000,
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
                    settings.KAFKA_AI_ANALYSIS_TOPIC,
                    bootstrap_servers=self._bootstrap_servers,
                    group_id="ai-analysis-workers",
                    auto_offset_reset="earliest",
                    enable_auto_commit=False,
                    value_deserializer=lambda v: json.loads(v.decode()),
                    max_poll_interval_ms=300000,
                    request_timeout_ms=30000,
                    retry_backoff_ms=1000,
                    session_timeout_ms=30000,
                    heartbeat_interval_ms=10000,
                )
                await self._consumer.start()
                print("Analysis consumer connected successfully in background")
                self._task = asyncio.create_task(self._poll_loop())
                return
            except Exception as e:
                print(f"Background reconnect failed ({e}), retrying in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    async def _process(self, msg):
        job = msg.value
        try:
            async with AsyncSessionLocal() as db:
                service = AIProxyService(self._http_client)
                await service.analyze_and_update_message(
                    UUID(job["message_id"]), job["content"], db
                )
        except Exception as e:
            print(f"Failed to process message {job.get('message_id')}: {e}")

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
