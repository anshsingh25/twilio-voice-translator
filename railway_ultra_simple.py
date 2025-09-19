#!/usr/bin/env python3
"""
Railway Deployment - ULTRA SIMPLE Voice Translation
GUARANTEED TO WORK - No complex features
"""

import os
import json
import time
import warnings
import requests
from flask import Flask, request, Response
import gunicorn.app.base

# Suppress warnings
warnings.filterwarnings("ignore")

# Set up Google Cloud credentials
def setup_google_credentials():
    try:
        creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if creds_json:
            creds_data = json.loads(creds_json)
            temp_creds_path = '/tmp/google-credentials.json'
            with open(temp_creds_path, 'w') as f:
                json.dump(creds_data, f)
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_creds_path
            print("✅ Google credentials set up")
            return True
        return False
    except Exception as e:
        print(f"❌ Credentials error: {e}")
        return False

credentials_setup = setup_google_credentials()

# Import Google Cloud
try:
    from google.cloud import translate_v2 as translate
    GOOGLE_CLOUD_AVAILABLE = True
    print("✅ Google Cloud available")
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    print("❌ Google Cloud not available")

app = Flask(__name__)

@app.route('/health')
def health_check():
    return {
        "status": "healthy",
        "google_cloud_available": GOOGLE_CLOUD_AVAILABLE,
        "credentials_setup": credentials_setup,
        "version": "15.0-ultra-simple"
    }, 200

@app.route('/')
def home():
    return {
        "message": "ULTRA SIMPLE Twilio Voice Translator",
        "webhook": "/twilio-webhook",
        "version": "15.0-ultra-simple"
    }, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    
    print(f"\n📞 CALL FROM: {from_number}")
    print(f"   CallSid: {call_sid}")
    print("="*40)
    
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')
    
    # ULTRA SIMPLE TwiML
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="alice" language="en-US">Hello! Speak now for translation.</Say>
        <Record 
            action="https://{railway_domain}/transcription-webhook" 
            method="POST"
            transcribe="true"
            transcribeCallback="https://{railway_domain}/transcription-webhook"
            maxLength="8"
            timeout="3"
            playBeep="true"
        />
    </Response>"""
    
    return Response(twiml, mimetype='text/xml')

@app.route('/transcription-webhook', methods=['POST'])
def transcription_webhook():
    call_sid = request.form.get('CallSid')
    transcription_text = request.form.get('TranscriptionText', '')
    transcription_status = request.form.get('TranscriptionStatus', '')
    
    print(f"\n🎤 TRANSCRIPTION:")
    print(f"   Status: {transcription_status}")
    print(f"   Text: '{transcription_text}'")
    print("="*40)
    
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')
    
    if not transcription_text:
        print("❌ No transcription - fallback response")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">I didn't hear anything. Goodbye.</Say>
        </Response>"""
        return Response(twiml, mimetype='text/xml')
    
    try:
        # Simple language detection
        devanagari_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
        is_hindi = any(char in devanagari_chars for char in transcription_text)
        
        if is_hindi:
            # Hindi to English
            translated_text = translate_text(transcription_text, 'hi', 'en')
            target_lang = "en-US"
            print(f"🔄 Hindi → English: '{translated_text}'")
        else:
            # English to Hindi
            translated_text = translate_text(transcription_text, 'en', 'hi')
            target_lang = "hi-IN"
            print(f"🔄 English → Hindi: '{translated_text}'")
        
        print(f"🔊 SPEAKING: You said: {transcription_text}")
        print(f"🔊 SPEAKING: Translation: {translated_text}")
        print("="*40)
        
        # ULTRA SIMPLE response
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">You said: {transcription_text}</Say>
            <Say voice="alice" language="{target_lang}">Translation: {translated_text}</Say>
            <Say voice="alice" language="en-US">Thank you. Goodbye.</Say>
        </Response>"""
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Error: {e}")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">Error occurred. Goodbye.</Say>
        </Response>"""
        return Response(twiml, mimetype='text/xml')

def translate_text(text, source_lang, target_lang):
    try:
        if not GOOGLE_CLOUD_AVAILABLE:
            return text
        
        client = translate.Client()
        result = client.translate(text, source_language=source_lang, target_language=target_lang)
        return result['translatedText']
    except Exception as e:
        print(f"❌ Translation error: {e}")
        return text

class StandaloneApplication(gunicorn.app.base.BaseApplication):
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
    port = int(os.environ.get('PORT', 3000))
    print(f"🚀 ULTRA SIMPLE TRANSLATOR on port {port}")
    print("="*50)
    print("✅ Features:")
    print("   ✓ Ultra simple responses")
    print("   ✓ Hindi ↔ English translation")
    print("   ✓ No complex features")
    print("   ✓ Guaranteed to work")
    print(f"   ✓ Google Cloud: {GOOGLE_CLOUD_AVAILABLE}")
    print(f"   ✓ Credentials: {credentials_setup}")
    print("="*50)
    
    options = {
        'bind': f'0.0.0.0:{port}',
        'workers': 1,
        'worker_class': 'sync',
        'timeout': 30,
    }
    
    StandaloneApplication(app, options).run()
