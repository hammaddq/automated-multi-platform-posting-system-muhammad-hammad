from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Automated Multi-Platform Posting System"
    app_timezone: str = "UTC"
    request_timeout_seconds: float = 15.0
    log_file: str = ""

    # DEV Community
    devto_api_key: str = ""

    # LinkedIn
    linkedin_access_token: str = ""
    linkedin_person_urn: str = ""
    linkedin_api_version: str = "202610"

    # Threads
    threads_access_token: str = ""
    threads_user_id: str = ""

    # Blogger
    blogger_client_id: str = ""
    blogger_client_secret: str = ""
    blogger_refresh_token: str = ""
    blogger_blog_id: str = ""

    # Discord
    discord_webhook_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
