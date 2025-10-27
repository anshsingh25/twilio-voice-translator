# Twilio Bidirectional Voice Translator

## Overview
A real-time voice translation system that enables seamless communication between Hindi and English speakers through Twilio phone calls. This project has been configured to run in the Replit environment.

## Current State
- **Main Application**: `improved_hindi_translator.py` - Flask web server on port 5000
- **Dependencies**: Installed via pip (Flask, Google Cloud APIs, Twilio SDK)
- **Workflow**: Configured to run on port 5000

## Project Architecture

### Key Components
1. **Flask Web Server** - Handles Twilio webhooks and API endpoints
2. **Google Cloud Integration**:
   - Speech-to-Text API for voice recognition
   - Text-to-Speech API for voice synthesis
   - Translation API for Hindi ↔ English translation
3. **Twilio Integration** - Manages phone calls and voice communication

### Main Endpoints
- `/` - Home endpoint with service info
- `/health` - Health check endpoint
- `/twilio-webhook` - Main Twilio webhook for incoming calls
- `/test-call-forwarding` - Test configuration endpoint
- `/gather-webhook` - Handles speech input from Twilio
- `/translate-text` - API endpoint for text translation

## Required Environment Variables

### Essential Configuration
- `FORWARD_TO_NUMBER` - Phone number to forward calls to (e.g., "+1234567890")
- `TWILIO_ACCOUNT_SID` - Your Twilio Account SID
- `TWILIO_AUTH_TOKEN` - Your Twilio Auth Token
- `REPLIT_DEV_DOMAIN` - Auto-set by Replit (your app's public URL)

### Optional Configuration
- `PORT` - Server port (defaults to 5000)
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to Google Cloud credentials JSON file (defaults to 'google-credentials.json')

## Setup Instructions

### 1. Environment Variables
Set the following secrets in Replit:
- `FORWARD_TO_NUMBER` - Your phone number to forward calls to
- `TWILIO_ACCOUNT_SID` - From Twilio Console
- `TWILIO_AUTH_TOKEN` - From Twilio Console

### 2. Google Cloud Credentials
1. Create a Google Cloud project
2. Enable: Speech-to-Text, Text-to-Speech, and Translation APIs
3. Create a service account and download the JSON key
4. Upload the key as `google-credentials.json` to this Repl

### 3. Twilio Configuration
1. Get your Replit URL (shown in the webview)
2. In Twilio Console, configure your phone number:
   - Webhook URL: `https://YOUR-REPLIT-URL/twilio-webhook`
   - Method: POST

## Features
- 🔄 Bidirectional Translation: Hindi ↔ English real-time translation
- 🎤 Voice Activity Detection: Automatic speech detection
- 🌐 Language Detection: Auto-detect Hindi/English speech
- ⚡ Low Latency: Optimized for real-time conversation
- 📞 Twilio Integration: Works with any Twilio phone number
- 🔊 High Quality Audio: Google Cloud TTS with natural voices

## Recent Changes
- **Oct 27, 2025**: Configured for Replit environment
  - Updated port to 5000 (Replit standard)
  - Replaced hardcoded phone numbers with environment variables
  - Changed domain references from Railway to Replit
  - Added security improvements for sensitive data
  - Installed all Python dependencies
  - Configured workflow for automatic server start

## File Structure
- `improved_hindi_translator.py` - Main application (recommended)
- `requirements.txt` - Python dependencies
- Multiple other translator scripts (legacy/alternatives)
- `README.md` - Original project documentation
- Audio test files (`.wav`, `.mp3`)

## Security Notes
- Never commit `google-credentials.json` to version control
- Use Replit Secrets for sensitive environment variables
- Phone numbers should be configured via environment variables only

## Usage
1. Start the server (automatically runs on Replit)
2. Configure Twilio webhook to point to your Replit URL
3. Call your Twilio number
4. Speak in English or Hindi
5. Translation happens in real-time

## Troubleshooting
- Check workflow console logs for errors
- Verify all environment variables are set
- Ensure Google Cloud credentials file exists
- Verify Twilio webhook URL is correctly configured
- Test the `/health` endpoint to check service status
