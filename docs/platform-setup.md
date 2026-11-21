# Platform setup

This guide explains how to get the credentials for each platform and where each value goes in `.env`. All five platforms are free to use.

When you're done, start the server and open `GET /platforms` to see which platforms are fully configured.

## DEV Community

1. Sign in at [dev.to](https://dev.to).
2. Open **Settings → Extensions**, scroll to **DEV Community API Keys**, enter a description, and click **Generate API Key**.
3. Copy the key into `.env`:

```env
DEVTO_API_KEY=<key>
```

Docs: [Forem API v1](https://developers.forem.com/api/v1)

## LinkedIn

LinkedIn developer apps must be linked to a LinkedIn Page. If you don't have one, create a free one first.

1. Open [LinkedIn Developers](https://www.linkedin.com/developers/apps) and click **Create app**. Fill in the name, your LinkedIn Page, and a logo, then accept the terms.
2. On the **Products** tab, request access to both of these products. Both are approved immediately.
   - **Share on LinkedIn**, which grants `w_member_social`.
   - **Sign In with LinkedIn using OpenID Connect**, which grants `openid` and `profile` and is needed to look up your member ID.
3. On the **Auth** tab, add a redirect URL, for example `http://127.0.0.1:8766/callback`, and copy the **Client ID** and **Client Secret**.
4. Open this URL in a browser and click **Allow**:

```text
https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=<CLIENT_ID>&redirect_uri=http%3A%2F%2F127.0.0.1%3A8766%2Fcallback&scope=openid%20profile%20w_member_social
```

5. Copy the `code` value from the redirect URL and exchange it for a token:

```bash
curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
  -d grant_type=authorization_code -d code=<CODE> \
  -d redirect_uri=http://127.0.0.1:8766/callback \
  -d client_id=<CLIENT_ID> -d client_secret=<CLIENT_SECRET>
```

6. Get your member ID. It is the `sub` field in the response:

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" https://api.linkedin.com/v2/userinfo
```

7. Copy the values into `.env`:

```env
LINKEDIN_ACCESS_TOKEN=<access_token>
LINKEDIN_PERSON_URN=urn:li:person:<sub>
LINKEDIN_API_VERSION=202610
```

The access token is valid for 60 days. `LINKEDIN_API_VERSION` must be a version LinkedIn currently supports. LinkedIn keeps each monthly version for about a year.

Docs: [Share on LinkedIn](https://learn.microsoft.com/linkedin/consumer/integrations/self-serve/share-on-linkedin), [Posts API](https://learn.microsoft.com/linkedin/marketing/community-management/shares/posts-api)

## Threads

1. Open [Meta for Developers](https://developers.facebook.com/apps) and click **Create app**. Choose the **Access the Threads API** use case. You don't need to connect a business portfolio.
2. Open **Use cases → Access the Threads API → Customize → Permissions** and add `threads_content_publish`. `threads_basic` is included by default.
3. Open **App roles → Roles → Add People**, choose **Threads Tester**, and enter your Threads username.
4. On Threads, open **Settings → Account → Website permissions → Invites** and accept the invite.
5. Back in the use case, open **Settings → User Token Generator**, click **Generate Access Token** next to your account, and approve the request. This creates a long-lived token that is valid for about 60 days.
6. Get your Threads user ID:

```bash
curl -H "Authorization: Bearer <TOKEN>" "https://graph.threads.net/v1.0/me?fields=id,username"
```

7. Copy the values into `.env`:

```env
THREADS_ACCESS_TOKEN=<token>
THREADS_USER_ID=<id>
```

While the app stays in development mode, it can only post to its tester accounts. That is all this project needs.

Docs: [Threads API](https://developers.facebook.com/docs/threads), [Create posts](https://developers.facebook.com/docs/threads/posts)

## Blogger

1. Create a blog at [blogger.com](https://www.blogger.com). The blog ID is the number in the dashboard URL: `blogger.com/blog/posts/<BLOG_ID>`.
2. In [Google Cloud console](https://console.cloud.google.com), create a project and enable the **Blogger API**.
3. Open **Google Auth Platform**, set up the consent screen with audience **External**, and add your Google account under **Audience → Test users**.
4. Open **Clients → Create client**, choose **Desktop app**, and copy the client ID and client secret.
5. Open this URL, choose your account, and click **Allow**:

```text
https://accounts.google.com/o/oauth2/v2/auth?client_id=<CLIENT_ID>&redirect_uri=http%3A%2F%2F127.0.0.1%3A8765%2F&response_type=code&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fblogger&access_type=offline&prompt=consent
```

6. Copy the `code` value from the redirect URL and exchange it for a refresh token:

```bash
curl -X POST https://oauth2.googleapis.com/token \
  -d grant_type=authorization_code -d code=<CODE> \
  -d redirect_uri=http://127.0.0.1:8765/ \
  -d client_id=<CLIENT_ID> -d client_secret=<CLIENT_SECRET>
```

7. Copy the values into `.env`:

```env
BLOGGER_CLIENT_ID=<client_id>
BLOGGER_CLIENT_SECRET=<client_secret>
BLOGGER_REFRESH_TOKEN=<refresh_token>
BLOGGER_BLOG_ID=<blog_id>
```

The service uses the refresh token to get a new access token whenever it needs one. While the consent screen is in **Testing**, Google expires refresh tokens after 7 days. Publish the consent screen to keep the token longer.

Docs: [Blogger API v3](https://developers.google.com/blogger/docs/3.0/using), [OAuth for desktop apps](https://developers.google.com/identity/protocols/oauth2/native-app)

## Discord

1. In a Discord server you manage, open **Edit Channel → Integrations → Webhooks** for the channel, and click **New Webhook**.
2. Click **Copy Webhook URL**.
3. Paste it into `.env`:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/<id>/<token>
```

The webhook URL contains a secret token, so treat it like a password.

Docs: [Execute Webhook](https://discord.com/developers/docs/resources/webhook#execute-webhook)
