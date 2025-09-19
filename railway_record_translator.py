#!/usr/bin/env python3
"""
Railway Deployment - Record-based Voice Translation
Uses Twilio Record verb for voice translation (more Railway-compatible)
"""

import os
import json
import time
import warnings
from flask import Flask, request, Response
import gunicorn.app.base

# Suppress pkg_resources deprecation warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
warnings.filterwarnings("ignore", category=UserWarning, module="google.cloud.translate_v2")

# Try to import Google Cloud libraries with error handling
try:
    from google.cloud import speech
    from google.cloud import texttospeech
    from google.cloud import translate_v2 as translate
    GOOGLE_CLOUD_AVAILABLE = True
    print("Google Cloud libraries imported successfully")
except ImportError as e:
    print(f"Google Cloud libraries not available: {e}")
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
        "port": os.environ.get('PORT', 'not_set'),
        "timestamp": time.time(),
        "version": "6.0-record-translation"
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
        "version": "6.0-record-translation",
        "features": [
            "Voice recording and transcription",
            "Hindi ↔ English translation",
            "Google Cloud Speech-to-Text",
            "Google Cloud Text-to-Speech",
            "Google Cloud Translation"
        ]
    }, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    """Handle incoming Twilio calls"""
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    to_number = request.form.get('To')
    
    print(f"Incoming call from {from_number} to {to_number} (CallSid: {call_sid})")
    
    # Get the Railway domain from environment variable
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')
    if railway_domain == 'your-railway-app.railway.app':
        # Fallback to Railway's default domain format
        railway_domain = os.environ.get('RAILWAY_STATIC_URL', 'web-production-6577e.up.railway.app')
    
    # TwiML response with recording
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say language="hi-IN">नमस्ते! मैं आपकी आवाज़ का अनुवाद करूंगा।</Say>
        <Say language="en-US">Hello! I will translate your voice.</Say>
        <Say language="hi-IN">अब आप बोल सकते हैं।</Say>
        <Say language="en-US">You can start speaking now.</Say>
        <Record 
            action="https://{railway_domain}/transcription-webhook" 
            method="POST"
            transcribe="true"
            transcribeCallback="https://{railway_domain}/transcription-webhook"
            maxLength="10"
            timeout="5"
            playBeep="false"
            finishOnKey="#"
        />
        <Say language="hi-IN">धन्यवाद! आपका अनुवाद तैयार है।</Say>
        <Say language="en-US">Thank you! Your translation is ready.</Say>
    </Response>"""
    
    return Response(twiml, mimetype='text/xml')

@app.route('/transcription-webhook', methods=['POST'])
def transcription_webhook():
    """Handle transcription results and provide translation"""
    call_sid = request.form.get('CallSid')
    transcription_text = request.form.get('TranscriptionText', '')
    recording_url = request.form.get('RecordingUrl', '')
    
    print(f"Transcription for call {call_sid}: {transcription_text}")
    
    if not transcription_text or not GOOGLE_CLOUD_AVAILABLE:
        # Fallback response if no transcription or Google Cloud not available
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say language="en-US">Sorry, I couldn't process your message. Please try again.</Say>
        </Response>"""
        return Response(twiml, mimetype='text/xml')
    
    try:
        # Detect language and translate
        detected_language = detect_language(transcription_text)
        
        if detected_language == "hi":
            # Hindi to English
            translated_text = translate_text(transcription_text, 'hi', 'en')
            target_language = "en-US"
            print(f"Hindi: {transcription_text} → English: {translated_text}")
        else:
            # English to Hindi
            translated_text = translate_text(transcription_text, 'en', 'hi')
            target_language = "hi-IN"
            print(f"English: {transcription_text} → Hindi: {translated_text}")
        
        # Create TwiML response with translation
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say language="en-US">You said: {transcription_text}</Say>
            <Say language="{target_language}">Translation: {translated_text}</Say>
            <Say language="hi-IN">क्या आप कुछ और कहना चाहते हैं?</Say>
            <Say language="en-US">Would you like to say something else?</Say>
            <Record 
                action="https://{os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')}/transcription-webhook" 
                method="POST"
                transcribe="true"
                transcribeCallback="https://{os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')}/transcription-webhook"
                maxLength="10"
                timeout="5"
                playBeep="false"
                finishOnKey="#"
            />
        </Response>"""
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"Translation error: {e}")
        # Error response
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say language="en-US">Sorry, there was an error processing your message. Please try again.</Say>
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
        client = translate.Client()
        result = client.translate(text, source_language=source_lang, target_language=target_lang)
        return result['translatedText']
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text if translation fails

@app.route('/call-status', methods=['POST'])
def call_status():
    """Handle call status updates"""
    call_sid = request.form.get('CallSid')
    call_status = request.form.get('CallStatus')
    
    print(f"Call {call_sid} status: {call_status}")
    
    return Response('OK', mimetype='text/plain')

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
        print(f"Starting Railway deployment on port {port}")
        print("="*70)
        print("RAILWAY TWILIO VOICE TRANSLATOR - RECORD TRANSLATION")
        print("="*70)
        print("Features:")
        print("✓ Voice recording and transcription")
        print("✓ Hindi ↔ English translation")
        print("✓ Google Cloud Speech-to-Text")
        print("✓ Google Cloud Text-to-Speech")
        print("✓ Google Cloud Translation")
        print("✓ Railway cloud deployment")
        print("✓ No WebSocket dependencies")
        print(f"✓ Google Cloud available: {GOOGLE_CLOUD_AVAILABLE}")
        print(f"✓ Port: {port}")
        print("="*70)
        
        if not GOOGLE_CLOUD_AVAILABLE:
            print("WARNING: Google Cloud libraries not available!")
            print("Please check your GOOGLE_APPLICATION_CREDENTIALS environment variable")
        
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
        print("Server stopped by user.")
    except Exception as e:
        print(f"Server startup error: {e}")
        import traceback
        traceback.print_exc()
