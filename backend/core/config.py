from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_BROADCAST_TOPIC: str = "chat.broadcasts"
    KAFKA_AI_ANALYSIS_TOPIC: str = "ai.analysis"
    JWT_SECRET: str
    JWT_ACCESS_EXPIRY_MINUTES: int = 15
    JWT_REFRESH_EXPIRY_DAYS: int = 7
    ENCRYPTION_KEYS: str
    FRONTEND_URL: str
    AI_BACKEND_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def encryption_keys_list(self) -> list[str]:
        return [k.strip() for k in self.ENCRYPTION_KEYS.split(",")]


settings = Settings() # type: ignore
