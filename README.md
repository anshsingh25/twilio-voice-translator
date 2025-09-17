# Twilio Bidirectional Voice Translator

A real-time voice translation system that enables seamless communication between Hindi and English speakers through Twilio phone calls.

## Features

- 🔄 **Bidirectional Translation**: Hindi ↔ English real-time translation
- 🎤 **Voice Activity Detection**: Automatic speech detection and processing
- 🌐 **Language Detection**: Auto-detect Hindi/English speech
- ⚡ **Low Latency**: Optimized for real-time conversation
- 📞 **Twilio Integration**: Works with any Twilio phone number
- 🔊 **High Quality Audio**: Google Cloud TTS with natural voices

## How It Works

1. **You call someone** through your Twilio number
2. **When they pick up**, the system starts listening
3. **You speak in English** → they hear it in Hindi
4. **They speak in Hindi** → you hear it in English
5. **Real-time conversation** with automatic translation

## Prerequisites

- Python 3.7+
- Google Cloud account with Speech-to-Text, Text-to-Speech, and Translation APIs enabled
- Twilio account with a phone number
- ngrok for local development

## Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the following APIs:
   - Cloud Speech-to-Text API
   - Cloud Text-to-Speech API
   - Cloud Translation API
4. Create a service account and download the JSON key
5. Save the key as `google-credentials.json` in this directory

### 3. Run Setup Script

```bash
python setup_twilio_translator.py
```

This script will:
- Check all dependencies
- Verify Google Cloud credentials
- Check ngrok status
- Update configuration files
- Provide setup instructions

### 4. Start ngrok (if not running)

```bash
ngrok http 3000
```

### 5. Configure Twilio

1. Go to your [Twilio Console](https://console.twilio.com/)
2. Navigate to Phone Numbers → Manage → Active numbers
3. Click on your phone number
4. Set the webhook URL to: `https://YOUR_NGROK_URL.ngrok-free.app/twilio-webhook`
5. Set HTTP method to POST
6. Save the configuration

### 6. Run the Translator

```bash
python advanced_twilio_translator.py
```

### 7. Test the System

1. Call your Twilio phone number
2. When the call connects, you'll hear welcome messages in both languages
3. Start speaking - the system will automatically translate between Hindi and English

## Files Overview

- `advanced_twilio_translator.py` - Main application with advanced features
- `bidirectional_twilio_translator.py` - Basic bidirectional translator
- `setup_twilio_translator.py` - Automated setup script
- `test_translation.py` - Test script for translation functions
- `requirements.txt` - Python dependencies
- `google-credentials.json` - Google Cloud service account key (you need to add this)

## Advanced Features

### Voice Activity Detection
- Automatically detects when someone is speaking
- Prevents processing of background noise
- Optimizes for real-time conversation

### Language Detection
- Automatically detects Hindi vs English speech
- Uses character analysis and word patterns
- Switches translation direction automatically

### Rate Limiting
- Prevents spam translations
- Minimum 2-second interval between translations
- Ensures smooth conversation flow

## Configuration Options

You can modify these settings in the code:

```python
# Voice activity detection threshold
VAD_THRESHOLD = 0.01

# Minimum confidence for speech recognition
CONFIDENCE_THRESHOLD = 0.6

# Minimum time between translations (seconds)
MIN_TRANSLATION_INTERVAL = 2.0

# Audio quality settings
SAMPLE_RATE = 8000  # Twilio standard
AUDIO_ENCODING = MULAW  # Twilio standard
```

## Troubleshooting

### Common Issues

1. **"Google credentials not found"**
   - Ensure `google-credentials.json` is in the project directory
   - Check that the file contains valid JSON

2. **"ngrok not running"**
   - Start ngrok with: `ngrok http 3000`
   - Update the webhook URL in Twilio console

3. **"Translation not working"**
   - Check Google Cloud API quotas
   - Ensure all required APIs are enabled
   - Run `python test_translation.py` to test functions

4. **"Audio quality issues"**
   - Check internet connection
   - Ensure stable ngrok tunnel
   - Verify Twilio account has sufficient credits

### Testing

Run the test script to verify everything is working:

```bash
python test_translation.py
```

This will test:
- Hindi to English translation
- English to Hindi translation
- English text-to-speech
- Hindi text-to-speech

## API Costs

- **Google Cloud Speech-to-Text**: ~$0.006 per 15 seconds
- **Google Cloud Translation**: ~$20 per 1M characters
- **Google Cloud Text-to-Speech**: ~$4 per 1M characters
- **Twilio**: ~$0.02 per minute for calls

## Production Deployment

For production use:

1. Deploy to a cloud service (AWS, GCP, Azure)
2. Use a proper domain instead of ngrok
3. Set up SSL certificates
4. Configure proper logging and monitoring
5. Set up API rate limiting
6. Use environment variables for sensitive data

## Support

If you encounter issues:

1. Check the console output for error messages
2. Verify all APIs are enabled in Google Cloud
3. Ensure Twilio webhook is configured correctly
4. Test individual components using the test script

## License

This project is open source. Feel free to modify and distribute.

---

**Happy translating! 🎉**
