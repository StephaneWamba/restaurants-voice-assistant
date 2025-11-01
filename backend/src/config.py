from pydantic_settings import BaseSettings
from functools import lru_cache
from pydantic import ConfigDict


class Settings(BaseSettings):
    supabase_url: str
    supabase_anon_key: str  # Anon key for reads (subject to RLS)
    openai_api_key: str
    vapi_secret_key: str
    environment: str = "development"
    cache_ttl_seconds: int = 60
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    cors_origins: str = "*"
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_prefix="",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
