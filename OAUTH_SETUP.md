# OAuth2 Setup Instructions

## Changes Made

Flask-Dance blueprint is now registered at `/login` with route prefix.

### URLs:
- **Login**: `https://converter.synapticlabs.ai/login/google`
- **Callback**: `https://converter.synapticlabs.ai/login/google/authorized`

(Flask-Dance adds `/google` to the url_prefix automatically)

## Google Cloud Console Setup

1. Go to https://console.cloud.google.com
2. Select your project
3. Navigate to: **APIs & Services** → **Credentials**
4. Click on your OAuth 2.0 Client ID
5. Update **Authorized redirect URIs** to:

```
https://converter.synapticlabs.ai/login/google/authorized
http://localhost:8080/login/google/authorized
```

6. Click **Save**

## Railway Environment Variables

Ensure these are set in Railway:

```bash
GOOGLE_OAUTH_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=<your-secret>  # SEAL THIS
SECRET_KEY=<64-char-hex-string>  # SEAL THIS
GOOGLE_CLOUD_PROJECT_ID=<your-project-id>
OAUTHLIB_RELAX_TOKEN_SCOPE=true
```

## Testing

After deploying:

1. Go to https://converter.synapticlabs.ai
2. Click "Sign in with Google"
3. Should redirect to Google OAuth consent screen
4. Approve permissions
5. Should redirect back to app (logged in)
6. Try converting a markdown file to Google Docs

## Troubleshooting

If OAuth still doesn't work, check Railway logs:
- Look for "Google OAuth blueprint registered at /login/google"
- Check for any Flask-Dance errors
- Verify environment variables are set

Test the endpoint directly:
```bash
curl https://converter.synapticlabs.ai/login/google
```

Should redirect to Google OAuth (not return 404).
