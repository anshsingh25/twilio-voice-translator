#!/usr/bin/env python3
"""
Railway Deployment - Final Working Voice Translation
SIMPLIFIED: Shorter responses, better audio
"""

import os
import json
import time
import warnings
import requests
from flask import Flask, request, Response
import gunicorn.app.base

# Suppress pkg_resources deprecation warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
warnings.filterwarnings("ignore", category=UserWarning, module="google.cloud.translate_v2")

# Set up Google Cloud credentials properly
def setup_google_credentials():
    """Set up Google Cloud credentials from environment variable"""
    try:
        # Check if GOOGLE_CREDENTIALS_JSON is set (Railway environment variable)
        creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if creds_json:
            try:
                # Parse the JSON to validate it
                creds_data = json.loads(creds_json)
                # Write to a temporary file
                temp_creds_path = '/tmp/google-credentials.json'
                with open(temp_creds_path, 'w') as f:
                    json.dump(creds_data, f)
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_creds_path
                print(f"✅ Using credentials from environment variable, saved to: {temp_creds_path}")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in GOOGLE_CREDENTIALS_JSON: {e}")
                return False
        
        print("❌ No Google Cloud credentials found")
        return False
        
    except Exception as e:
        print(f"❌ Error setting up Google Cloud credentials: {e}")
        return False

# Set up credentials
credentials_setup = setup_google_credentials()

# Try to import Google Cloud libraries with error handling
try:
    from google.cloud import speech
    from google.cloud import texttospeech
    from google.cloud import translate_v2 as translate
    GOOGLE_CLOUD_AVAILABLE = True
    print("✅ Google Cloud libraries imported successfully")
except ImportError as e:
    print(f"❌ Google Cloud libraries not available: {e}")
    GOOGLE_CLOUD_AVAILABLE = False

# Flask app for HTTP webhooks
app = Flask(__name__)

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    status = {
        "status": "healthy", 
        "service": "twilio-voice-translator",
        "google_cloud_available": GOOGLE_CLOUD_AVAILABLE,
        "credentials_setup": credentials_setup,
        "port": os.environ.get('PORT', 'not_set'),
        "timestamp": time.time(),
        "version": "14.0-final-working"
    }
    return status, 200

@app.route('/')
def home():
    """Home endpoint"""
    return {
        "message": "Twilio Voice Translator is running!",
        "health_check": "/health",
        "webhook": "/twilio-webhook",
        "transcription_webhook": "/transcription-webhook",
        "google_cloud_available": GOOGLE_CLOUD_AVAILABLE,
        "credentials_setup": credentials_setup,
        "version": "14.0-final-working",
        "features": [
            "Final working translation",
            "Simplified responses",
            "Hindi ↔ English translation",
            "Google Cloud Translation"
        ]
    }, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    """Handle incoming Twilio calls"""
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    to_number = request.form.get('To')
    
    print(f"\n📞 INCOMING CALL:")
    print(f"   From: {from_number}")
    print(f"   To: {to_number}")
    print(f"   CallSid: {call_sid}")
    print("="*50)
    
    # Get the Railway domain from environment variable
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')
    if railway_domain == 'your-railway-app.railway.app':
        # Fallback to Railway's default domain format
        railway_domain = os.environ.get('RAILWAY_STATIC_URL', 'web-production-6577e.up.railway.app')
    
    # SIMPLIFIED TwiML response
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="alice" language="en-US">Hello! I will translate your voice. Please speak now.</Say>
        <Record 
            action="https://{railway_domain}/transcription-webhook" 
            method="POST"
            transcribe="true"
            transcribeCallback="https://{railway_domain}/transcription-webhook"
            maxLength="10"
            timeout="5"
            playBeep="true"
            finishOnKey="#"
        />
    </Response>"""
    
    return Response(twiml, mimetype='text/xml')

@app.route('/transcription-webhook', methods=['POST'])
def transcription_webhook():
    """Handle transcription results and provide translation"""
    call_sid = request.form.get('CallSid')
    transcription_text = request.form.get('TranscriptionText', '')
    transcription_status = request.form.get('TranscriptionStatus', '')
    recording_url = request.form.get('RecordingUrl', '')
    recording_duration = request.form.get('RecordingDuration', '0')
    
    print(f"\n🎤 TRANSCRIPTION WEBHOOK CALLED:")
    print(f"   CallSid: {call_sid}")
    print(f"   Status: {transcription_status}")
    print(f"   Text: '{transcription_text}'")
    print(f"   Duration: {recording_duration} seconds")
    print(f"   Recording URL: {recording_url}")
    print("="*50)
    
    # Get the Railway domain
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')
    
    if not transcription_text:
        # Fallback response if no transcription
        print("❌ No transcription available, providing fallback response")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">I couldn't understand. Please speak again.</Say>
            <Record 
                action="https://{railway_domain}/transcription-webhook" 
                method="POST"
                transcribe="true"
                transcribeCallback="https://{railway_domain}/transcription-webhook"
                maxLength="10"
                timeout="5"
                playBeep="true"
                finishOnKey="#"
            />
        </Response>"""
        return Response(twiml, mimetype='text/xml')
    
    try:
        # Detect language and translate
        detected_language = detect_language(transcription_text)
        print(f"🌍 Detected language: {detected_language}")
        
        if detected_language == "hi":
            # Hindi to English
            translated_text = translate_text(transcription_text, 'hi', 'en')
            target_language = "en-US"
            print(f"🔄 TRANSLATION:")
            print(f"   Hindi: '{transcription_text}'")
            print(f"   English: '{translated_text}'")
        else:
            # English to Hindi
            translated_text = translate_text(transcription_text, 'en', 'hi')
            target_language = "hi-IN"
            print(f"🔄 TRANSLATION:")
            print(f"   English: '{transcription_text}'")
            print(f"   Hindi: '{translated_text}'")
        
        print(f"🔊 SPEAKING RESPONSE:")
        print(f"   'You said: {transcription_text}'")
        print(f"   'Translation: {translated_text}'")
        print("="*50)
        
        # SIMPLIFIED TwiML response - shorter and clearer
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">You said: {transcription_text}</Say>
            <Pause length="1"/>
            <Say voice="alice" language="{target_language}">Translation: {translated_text}</Say>
            <Pause length="1"/>
            <Say voice="alice" language="en-US">Say something else or hang up.</Say>
            <Record 
                action="https://{railway_domain}/transcription-webhook" 
                method="POST"
                transcribe="true"
                transcribeCallback="https://{railway_domain}/transcription-webhook"
                maxLength="10"
                timeout="5"
                playBeep="true"
                finishOnKey="#"
            />
        </Response>"""
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Translation error: {e}")
        # Error response
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">Translation error. Please try again.</Say>
            <Record 
                action="https://{railway_domain}/transcription-webhook" 
                method="POST"
                transcribe="true"
                transcribeCallback="https://{railway_domain}/transcription-webhook"
                maxLength="10"
                timeout="5"
                playBeep="true"
                finishOnKey="#"
            />
        </Response>"""
        return Response(twiml, mimetype='text/xml')

def detect_language(text):
    """Simple language detection"""
    # Simple heuristic: if text contains Devanagari characters, it's Hindi
    devanagari_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
    if any(char in devanagari_chars for char in text):
        return "hi"
    return "en"

def translate_text(text, source_lang, target_lang):
    """Translate text using Google Cloud Translation"""
    try:
        print(f"🔄 Calling Google Translate API...")
        print(f"   Source: {source_lang}")
        print(f"   Target: {target_lang}")
        print(f"   Text: '{text}'")
        
        # Initialize the translate client with proper credentials
        client = translate.Client()
        result = client.translate(text, source_language=source_lang, target_language=target_lang)
        
        translated_text = result['translatedText']
        print(f"✅ Translation successful: '{translated_text}'")
        return translated_text
        
    except Exception as e:
        print(f"❌ Translation error: {e}")
        print(f"   Returning original text: '{text}'")
        # Return original text if translation fails
        return text

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    """Gunicorn application for Railway deployment"""
    
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()
    
    def load_config(self):
        config = {key: value for key, value in self.options.items()
                 if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)
    
    def load(self):
        return self.application

if __name__ == "__main__":
    try:
        # Get port from Railway environment variable
        port = int(os.environ.get('PORT', 3000))
        print(f"🚀 Starting Railway deployment on port {port}")
        print("="*70)
        print("🎯 RAILWAY TWILIO VOICE TRANSLATOR - FINAL WORKING")
        print("="*70)
        print("✅ Features:")
        print("   ✓ Final working translation")
        print("   ✓ Simplified responses")
        print("   ✓ Hindi ↔ English translation")
        print("   ✓ Google Cloud Translation")
        print("   ✓ Railway cloud deployment")
        print("   ✓ Better error handling")
        print("   ✓ Shorter, clearer audio responses")
        print(f"   ✓ Google Cloud available: {GOOGLE_CLOUD_AVAILABLE}")
        print(f"   ✓ Credentials setup: {credentials_setup}")
        print(f"   ✓ Port: {port}")
        print("="*70)
        
        if not GOOGLE_CLOUD_AVAILABLE:
            print("⚠️  WARNING: Google Cloud libraries not available!")
            print("   Please check your GOOGLE_APPLICATION_CREDENTIALS environment variable")
        
        if not credentials_setup:
            print("⚠️  WARNING: Google Cloud credentials not properly set up!")
            print("   Please check your GOOGLE_CREDENTIALS_JSON environment variable")
        
        # Start Flask app with Gunicorn
        options = {
            'bind': f'0.0.0.0:{port}',
            'workers': 1,
            'worker_class': 'sync',
            'worker_connections': 1000,
            'timeout': 30,
            'keepalive': 2,
            'max_requests': 1000,
            'max_requests_jitter': 100,
            'preload_app': True,
        }
        
        StandaloneApplication(app, options).run()
        
    except KeyboardInterrupt:
        print("🛑 Server stopped by user.")
    except Exception as e:
        print(f"❌ Server startup error: {e}")
        import traceback
        traceback.print_exc()
