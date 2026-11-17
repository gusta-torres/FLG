from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "FLG Content System"
    app_env: str = "development"

    llm_provider: str = "mock"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"

    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"

    database_url: str = "sqlite+aiosqlite:///./flg.db"

    # Origens permitidas para CORS (separadas por vírgula)
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # Autenticação / JWT
    jwt_secret: str = "dev-insecure-secret-change-me-in-production-0123456789"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # Usuário inicial de marketing (criado automaticamente se não existir)
    admin_email: str = "admin@flg.local"
    admin_password: str = "flg-admin-123"
    admin_name: str = "Equipe de Marketing"


@lru_cache
def get_settings() -> Settings:
    return Settings()
