from __future__ import annotations

from fastapi import WebSocket
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kafka_manager.producer import KafkaProducerManager


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, dict[str, list[WebSocket]]] = {}
        self._lock = asyncio.Lock()
        self.kafka_producer: KafkaProducerManager | None = None

    def setup(self, kafka_producer: KafkaProducerManager):
        self.kafka_producer = kafka_producer

    async def connect(self, websocket: WebSocket, channel_id: str, user_id: str):
        await websocket.accept()
        async with self._lock:
            self.active_connections \
                .setdefault(channel_id, {}) \
                .setdefault(user_id, []) \
                .append(websocket)

    async def disconnect(self, websocket: WebSocket, channel_id: str, user_id: str):
        async with self._lock:
            self._remove_socket(channel_id, user_id, websocket)

    async def disconnect_user(self, channel_id: str, user_id: str):
        async with self._lock:
            conns = self.active_connections.get(channel_id, {}).pop(user_id, [])
        for ws in conns:
            try:
                await ws.close(code=4003)
            except Exception:
                pass

    async def broadcast_to_channel(self, channel_id: str, message: dict):
        if self.kafka_producer:
            sent = await self.kafka_producer.publish_broadcast(channel_id, message)
            if sent:
                return  # Kafka consumer delivers to all instances
        await self._send_to_local_connections(channel_id, message)

    def _remove_socket(self, channel_id: str, user_id: str, websocket: WebSocket):
        channel = self.active_connections.get(channel_id)
        if not channel:
            return
        user_conns = channel.get(user_id)
        if not user_conns:
            return
        try:
            user_conns.remove(websocket)
        except ValueError:
            pass
        if not user_conns:
            del channel[user_id]
        if not channel:
            del self.active_connections[channel_id]

    async def _send_to_local_connections(self, channel_id: str, message: dict):
        async with self._lock:
            channel_users = self.active_connections.get(channel_id, {})
            snapshot: list[tuple[str, WebSocket]] = [
                (uid, ws)
                for uid, sockets in channel_users.items()
                for ws in sockets
            ]

        if not snapshot:
            return

        async def _send(user_id: str, ws: WebSocket):
            try:
                await ws.send_json(message)
                return None
            except Exception:
                return (user_id, ws)

        results = await asyncio.gather(*[_send(uid, ws) for uid, ws in snapshot])

        dead = [r for r in results if r is not None]
        if dead:
            async with self._lock:
                for user_id, ws in dead:
                    self._remove_socket(channel_id, user_id, ws)


manager = ConnectionManager()