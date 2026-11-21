import re
from urllib.parse import urlsplit

from pydantic import HttpUrl, TypeAdapter, ValidationError

# Anything with a scheme (so "ftp://..." is caught and rejected) or a bare "www." address.
LINK_PATTERN = re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.-]*://[^\s<>\"']+|\bwww\.[^\s<>\"']+")

# Punctuation that usually belongs to the sentence, not the URL, e.g. "Visit https://example.com."
TRAILING_PUNCTUATION = ".,;:!?)]}'\""

TITLE_MAX_LENGTH = 60

_http_url = TypeAdapter(HttpUrl)


def find_links(text: str) -> list[str]:
    return [match.rstrip(TRAILING_PUNCTUATION) for match in LINK_PATTERN.findall(text)]


def link_error(link: str) -> str | None:
    """Return a readable reason when the link is not a usable public URL, otherwise None."""
    parts = urlsplit(link)

    if parts.scheme.lower() not in ("http", "https"):
        return f"'{link}' must start with http:// or https://."

    try:
        _http_url.validate_python(link)
    except ValidationError:
        return f"'{link}' is not a valid URL."

    host = parts.hostname or ""
    labels = host.split(".")
    if len(labels) < 2 or not all(labels) or not re.fullmatch(r"[a-zA-Z]{2,63}|xn--[a-zA-Z0-9-]+", labels[-1]):
        return f"'{link}' does not have a valid domain name."

    return None


def build_title(message: str, link: str) -> str:
    """Make a short title out of the message text, for platforms that need one."""
    text = " ".join(message.replace(link, " ").split()).strip(" -–—:|")
    if not text:
        return "New post"
    if len(text) <= TITLE_MAX_LENGTH:
        return text.rstrip(".")

    cut = text[:TITLE_MAX_LENGTH].rsplit(" ", 1)[0]
    return cut.rstrip(" ,.;:") + "…"
