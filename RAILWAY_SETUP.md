# Railway Deployment Guide

## Quick Setup for Railway.com

### 1. Deploy to Railway

1. Go to [Railway.app](https://railway.app/)
2. Create a new project
3. Connect this GitHub repository (or deploy from CLI)
4. Railway will auto-detect it's a Python project

### 2. Configure Environment Variables

In Railway Dashboard, go to **Variables** and add:

```
TWILIO_ACCOUNT_SID=<your-twilio-account-sid>
TWILIO_AUTH_TOKEN=<your-twilio-auth-token>
FORWARD_TO_NUMBER=<your-phone-number-with-country-code>
PORT=5000
```

### 3. Upload Google Credentials

**Option A: Upload via Railway CLI**
```bash
railway up google-credentials.json
```

**Option B: Base64 encode and store as environment variable**
```bash
# On your computer:
base64 google-credentials.json > credentials.txt

# In Railway, add variable:
GOOGLE_CREDENTIALS_BASE64=<paste-the-base64-content>
```

Then update the code to decode it on startup.

### 4. Configure Deployment

Railway should use the `Procfile` which contains:
```
web: gunicorn --bind 0.0.0.0:$PORT --workers 2 realtime_translator:app
```

Or you can configure it in Railway settings:
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 2 realtime_translator:app`
- **Build Command**: `pip install -r requirements.txt`

### 5. Get Your Railway Domain

After deployment, Railway will give you a public URL like:
```
https://your-app.up.railway.app
```

### 6. Configure Twilio Webhook

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to **Phone Numbers → Manage → Active numbers**
3. Click your phone number
4. Under "Voice Configuration":
   - **A CALL COMES IN**: Webhook
   - **URL**: `https://your-app.up.railway.app/twilio-webhook`
   - **HTTP**: POST
5. Save

### 7. Test Your Deployment

1. Have someone call your Twilio number
2. You should receive a call on your configured phone number
3. Both parties will be connected

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `TWILIO_ACCOUNT_SID` | Your Twilio Account SID | `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `TWILIO_AUTH_TOKEN` | Your Twilio Auth Token | `your_auth_token` |
| `FORWARD_TO_NUMBER` | Your phone number (with country code) | `+1234567890` |
| `PORT` | Server port (Railway sets this automatically) | `5000` |
| `RAILWAY_PUBLIC_DOMAIN` | Auto-set by Railway | `your-app.up.railway.app` |

## Files Needed for Railway

- ✅ `realtime_translator.py` - Main application
- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Railway deployment config
- ✅ `google-credentials.json` - Google Cloud credentials (upload separately)

## Troubleshooting

### Logs
View logs in Railway Dashboard or via CLI:
```bash
railway logs
```

### Common Issues

1. **Port binding error**: Make sure the app uses `PORT` environment variable
2. **Google credentials not found**: Ensure `google-credentials.json` is uploaded or use base64 method
3. **Twilio webhook not working**: Verify the webhook URL uses your Railway domain

## Cost Estimates

- **Railway**: Free tier available, then ~$5-20/month
- **Twilio**: ~$0.02 per minute for calls
- **Google Cloud**: ~$0.006 per 15 seconds of audio processing

## Development vs Production

**Current Status**: 
- ✅ Basic call forwarding working
- ⚠️ Real-time translation requires Media Streams implementation

**For production deployment**:
- Use gunicorn (already configured in Procfile)
- Enable HTTPS (Railway provides this automatically)
- Monitor API costs
- Set up error tracking
