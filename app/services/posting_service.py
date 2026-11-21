import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.platforms.base import Platform, PlatformError, PostContent
from app.schemas import PlatformResult, PlatformStatus, PostStatus

logger = logging.getLogger(__name__)


class PostingService:
    """Sends one message to every platform and collects a result for each of them."""

    def __init__(self, platforms: list[Platform], timezone: ZoneInfo) -> None:
        self.platforms = platforms
        self.timezone = timezone

    async def publish_everywhere(self, message: str, link: str) -> list[PlatformResult]:
        content = PostContent.from_message(message, link)
        logger.info("Publishing to %d platforms, CTA link %s", len(self.platforms), link)

        # All platforms run at the same time, and _publish_to never raises,
        # so one slow or broken platform can't hold up or cancel the others.
        results = list(await asyncio.gather(*(self._publish_to(platform, content) for platform in self.platforms)))

        succeeded = sum(result.status == PostStatus.SUCCESS for result in results)
        logger.info("Finished: %d of %d platforms succeeded", succeeded, len(results))
        return results

    def platform_statuses(self) -> list[PlatformStatus]:
        statuses = []
        for platform in self.platforms:
            missing = platform.missing_settings()
            statuses.append(PlatformStatus(platform=platform.name, configured=not missing, missing_settings=missing))
        return statuses

    async def _publish_to(self, platform: Platform, content: PostContent) -> PlatformResult:
        missing = platform.missing_settings()
        if missing:
            return self._failed(platform, f"Not configured. Missing: {', '.join(missing)}")

        try:
            post = await platform.publish(content)
        except PlatformError as exc:
            return self._failed(platform, str(exc))
        except httpx.TimeoutException:
            return self._failed(platform, "The platform did not respond in time.")
        except httpx.HTTPError as exc:
            return self._failed(platform, f"Network error: {exc.__class__.__name__}")
        except Exception:
            logger.exception("Unexpected error while posting to %s", platform.name)
            return self._failed(platform, "Unexpected error. Check the server logs for details.")

        posted_at = datetime.now(self.timezone)
        logger.info("%s: posted %s", platform.name, post.url)
        return PlatformResult(
            platform=platform.name,
            status=PostStatus.SUCCESS,
            posted_url=post.url,
            public_access=post.public,
            date=posted_at.strftime("%Y-%m-%d"),
            time=posted_at.strftime("%H:%M:%S"),
        )

    @staticmethod
    def _failed(platform: Platform, error: str) -> PlatformResult:
        logger.warning("%s: failed - %s", platform.name, error)
        return PlatformResult(platform=platform.name, status=PostStatus.FAILED, error=error)
