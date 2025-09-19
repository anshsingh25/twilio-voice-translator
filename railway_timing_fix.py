#!/usr/bin/env python3
"""
Railway Deployment - TIMING FIX Voice Translation
FIXED: First call transcription issue
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
        "version": "16.0-timing-fix"
    }, 200

@app.route('/')
def home():
    return {
        "message": "TIMING FIX Twilio Voice Translator",
        "webhook": "/twilio-webhook",
        "version": "16.0-timing-fix"
    }, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    
    print(f"\n📞 CALL FROM: {from_number}")
    print(f"   CallSid: {call_sid}")
    print("="*40)
    
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')
    
    # FIXED: Longer timeout and better recording settings
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="alice" language="en-US">Hello! Please speak clearly for translation.</Say>
        <Record 
            action="https://{railway_domain}/transcription-webhook" 
            method="POST"
            transcribe="true"
            transcribeCallback="https://{railway_domain}/transcription-webhook"
            maxLength="10"
            timeout="8"
            playBeep="true"
            finishOnKey="#"
            recordingStatusCallback="https://{railway_domain}/recording-status"
        />
        <Say voice="alice" language="en-US">Processing your speech. Please wait.</Say>
    </Response>"""
    
    return Response(twiml, mimetype='text/xml')

@app.route('/transcription-webhook', methods=['POST'])
def transcription_webhook():
    call_sid = request.form.get('CallSid')
    transcription_text = request.form.get('TranscriptionText', '')
    transcription_status = request.form.get('TranscriptionStatus', '')
    recording_url = request.form.get('RecordingUrl', '')
    
    print(f"\n🎤 TRANSCRIPTION WEBHOOK:")
    print(f"   CallSid: {call_sid}")
    print(f"   Status: {transcription_status}")
    print(f"   Text: '{transcription_text}'")
    print(f"   Recording URL: {recording_url}")
    print("="*40)
    
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')
    
    # FIXED: Handle different transcription statuses
    if transcription_status == 'in-progress':
        print("⏳ Transcription in progress - waiting...")
        # Return a waiting response
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">Processing your speech. Please wait.</Say>
            <Pause length="3"/>
            <Say voice="alice" language="en-US">Still processing. Please wait.</Say>
        </Response>"""
        return Response(twiml, mimetype='text/xml')
    
    elif transcription_status == 'failed':
        print("❌ Transcription failed")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">Sorry, I couldn't understand. Please try again.</Say>
            <Record 
                action="https://{railway_domain}/transcription-webhook" 
                method="POST"
                transcribe="true"
                transcribeCallback="https://{railway_domain}/transcription-webhook"
                maxLength="10"
                timeout="8"
                playBeep="true"
                finishOnKey="#"
            />
        </Response>"""
        return Response(twiml, mimetype='text/xml')
    
    elif not transcription_text or transcription_status != 'completed':
        print("❌ No transcription text or not completed")
        # Try to process recording directly if available
        if recording_url and GOOGLE_CLOUD_AVAILABLE:
            print("🔄 Attempting direct recording processing...")
            try:
                direct_transcription = process_recording_directly(recording_url)
                if direct_transcription:
                    transcription_text = direct_transcription
                    print(f"✅ Direct processing result: '{transcription_text}'")
                else:
                    print("❌ Direct processing failed")
            except Exception as e:
                print(f"❌ Direct processing error: {e}")
        
        if not transcription_text:
            print("❌ No transcription available - fallback response")
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say voice="alice" language="en-US">I didn't hear anything clearly. Please try again.</Say>
                <Record 
                    action="https://{railway_domain}/transcription-webhook" 
                    method="POST"
                    transcribe="true"
                    transcribeCallback="https://{railway_domain}/transcription-webhook"
                    maxLength="10"
                    timeout="8"
                    playBeep="true"
                    finishOnKey="#"
                />
            </Response>"""
            return Response(twiml, mimetype='text/xml')
    
    # Process transcription
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
        
        # Success response
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">You said: {transcription_text}</Say>
            <Pause length="1"/>
            <Say voice="alice" language="{target_lang}">Translation: {translated_text}</Say>
            <Pause length="1"/>
            <Say voice="alice" language="en-US">Thank you. Goodbye.</Say>
        </Response>"""
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Translation error: {e}")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">Translation error. Please try again.</Say>
            <Record 
                action="https://{railway_domain}/transcription-webhook" 
                method="POST"
                transcribe="true"
                transcribeCallback="https://{railway_domain}/transcription-webhook"
                maxLength="10"
                timeout="8"
                playBeep="true"
                finishOnKey="#"
            />
        </Response>"""
        return Response(twiml, mimetype='text/xml')

@app.route('/recording-status', methods=['POST'])
def recording_status():
    call_sid = request.form.get('CallSid')
    recording_status = request.form.get('RecordingStatus', '')
    recording_url = request.form.get('RecordingUrl', '')
    
    print(f"\n📹 RECORDING STATUS:")
    print(f"   CallSid: {call_sid}")
    print(f"   Status: {recording_status}")
    print(f"   URL: {recording_url}")
    print("="*40)
    
    return Response('OK', mimetype='text/plain')

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

def process_recording_directly(recording_url):
    """Process recording directly using Google Cloud Speech-to-Text"""
    try:
        print(f"🔄 Downloading recording from: {recording_url}")
        # Download the recording
        response = requests.get(recording_url, timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to download recording: {response.status_code}")
            return ""
        
        audio_content = response.content
        print(f"✅ Downloaded {len(audio_content)} bytes of audio")
        
        # Initialize Speech-to-Text client
        from google.cloud import speech
        client = speech.SpeechClient()
        
        # Configure recognition
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
            sample_rate_hertz=8000,
            language_code="hi-IN",
            alternative_language_codes=["en-US"],
            enable_automatic_punctuation=True,
            model="latest_long"
        )
        
        audio = speech.RecognitionAudio(content=audio_content)
        
        # Perform recognition
        print("🔄 Performing speech recognition...")
        response = client.recognize(config=config, audio=audio)
        
        if response.results:
            result = response.results[0]
            if result.is_final:
                transcript = result.alternatives[0].transcript
                confidence = result.alternatives[0].confidence
                print(f"✅ Direct processing confidence: {confidence}")
                if confidence > 0.5:
                    return transcript
        
        return ""
        
    except Exception as e:
        print(f"❌ Direct processing error: {e}")
        return ""

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
    print(f"🚀 TIMING FIX TRANSLATOR on port {port}")
    print("="*50)
    print("✅ Features:")
    print("   ✓ Fixed first call transcription issue")
    print("   ✓ Better timing handling")
    print("   ✓ Hindi ↔ English translation")
    print("   ✓ Direct recording processing fallback")
    print("   ✓ Recording status monitoring")
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
