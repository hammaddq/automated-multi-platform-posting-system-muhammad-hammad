from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar

import httpx

from app.config import Settings
from app.utils.text import build_title


class PlatformError(Exception):
    """A platform rejected the post or returned something we could not use."""


@dataclass(frozen=True)
class PostContent:
    message: str
    link: str
    title: str

    @classmethod
    def from_message(cls, message: str, link: str) -> "PostContent":
        return cls(message=message, link=link, title=build_title(message, link))


@dataclass(frozen=True)
class PublishedPost:
    url: str
    public: bool = True


class Platform(ABC):
    name: ClassVar[str]
    required_settings: ClassVar[tuple[str, ...]] = ()

    def __init__(self, settings: Settings, http: httpx.AsyncClient) -> None:
        self.settings = settings
        self.http = http

    def missing_settings(self) -> list[str]:
        return [key.upper() for key in self.required_settings if not getattr(self.settings, key, "")]

    @abstractmethod
    async def publish(self, content: PostContent) -> PublishedPost:
        """Publish the content and return where it can be found."""

    def parse_json(self, response: httpx.Response) -> Any:
        """Return the JSON body, or raise PlatformError with the platform's own error text."""
        if response.is_error:
            raise PlatformError(f"HTTP {response.status_code}: {error_detail(response)}")
        try:
            return response.json()
        except ValueError as exc:
            raise PlatformError("Platform returned a response that is not JSON.") from exc


def error_detail(response: httpx.Response) -> str:
    """Pull the most useful error message out of a failed response."""
    try:
        body = response.json()
    except ValueError:
        return response.text.strip()[:200] or response.reason_phrase

    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            return str(error.get("message") or error)
        for key in ("error_description", "message", "error", "errors"):
            if body.get(key):
                return str(body[key])
    return str(body)[:200]
