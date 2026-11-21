import json

from tests.conftest import DISCORD_WEBHOOK
from tests.test_posting import MESSAGE, mock_all_platforms


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_platforms_lists_all_five_as_configured(client):
    statuses = client.get("/platforms").json()

    assert [status["platform"] for status in statuses] == ["DEV Community", "LinkedIn", "Threads", "Blogger", "Discord"]
    assert all(status["configured"] and status["missing_settings"] == [] for status in statuses)


def test_platforms_shows_missing_settings_without_values(client, settings):
    settings.blogger_refresh_token = ""
    settings.discord_webhook_url = ""

    statuses = {status["platform"]: status for status in client.get("/platforms").json()}

    assert statuses["Blogger"] == {
        "platform": "Blogger",
        "configured": False,
        "missing_settings": ["BLOGGER_REFRESH_TOKEN"],
    }
    assert statuses["Discord"]["missing_settings"] == ["DISCORD_WEBHOOK_URL"]
    assert statuses["DEV Community"]["configured"] is True


def test_threads_token_is_sent_as_a_header_not_in_the_url(client, platform_api):
    mock_all_platforms(platform_api)

    client.post("/posting", json={"message": MESSAGE})

    threads_requests = [call.request for call in platform_api.calls if call.request.url.host == "graph.threads.net"]
    assert len(threads_requests) == 3
    for request in threads_requests:
        assert "access_token" not in str(request.url)
        assert request.headers["Authorization"] == "Bearer test-threads-token"


def test_discord_posts_under_a_friendly_name_without_pings(client, platform_api):
    mock_all_platforms(platform_api)

    client.post("/posting", json={"message": MESSAGE})

    discord_post = next(
        call.request for call in platform_api.calls if str(call.request.url).startswith(DISCORD_WEBHOOK) and call.request.method == "POST"
    )
    body = json.loads(discord_post.content)
    assert body["username"] == "Multi-Platform Poster"
    assert body["allowed_mentions"] == {"parse": []}
    assert body["content"] == MESSAGE
