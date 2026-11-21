import re

from app.platforms.base import Platform, PlatformError, PostContent, PublishedPost, error_detail

# LinkedIn's "little text" format treats these characters as markup, so they need a backslash.
# https://learn.microsoft.com/linkedin/marketing/community-management/shares/little-text-format
RESERVED_CHARACTERS = re.compile(r"([\\|{}@\[\]()<>#*_~])")


class LinkedInPlatform(Platform):
    """Shares a public post on the member's profile. Docs: Share on LinkedIn / Posts API."""

    name = "LinkedIn"
    required_settings = ("linkedin_access_token", "linkedin_person_urn")

    API_URL = "https://api.linkedin.com/rest/posts"

    async def publish(self, content: PostContent) -> PublishedPost:
        response = await self.http.post(
            self.API_URL,
            headers={
                "Authorization": f"Bearer {self.settings.linkedin_access_token}",
                "LinkedIn-Version": self.settings.linkedin_api_version,
                "X-Restli-Protocol-Version": "2.0.0",
            },
            json={
                "author": self.settings.linkedin_person_urn,
                "commentary": RESERVED_CHARACTERS.sub(r"\\\1", content.message),
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False,
            },
        )
        if response.is_error:
            raise PlatformError(f"HTTP {response.status_code}: {error_detail(response)}")

        # The new post's URN comes back in a header, not the body.
        post_urn = response.headers.get("x-restli-id")
        if not post_urn:
            raise PlatformError("LinkedIn accepted the post but did not return its ID.")
        return PublishedPost(url=f"https://www.linkedin.com/feed/update/{post_urn}/")
