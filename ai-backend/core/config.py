from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    HOST: str = "127.0.0.1"
    PORT: int = 8001

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
