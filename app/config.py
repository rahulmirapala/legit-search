from functools import lru_cache
try:
    # pydantic v2 moved BaseSettings to the separate `pydantic-settings` package.
    # Prefer pydantic_settings when available, otherwise fall back to pydantic for v1 compatibility.
    from pydantic_settings import BaseSettings
except Exception:
    from pydantic import BaseSettings

class Settings(BaseSettings):
    es_host: str = "http://localhost:9200"
    index_name: str = "legit_search_index"
    default_page_size: int = 10
    title_boost_default: float = 3.0
    llm_api_key: str | None = None  # Google AI Studio API key (Gemini) optional

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
