from app.platforms.base import Platform, PlatformError, PostContent, PublishedPost


class DiscordPlatform(Platform):
    """Posts to a channel through a webhook. Docs: https://discord.com/developers/docs/resources/webhook"""

    name = "Discord"
    required_settings = ("discord_webhook_url",)

    SENDER_NAME = "Multi-Platform Poster"

    _guild_id: str | None = None

    async def publish(self, content: PostContent) -> PublishedPost:
        response = await self.http.post(
            self.settings.discord_webhook_url,
            params={"wait": "true"},
            json={
                "content": content.message,
                "username": self.SENDER_NAME,
                # No pings, even if the message happens to contain @everyone.
                "allowed_mentions": {"parse": []},
            },
        )
        message = self.parse_json(response)

        if not message.get("id") or not message.get("channel_id"):
            raise PlatformError("Discord accepted the message but did not return its ID.")

        guild_id = await self._get_guild_id()
        url = f"https://discord.com/channels/{guild_id}/{message['channel_id']}/{message['id']}"

        # Discord messages are only visible to members of the server, so they are not public.
        return PublishedPost(url=url, public=False)

    async def _get_guild_id(self) -> str:
        if self._guild_id is None:
            webhook = self.parse_json(await self.http.get(self.settings.discord_webhook_url))
            if not webhook.get("guild_id"):
                raise PlatformError("Could not find which Discord server the webhook belongs to.")
            self._guild_id = str(webhook["guild_id"])
        return self._guild_id
