# Local Development Setup

This guide covers setting up your local development environment for Snap and Say, with a focus on camera/microphone access which requires a secure context (HTTPS).

## Prerequisites

- Node.js 18+ and pnpm
- Python 3.11+ and uv
- Docker (for running Supabase locally)
- ngrok or Cloudflare Tunnel (for HTTPS tunneling)

## Quick Start

```bash
# Backend
cd backend
uv sync
cp .env.example .env  # Configure with Supabase credentials
uv run uvicorn app.main:app --reload

# Frontend
cd frontend
pnpm install
cp .env.example .env.local  # Configure API URL
pnpm dev
```

## Secure Context for Camera/Microphone

Modern browsers require HTTPS (a "secure context") to access the camera and microphone APIs. This is Chrome 47+ and all modern browsers.

### Option 1: Chrome Localhost Exception (Simplest)

Chrome treats `localhost` and `127.0.0.1` as secure contexts by default. Use these URLs:

```
http://localhost:3000
```

**Note:** This only works for Chrome/Chromium browsers. Firefox and Safari may still require HTTPS.

### Option 2: Chrome Flags (Testing Only)

For testing on non-localhost URLs (like your local IP), you can enable insecure origins:

1. Open `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
2. Add your URL: `http://192.168.x.x:3000`
3. Restart Chrome

> ⚠️ **Warning:** This is for development only. Never use in production.

### Option 3: ngrok (Recommended for Mobile Testing)

ngrok provides HTTPS tunneling, useful for testing on real mobile devices.

```bash
# Install ngrok
brew install ngrok  # macOS
# or from https://ngrok.com/download

# Authenticate (one-time)
ngrok config add-authtoken YOUR_TOKEN

# Tunnel frontend
ngrok http 3000
```

Use the generated `https://xxx.ngrok-free.app` URL on your phone.

**Update frontend `.env.local`:**
```env
NEXT_PUBLIC_BACKEND_URL=https://xxx.ngrok-free.app/api
```

### Option 4: Cloudflare Tunnel (Alternative to ngrok)

```bash
# Install cloudflared
brew install cloudflare/cloudflare/cloudflared

# Quick tunnel (no account needed)
cloudflared tunnel --url http://localhost:3000
```

## Testing Camera/Microphone Access

1. Open your app URL
2. Navigate to the Snap page
3. Browser should prompt for camera permission
4. If permissions are denied silently or `navigator.mediaDevices` is undefined, you're not in a secure context

## Troubleshooting

### "NotAllowedError: Permission denied"
- Ensure you're using localhost or HTTPS
- Check browser settings for blocked permissions
- Try an incognito window (fresh permission state)

### "TypeError: Cannot read properties of undefined (navigator.mediaDevices)"
- You're not in a secure context
- Use one of the options above to enable HTTPS

### Supabase Connection Issues
- Ensure `supabase start` is running
- Check anon key and URL in `.env.local`
- For anonymous auth, ensure it's enabled in Supabase dashboard

## Additional Resources

- [Chrome Secure Context Requirements](https://developer.chrome.com/blog/secure-your-origins/)
- [ngrok Documentation](https://ngrok.com/docs)
- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
