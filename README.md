# Real-Time Bidirectional Voice Translator

A Twilio-powered voice translation system that provides real-time translation between Hindi and English during phone calls using Google Cloud AI and Twilio Media Streams.

## Features

- 🔄 **Bidirectional Translation**: Real-time Hindi ↔ English translation
- 📞 **Twilio Media Streams**: Low-latency audio streaming
- 🎤 **Google Cloud AI**: 
  - Speech-to-Text for transcription
  - Translation API for language conversion
  - Text-to-Speech for natural voice output
- 🌐 **Automatic Call Forwarding**: Forwards incoming calls to configured number
- ⚡ **Real-Time Processing**: Instant translation during conversation

## How It Works

1. Someone calls your Twilio number (speaks English)
2. System automatically forwards call to your configured number (+441138876033)
3. Real-time translation happens in both directions:
   - English → Hindi (for receiver to hear)
   - Hindi → English (for caller to hear)
4. Both parties hear translated audio in real-time through media streams

## Prerequisites

- Python 3.11+
- Twilio account with a phone number
- Google Cloud account with the following APIs enabled:
  - Cloud Speech-to-Text API
  - Cloud Translation API
  - Cloud Text-to-Speech API

## Setup Instructions

### 1. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the following APIs:
   - Cloud Speech-to-Text API
   - Cloud Text-to-Speech API
   - Cloud Translation API
4. Create a service account and download the JSON key
5. Save the key as `google-credentials.json` in project root

### 2. Environment Variables

Set the following secrets in your Replit project or create a `.env` file:

```bash
FORWARD_TO_NUMBER=+441138876033
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
```

### 3. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python media_stream_translator.py
```

The server will start on port 5000.

### 4. Twilio Configuration

1. Go to your [Twilio Console](https://console.twilio.com/)
2. Navigate to Phone Numbers → Manage → Active numbers
3. Click on your phone number
4. Under "Voice & Fax" → "A Call Comes In"
5. Set Webhook URL to: `https://your-domain.com/twilio-webhook`
6. Method: POST
7. Save configuration

## API Endpoints

- `GET /` - Status and features information
- `GET /health` - Health check with active streams count
- `POST /twilio-webhook` - Main webhook for incoming calls
- `POST /receiver-connected/<call_sid>` - Handles receiver connection
- `POST /call-ended` - Cleanup when call ends
- `WebSocket /media-stream/<call_sid>/<participant>` - Audio stream handling

## Project Structure

```
.
├── media_stream_translator.py  # Main application with Media Streams
├── improved_hindi_translator.py # Enhanced translator (alternative)
├── requirements.txt            # Python dependencies
├── google-credentials.json     # Google Cloud credentials (not in git)
├── .gitignore                 # Git ignore rules
├── replit.md                  # Project documentation
└── README.md                  # This file
```

## Technology Stack

- **Backend**: Python 3.11, Flask
- **WebSockets**: flask-sock for real-time communication
- **Speech Recognition**: Google Cloud Speech-to-Text
- **Translation**: Google Cloud Translation API
- **Voice Synthesis**: Google Cloud Text-to-Speech
- **Telephony**: Twilio Media Streams API
- **Audio Processing**: audioop (mulaw encoding at 8kHz)

## Security Notes

- ✅ `google-credentials.json` is excluded from git
- ✅ Environment variables used for sensitive data
- ✅ `.gitignore` configured to exclude credentials
- ⚠️ Never commit API keys or tokens to version control

## Deployment

This project runs on Replit and can be deployed to any platform supporting:
- Python 3.11+
- WebSocket connections
- Public HTTPS endpoint (required for Twilio webhooks)

### Production Considerations

- Use production WSGI server (Gunicorn, uWSGI) instead of Flask dev server
- Implement proper logging and monitoring
- Add rate limiting for API endpoints
- Set up error handling and retry logic
- Configure SSL/TLS certificates

## Known Issues & Limitations

- `audioop` module is deprecated in Python 3.13 (currently using 3.11)
- Translation accuracy depends on speech clarity and background noise
- Network latency may affect real-time translation quality
- Google Cloud API costs apply per usage

## Testing

1. Call your Twilio number from any phone
2. When your configured number rings, answer it
3. Speak clearly in English or Hindi
4. Listen for the translated audio on the other end

## Troubleshooting

**No translation happening:**
- Check Google Cloud credentials are valid
- Verify all APIs are enabled in Google Cloud Console
- Speak clearly and minimize background noise
- Check console logs for errors

**Call not connecting:**
- Verify Twilio webhook URL is correct
- Check FORWARD_TO_NUMBER is set correctly
- Ensure Twilio account has sufficient credits

**Audio quality issues:**
- Check internet connection stability
- Verify network latency is reasonable
- Test with different phone connections

## API Costs

- **Google Cloud Speech-to-Text**: ~$0.006 per 15 seconds
- **Google Cloud Translation**: ~$20 per 1M characters
- **Google Cloud Text-to-Speech**: ~$4 per 1M characters
- **Twilio Voice**: ~$0.02 per minute for calls
- **Twilio Media Streams**: Free with voice calls

## License

MIT License - Feel free to use and modify for your needs.

## Support

For issues or questions, please open an issue in the GitHub repository.

---

**Built with ❤️ using Twilio Media Streams and Google Cloud AI**
