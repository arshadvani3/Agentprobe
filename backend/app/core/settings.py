from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM provider — set GROQ_API_KEY to use Groq in production; otherwise Ollama
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"

    # Ollama (judge LLM — used when GROQ_API_KEY is not set)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_temperature: float = 0.7
    ollama_timeout: int = 120

    # PostgreSQL — strip SQLAlchemy prefix if present
    postgres_url: str = "postgresql://postgres:postgres@localhost:5432/agentprobe"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # ChromaDB
    chromadb_path: str = "./data/chromadb"

    # CORS — comma-separated allowed origins; "*" allows all
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Auth — if empty, auth is disabled (dev mode)
    agentprobe_api_key: str = ""

    # App
    log_level: str = "INFO"

    @property
    def allowed_origins(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return origins if origins else ["*"]

    @property
    def asyncpg_url(self) -> str:
        """Return a URL asyncpg can use (no +asyncpg driver prefix)."""
        return self.postgres_url.replace("postgresql+asyncpg://", "postgresql://")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
