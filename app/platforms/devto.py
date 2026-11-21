from app.platforms.base import Platform, PlatformError, PostContent, PublishedPost


class DevToPlatform(Platform):
    """Publishes an article through the Forem API. Docs: https://developers.forem.com/api/v1"""

    name = "DEV Community"
    required_settings = ("devto_api_key",)

    API_URL = "https://dev.to/api/articles"

    async def publish(self, content: PostContent) -> PublishedPost:
        response = await self.http.post(
            self.API_URL,
            headers={
                "api-key": self.settings.devto_api_key,
                "Accept": "application/vnd.forem.api-v1+json",
            },
            json={
                "article": {
                    "title": content.title,
                    "body_markdown": content.message,
                    "published": True,
                }
            },
        )
        data = self.parse_json(response)

        url = data.get("url")
        if not url:
            raise PlatformError("DEV accepted the article but did not return its URL.")
        return PublishedPost(url=url, public=bool(data.get("published", True)))
