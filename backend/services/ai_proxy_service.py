import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from core.config import settings
from uuid import UUID
from models.message import Message
from ws_manager.manager import manager


class AIProxyService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _call_ai_backend(self, text: str) -> dict:
        res = await self.client.post(
            f"{settings.AI_BACKEND_URL}/analyze",
            json={"text": text},
            timeout=90.0,
        )
        res.raise_for_status()
        return res.json()

    async def analyze_and_update_message(
        self, message_id: UUID, text: str, db
    ):
        msg = await db.get(Message, message_id)
        if not msg:
            return

        try:
            analysis = await self._call_ai_backend(text)
            msg.sentiment_label = analysis["label"]
            msg.sentiment_score = analysis["score"]
            msg.sentiment_status = "complete"
            await db.commit()

            await manager.broadcast_to_channel(
                str(msg.channel_id),
                {
                    "type": "sentiment_update",
                    "id": str(msg.id),
                    "sentiment_label": msg.sentiment_label,
                    "sentiment_score": msg.sentiment_score,
                    "sentiment_status": msg.sentiment_status,
                },
            )
        except Exception:
            msg.sentiment_status = "failed"
            await db.commit()
            raise
