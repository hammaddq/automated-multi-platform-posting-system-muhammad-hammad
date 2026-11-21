import httpx

from app.config import Settings
from app.platforms.base import Platform
from app.platforms.blogger import BloggerPlatform
from app.platforms.devto import DevToPlatform
from app.platforms.discord import DiscordPlatform
from app.platforms.linkedin import LinkedInPlatform
from app.platforms.threads import ThreadsPlatform

# Every request publishes to all of these. Add a new integration by appending its class here.
PLATFORM_CLASSES: tuple[type[Platform], ...] = (
    DevToPlatform,
    LinkedInPlatform,
    ThreadsPlatform,
    BloggerPlatform,
    DiscordPlatform,
)


def build_platforms(settings: Settings, http: httpx.AsyncClient) -> list[Platform]:
    return [platform_class(settings, http) for platform_class in PLATFORM_CLASSES]
