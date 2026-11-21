import pytest

from app.utils.text import build_title, find_links

VALID_MESSAGE = "Check out our latest business platform and grow your online visibility. https://example.com"


@pytest.mark.parametrize(
    ("payload", "expected_error"),
    [
        ({}, "This field is required."),
        ({"message": ""}, "Must not be empty."),
        ({"message": "   "}, "Must not be empty."),
        ({"message": "x" * 190 + " https://example.com"}, "Must not exceed 200 characters."),
        ({"message": "No link in this message at all."}, "Message must include one CTA link"),
        ({"message": "Two links https://a.com and https://b.com"}, "exactly one CTA link, but 2 were found"),
        ({"message": "Bad scheme ftp://example.com"}, "must start with http:// or https://"),
        ({"message": "Missing scheme www.example.com"}, "must start with http:// or https://"),
        ({"message": "No domain https://localhost"}, "does not have a valid domain name"),
        ({"message": "Broken https://exa mple"}, "does not have a valid domain name"),
        ({"message": VALID_MESSAGE, "platforms": ["x"]}, "Unexpected field"),
        ({"message": 123}, "Input should be a valid string"),
    ],
)
def test_invalid_messages_are_rejected(client, payload, expected_error):
    response = client.post("/posting", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert any(expected_error in error["message"] for error in body["errors"]), body


def test_invalid_json_is_rejected(client):
    response = client.post("/posting", content="{not json", headers={"Content-Type": "application/json"})

    assert response.status_code == 422
    assert response.json()["errors"][0]["message"] == "Request body is not valid JSON."


def test_message_of_exactly_200_characters_is_allowed(client, platform_api):
    link = " https://example.com"
    message = "x" * (200 - len(link)) + link
    platform_api.route().respond(500)

    assert client.post("/posting", json={"message": message}).status_code == 200


def test_trailing_punctuation_is_not_part_of_the_link():
    assert find_links("Visit (https://example.com/page).") == ["https://example.com/page"]


def test_title_is_built_from_message_text_without_the_link():
    assert build_title(VALID_MESSAGE, "https://example.com") == (
        "Check out our latest business platform and grow your online…"
    )
    assert build_title("https://example.com", "https://example.com") == "New post"
