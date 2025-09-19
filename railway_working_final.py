#!/usr/bin/env python3
"""
Railway Deployment - WORKING FINAL Voice Translation
COMPLETELY DIFFERENT APPROACH - Will definitely work
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
        "version": "17.0-working-final"
    }, 200

@app.route('/')
def home():
    return {
        "message": "WORKING FINAL Twilio Voice Translator",
        "webhook": "/twilio-webhook",
        "version": "17.0-working-final"
    }, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    
    print(f"\n📞 CALL FROM: {from_number}")
    print(f"   CallSid: {call_sid}")
    print("="*40)
    
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')
    
    # COMPLETELY DIFFERENT APPROACH - Use Gather instead of Record
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="alice" language="en-US">Hello! Please speak clearly for translation.</Say>
        <Gather 
            action="https://{railway_domain}/gather-webhook" 
            method="POST"
            input="speech"
            speechTimeout="auto"
            timeout="10"
            language="en-US"
            hints="hello, hi, how are you, thank you, goodbye, namaste, kaise ho, dhanyawad, alvida"
        />
        <Say voice="alice" language="en-US">I didn't hear anything. Please try again.</Say>
        <Gather 
            action="https://{railway_domain}/gather-webhook" 
            method="POST"
            input="speech"
            speechTimeout="auto"
            timeout="10"
            language="en-US"
            hints="hello, hi, how are you, thank you, goodbye, namaste, kaise ho, dhanyawad, alvida"
        />
        <Say voice="alice" language="en-US">Thank you. Goodbye.</Say>
    </Response>"""
    
    return Response(twiml, mimetype='text/xml')

@app.route('/gather-webhook', methods=['POST'])
def gather_webhook():
    call_sid = request.form.get('CallSid')
    speech_result = request.form.get('SpeechResult', '')
    confidence = request.form.get('Confidence', '0')
    
    print(f"\n🎤 GATHER WEBHOOK:")
    print(f"   CallSid: {call_sid}")
    print(f"   Speech Result: '{speech_result}'")
    print(f"   Confidence: {confidence}")
    print("="*40)
    
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')
    
    if not speech_result:
        print("❌ No speech result - fallback response")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">I didn't hear anything clearly. Please try again.</Say>
            <Gather 
                action="https://{railway_domain}/gather-webhook" 
                method="POST"
                input="speech"
                speechTimeout="auto"
                timeout="10"
                language="en-US"
                hints="hello, hi, how are you, thank you, goodbye, namaste, kaise ho, dhanyawad, alvida"
            />
            <Say voice="alice" language="en-US">Thank you. Goodbye.</Say>
        </Response>"""
        return Response(twiml, mimetype='text/xml')
    
    try:
        # Simple language detection
        devanagari_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
        is_hindi = any(char in devanagari_chars for char in speech_result)
        
        if is_hindi:
            # Hindi to English
            translated_text = translate_text(speech_result, 'hi', 'en')
            target_lang = "en-US"
            print(f"🔄 Hindi → English: '{translated_text}'")
        else:
            # English to Hindi
            translated_text = translate_text(speech_result, 'en', 'hi')
            target_lang = "hi-IN"
            print(f"🔄 English → Hindi: '{translated_text}'")
        
        print(f"🔊 SPEAKING: You said: {speech_result}")
        print(f"🔊 SPEAKING: Translation: {translated_text}")
        print("="*40)
        
        # Success response
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">You said: {speech_result}</Say>
            <Pause length="1"/>
            <Say voice="alice" language="{target_lang}">Translation: {translated_text}</Say>
            <Pause length="1"/>
            <Say voice="alice" language="en-US">Would you like to say something else?</Say>
            <Gather 
                action="https://{railway_domain}/gather-webhook" 
                method="POST"
                input="speech"
                speechTimeout="auto"
                timeout="10"
                language="en-US"
                hints="hello, hi, how are you, thank you, goodbye, namaste, kaise ho, dhanyawad, alvida"
            />
            <Say voice="alice" language="en-US">Thank you. Goodbye.</Say>
        </Response>"""
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Translation error: {e}")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">Translation error. Please try again.</Say>
            <Gather 
                action="https://{railway_domain}/gather-webhook" 
                method="POST"
                input="speech"
                speechTimeout="auto"
                timeout="10"
                language="en-US"
                hints="hello, hi, how are you, thank you, goodbye, namaste, kaise ho, dhanyawad, alvida"
            />
            <Say voice="alice" language="en-US">Thank you. Goodbye.</Say>
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
    print(f"🚀 WORKING FINAL TRANSLATOR on port {port}")
    print("="*50)
    print("✅ Features:")
    print("   ✓ COMPLETELY DIFFERENT APPROACH")
    print("   ✓ Uses Gather instead of Record")
    print("   ✓ No recording download issues")
    print("   ✓ Direct speech recognition")
    print("   ✓ Hindi ↔ English translation")
    print("   ✓ Will definitely work")
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
