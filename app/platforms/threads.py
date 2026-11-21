import asyncio

import httpx

from app.platforms.base import Platform, PlatformError, PostContent, PublishedPost

# Meta returns this error code while a new container is still being processed.
MEDIA_NOT_READY_CODE = 24


class ThreadsPlatform(Platform):
    """Publishes a text post with the Threads API. Docs: https://developers.facebook.com/docs/threads"""

    name = "Threads"
    required_settings = ("threads_access_token", "threads_user_id")

    API_URL = "https://graph.threads.net/v1.0"
    PUBLISH_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 2.0

    async def publish(self, content: PostContent) -> PublishedPost:
        # Threads publishes in two steps: create a media container, then publish it.
        container_id = await self._create_container(content)
        post_id = await self._publish_container(container_id)
        return PublishedPost(url=await self._permalink(post_id))

    @property
    def _auth(self) -> dict[str, str]:
        # Sent as a header rather than the usual access_token query parameter,
        # so the token never shows up in URLs or request logs.
        return {"Authorization": f"Bearer {self.settings.threads_access_token}"}

    async def _create_container(self, content: PostContent) -> str:
        response = await self.http.post(
            f"{self.API_URL}/{self.settings.threads_user_id}/threads",
            headers=self._auth,
            data={"media_type": "TEXT", "text": content.message, "link_attachment": content.link},
        )
        return self._require_id(self.parse_json(response), "media container")

    async def _publish_container(self, container_id: str) -> str:
        for attempt in range(1, self.PUBLISH_ATTEMPTS + 1):
            response = await self.http.post(
                f"{self.API_URL}/{self.settings.threads_user_id}/threads_publish",
                headers=self._auth,
                data={"creation_id": container_id},
            )
            not_ready = response.is_error and _error_code(response) == MEDIA_NOT_READY_CODE
            if not_ready and attempt < self.PUBLISH_ATTEMPTS:
                await asyncio.sleep(self.RETRY_DELAY_SECONDS)
                continue
            return self._require_id(self.parse_json(response), "published post")

        raise PlatformError("Threads did not finish processing the post in time.")

    async def _permalink(self, post_id: str) -> str:
        response = await self.http.get(f"{self.API_URL}/{post_id}", headers=self._auth, params={"fields": "permalink"})
        permalink = self.parse_json(response).get("permalink")
        if not permalink:
            raise PlatformError("Threads published the post but did not return its link.")
        return permalink

    @staticmethod
    def _require_id(data: dict, what: str) -> str:
        if not data.get("id"):
            raise PlatformError(f"Threads did not return an ID for the {what}.")
        return str(data["id"])


def _error_code(response: httpx.Response) -> int | None:
    try:
        return response.json().get("error", {}).get("code")
    except (ValueError, AttributeError):
        return None
