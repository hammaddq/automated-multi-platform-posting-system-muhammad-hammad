import json

import httpx
import respx

from tests.conftest import DISCORD_WEBHOOK

MESSAGE = "Grow your online visibility with our new platform (beta). https://example.com/launch"


def mock_all_platforms(api: respx.MockRouter) -> None:
    api.post("https://dev.to/api/articles").respond(
        201, json={"url": "https://dev.to/hammad/grow-your-online-visibility-1a2b", "published": True}
    )
    api.post("https://api.linkedin.com/rest/posts").respond(201, headers={"x-restli-id": "urn:li:share:7001"})

    api.post("https://graph.threads.net/v1.0/1234/threads").respond(200, json={"id": "container-1"})
    api.post("https://graph.threads.net/v1.0/1234/threads_publish").respond(200, json={"id": "post-1"})
    api.get("https://graph.threads.net/v1.0/post-1").respond(
        200, json={"permalink": "https://www.threads.com/@hammad/post/ABC"}
    )

    api.post("https://oauth2.googleapis.com/token").respond(200, json={"access_token": "google-token", "expires_in": 3600})
    api.post("https://www.googleapis.com/blogger/v3/blogs/5678/posts/").respond(
        200, json={"url": "https://hammad.blogspot.com/2026/11/grow.html", "status": "LIVE"}
    )

    api.post(DISCORD_WEBHOOK).respond(200, json={"id": "999", "channel_id": "222"})
    api.get(DISCORD_WEBHOOK).respond(200, json={"guild_id": "333"})


def results_by_platform(response: httpx.Response) -> dict:
    return {result["platform"]: result for result in response.json()["results"]}


def test_posts_to_all_five_platforms(client, platform_api):
    mock_all_platforms(platform_api)

    response = client.post("/posting", json={"message": MESSAGE})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    results = results_by_platform(response)
    assert set(results) == {"DEV Community", "LinkedIn", "Threads", "Blogger", "Discord"}
    assert all(result["status"] == "success" and result["error"] is None for result in results.values())
    assert all(result["date"] and result["time"] for result in results.values())

    assert results["LinkedIn"]["posted_url"] == "https://www.linkedin.com/feed/update/urn:li:share:7001/"
    assert results["Threads"]["posted_url"] == "https://www.threads.com/@hammad/post/ABC"
    assert results["Discord"]["posted_url"] == "https://discord.com/channels/333/222/999"
    assert results["Discord"]["public_access"] is False
    assert results["Blogger"]["public_access"] is True


def test_one_failure_does_not_stop_the_others(client, platform_api):
    mock_all_platforms(platform_api)
    platform_api.post("https://dev.to/api/articles").respond(401, json={"error": "unauthorized", "status": 401})

    response = client.post("/posting", json={"message": MESSAGE})

    results = results_by_platform(response)
    assert response.json()["success"] is True
    assert results["DEV Community"]["status"] == "failed"
    assert results["DEV Community"]["error"] == "HTTP 401: unauthorized"
    assert results["DEV Community"]["posted_url"] is None
    assert results["DEV Community"]["date"] is None
    assert all(results[name]["status"] == "success" for name in ("LinkedIn", "Threads", "Blogger", "Discord"))


def test_timeouts_and_network_errors_are_reported(client, platform_api):
    mock_all_platforms(platform_api)
    platform_api.post("https://api.linkedin.com/rest/posts").mock(side_effect=httpx.ReadTimeout("slow"))
    platform_api.post(DISCORD_WEBHOOK).mock(side_effect=httpx.ConnectError("down"))

    results = results_by_platform(client.post("/posting", json={"message": MESSAGE}))

    assert results["LinkedIn"]["error"] == "The platform did not respond in time."
    assert results["Discord"]["error"] == "Network error: ConnectError"
    assert results["Blogger"]["status"] == "success"


def test_all_platforms_failing_returns_success_false(client, platform_api):
    platform_api.route().respond(503, text="Service Unavailable")

    response = client.post("/posting", json={"message": MESSAGE})

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert all(result["status"] == "failed" for result in response.json()["results"])


def test_missing_credentials_are_reported_per_platform(client, platform_api, settings):
    mock_all_platforms(platform_api)
    settings.threads_access_token = ""

    results = results_by_platform(client.post("/posting", json={"message": MESSAGE}))

    assert results["Threads"]["status"] == "failed"
    assert results["Threads"]["error"] == "Not configured. Missing: THREADS_ACCESS_TOKEN"
    assert results["DEV Community"]["status"] == "success"


def test_linkedin_escapes_reserved_characters(client, platform_api):
    mock_all_platforms(platform_api)

    client.post("/posting", json={"message": MESSAGE})

    linkedin_route = next(route for route in platform_api.routes if "linkedin" in str(route.pattern))
    sent = json.loads(linkedin_route.calls.last.request.content)
    assert sent["commentary"].startswith("Grow your online visibility with our new platform \\(beta\\).")
    assert sent["visibility"] == "PUBLIC"


def test_blogger_turns_the_link_into_an_anchor(client, platform_api):
    mock_all_platforms(platform_api)

    client.post("/posting", json={"message": MESSAGE})

    blogger_route = next(route for route in platform_api.routes if "blogger" in str(route.pattern))
    sent = json.loads(blogger_route.calls.last.request.content)
    assert '<a href="https://example.com/launch">https://example.com/launch</a>' in sent["content"]
    assert sent["title"] == "Grow your online visibility with our new platform (beta)"
