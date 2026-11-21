import html
import time

from app.platforms.base import Platform, PlatformError, PostContent, PublishedPost

# Refresh the access token a little before Google says it expires.
TOKEN_EXPIRY_MARGIN_SECONDS = 60


class BloggerPlatform(Platform):
    """Publishes a blog post with the Blogger API v3. Docs: https://developers.google.com/blogger"""

    name = "Blogger"
    required_settings = (
        "blogger_client_id",
        "blogger_client_secret",
        "blogger_refresh_token",
        "blogger_blog_id",
    )

    TOKEN_URL = "https://oauth2.googleapis.com/token"
    API_URL = "https://www.googleapis.com/blogger/v3"

    _access_token: str | None = None
    _token_expires_at: float = 0.0

    async def publish(self, content: PostContent) -> PublishedPost:
        token = await self._get_access_token()
        response = await self.http.post(
            f"{self.API_URL}/blogs/{self.settings.blogger_blog_id}/posts/",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": content.title, "content": _to_html(content)},
        )
        data = self.parse_json(response)

        url = data.get("url")
        if not url:
            raise PlatformError("Blogger created the post but did not return its URL.")
        return PublishedPost(url=url, public=data.get("status", "LIVE") == "LIVE")

    async def _get_access_token(self) -> str:
        if self._access_token and time.monotonic() < self._token_expires_at:
            return self._access_token

        response = await self.http.post(
            self.TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": self.settings.blogger_client_id,
                "client_secret": self.settings.blogger_client_secret,
                "refresh_token": self.settings.blogger_refresh_token,
            },
        )
        data = self.parse_json(response)
        if not data.get("access_token"):
            raise PlatformError("Google did not return an access token.")

        self._access_token = data["access_token"]
        self._token_expires_at = time.monotonic() + int(data.get("expires_in", 3600)) - TOKEN_EXPIRY_MARGIN_SECONDS
        return self._access_token


def _to_html(content: PostContent) -> str:
    safe_message = html.escape(content.message)
    safe_link = html.escape(content.link)
    anchor = f'<a href="{html.escape(content.link, quote=True)}">{safe_link}</a>'
    return f"<p>{safe_message.replace(safe_link, anchor, 1)}</p>"
