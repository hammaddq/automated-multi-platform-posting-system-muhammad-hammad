from collections.abc import Iterator

import pytest
import respx
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/111/test-token"


@pytest.fixture
def settings() -> Settings:
    # _env_file=None keeps the real .env (and real keys) out of the tests.
    return Settings(
        _env_file=None,
        app_timezone="UTC",
        devto_api_key="test-devto-key",
        linkedin_access_token="test-linkedin-token",
        linkedin_person_urn="urn:li:person:abc123",
        threads_access_token="test-threads-token",
        threads_user_id="1234",
        blogger_client_id="client-id",
        blogger_client_secret="client-secret",
        blogger_refresh_token="refresh-token",
        blogger_blog_id="5678",
        discord_webhook_url=DISCORD_WEBHOOK,
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def platform_api() -> Iterator[respx.MockRouter]:
    """Intercepts every outgoing HTTP call, so tests never reach the real platforms."""
    with respx.mock(assert_all_called=False) as router:
        yield router
