from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from redis.asyncio import Redis
import httpx

from core.config import settings
from core.exceptions import AppException, app_exception_handler
from ws_manager.manager import manager
from routers.auth import router as auth_router
from routers.channels import router as channels_router
from routers.chat import router as chat_router
from services.ai_proxy_service import AIProxyService
from kafka_manager import KafkaProducerManager, BroadcastConsumer, AnalysisConsumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    app.state.redis = redis

    # HTTP client
    http_client = httpx.AsyncClient()
    app.state.http_client = http_client

    # Kafka producer + broadcast consumer
    kafka_producer = KafkaProducerManager(settings.KAFKA_BOOTSTRAP_SERVERS)
    await kafka_producer.start()
    app.state.kafka_producer = kafka_producer
    manager.setup(kafka_producer)

    broadcast_consumer = BroadcastConsumer(settings.KAFKA_BOOTSTRAP_SERVERS)
    await broadcast_consumer.start(manager._send_to_local_connections)

    # AI analysis consumer
    analysis_consumer = AnalysisConsumer(
        settings.KAFKA_BOOTSTRAP_SERVERS, http_client
    )
    await analysis_consumer.start()

    yield

    # Shutdown
    await broadcast_consumer.stop()
    await analysis_consumer.stop()
    await kafka_producer.stop()
    await redis.aclose()
    await http_client.aclose()


app = FastAPI(title="Chat App Backend", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler
app.add_exception_handler(AppException, app_exception_handler)


# Dependency for Redis
async def get_redis(request: Request):
    return request.app.state.redis


# Dependency for httpx client
async def get_http_client(request: Request):
    return request.app.state.http_client


# Dependency for AIProxyService
async def get_ai_proxy_service(request: Request):
    return AIProxyService(request.app.state.http_client)


api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(channels_router)
api_router.include_router(chat_router)

app.include_router(api_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
