#!/usr/bin/env python3
"""
Railway Deployment - Fixed Credentials Voice Translation
Properly handles Google Cloud credentials
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
        # Check if GOOGLE_APPLICATION_CREDENTIALS is set
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if creds_path and os.path.exists(creds_path):
            print(f"Using credentials from file: {creds_path}")
            return True
        
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
                print(f"Using credentials from environment variable, saved to: {temp_creds_path}")
                return True
            except json.JSONDecodeError as e:
                print(f"Invalid JSON in GOOGLE_CREDENTIALS_JSON: {e}")
                return False
        
        # Check if we have the credentials file in the current directory
        local_creds_path = 'google-credentials.json'
        if os.path.exists(local_creds_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.abspath(local_creds_path)
            print(f"Using local credentials file: {os.path.abspath(local_creds_path)}")
            return True
        
        print("No Google Cloud credentials found")
        return False
        
    except Exception as e:
        print(f"Error setting up Google Cloud credentials: {e}")
        return False

# Set up credentials
credentials_setup = setup_google_credentials()

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
        "credentials_setup": credentials_setup,
        "port": os.environ.get('PORT', 'not_set'),
        "timestamp": time.time(),
        "version": "12.0-fixed-credentials"
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
        "version": "12.0-fixed-credentials",
        "features": [
            "Fixed Google Cloud credentials handling",
            "Hindi ↔ English translation",
            "Google Cloud Speech-to-Text",
            "Google Cloud Translation",
            "Proper language voice selection"
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
    
    # TwiML response with improved recording
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="alice" language="hi-IN">नमस्ते! मैं आपकी आवाज़ का अनुवाद करूंगा।</Say>
        <Say voice="alice" language="en-US">Hello! I will translate your voice.</Say>
        <Say voice="alice" language="hi-IN">अब आप बोल सकते हैं।</Say>
        <Say voice="alice" language="en-US">You can start speaking now.</Say>
        <Record 
            action="https://{railway_domain}/transcription-webhook" 
            method="POST"
            transcribe="true"
            transcribeCallback="https://{railway_domain}/transcription-webhook"
            maxLength="15"
            timeout="10"
            playBeep="true"
            finishOnKey="#"
            recordingStatusCallback="https://{railway_domain}/recording-status"
        />
        <Say voice="alice" language="hi-IN">धन्यवाद! आपका अनुवाद तैयार है।</Say>
        <Say voice="alice" language="en-US">Thank you! Your translation is ready.</Say>
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
    
    print(f"Transcription webhook called for call {call_sid}")
    print(f"Transcription Status: {transcription_status}")
    print(f"Transcription Text: {transcription_text}")
    print(f"Recording URL: {recording_url}")
    print(f"Recording Duration: {recording_duration}")
    
    # Get the Railway domain
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')
    
    # If no transcription text, try to process the recording directly
    if not transcription_text and recording_url and GOOGLE_CLOUD_AVAILABLE:
        try:
            print("Attempting direct recording processing...")
            transcription_text = process_recording_directly(recording_url)
            print(f"Direct processing result: {transcription_text}")
        except Exception as e:
            print(f"Direct processing failed: {e}")
            transcription_text = ""
    
    if not transcription_text:
        # Fallback response if no transcription
        print("No transcription available, providing fallback response")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="hi-IN">मुझे आपकी आवाज़ समझ नहीं आई।</Say>
            <Say voice="alice" language="en-US">I couldn't understand your voice.</Say>
            <Say voice="alice" language="hi-IN">कृपया फिर से बोलें।</Say>
            <Say voice="alice" language="en-US">Please speak again.</Say>
            <Record 
                action="https://{railway_domain}/transcription-webhook" 
                method="POST"
                transcribe="true"
                transcribeCallback="https://{railway_domain}/transcription-webhook"
                maxLength="15"
                timeout="10"
                playBeep="true"
                finishOnKey="#"
            />
        </Response>"""
        return Response(twiml, mimetype='text/xml')
    
    try:
        # Detect language and translate
        detected_language = detect_language(transcription_text)
        print(f"Detected language: {detected_language}")
        
        if detected_language == "hi":
            # Hindi to English
            translated_text = translate_text(transcription_text, 'hi', 'en')
            target_language = "en-US"
            target_voice = "alice"
            print(f"Hindi: {transcription_text} → English: {translated_text}")
        else:
            # English to Hindi
            translated_text = translate_text(transcription_text, 'en', 'hi')
            target_language = "hi-IN"
            target_voice = "alice"
            print(f"English: {transcription_text} → Hindi: {translated_text}")
        
        # Create TwiML response with proper voice and language
        print("Creating TwiML response with translation")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">You said: {transcription_text}</Say>
            <Say voice="{target_voice}" language="{target_language}">Translation: {translated_text}</Say>
            <Say voice="alice" language="hi-IN">क्या आप कुछ और कहना चाहते हैं?</Say>
            <Say voice="alice" language="en-US">Would you like to say something else?</Say>
            <Record 
                action="https://{railway_domain}/transcription-webhook" 
                method="POST"
                transcribe="true"
                transcribeCallback="https://{railway_domain}/transcription-webhook"
                maxLength="15"
                timeout="10"
                playBeep="true"
                finishOnKey="#"
            />
        </Response>"""
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"Translation error: {e}")
        # Error response
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="hi-IN">अनुवाद में त्रुटि हुई है।</Say>
            <Say voice="alice" language="en-US">There was an error in translation.</Say>
            <Say voice="alice" language="hi-IN">कृपया फिर से कोशिश करें।</Say>
            <Say voice="alice" language="en-US">Please try again.</Say>
            <Record 
                action="https://{railway_domain}/transcription-webhook" 
                method="POST"
                transcribe="true"
                transcribeCallback="https://{railway_domain}/transcription-webhook"
                maxLength="15"
                timeout="10"
                playBeep="true"
                finishOnKey="#"
            />
        </Response>"""
        return Response(twiml, mimetype='text/xml')

@app.route('/recording-status', methods=['POST'])
def recording_status():
    """Handle recording status updates"""
    call_sid = request.form.get('CallSid')
    recording_status = request.form.get('RecordingStatus', '')
    recording_url = request.form.get('RecordingUrl', '')
    
    print(f"Recording status for call {call_sid}: {recording_status}")
    if recording_url:
        print(f"Recording URL: {recording_url}")
    
    return Response('OK', mimetype='text/plain')

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
        # Initialize the translate client with proper credentials
        client = translate.Client()
        result = client.translate(text, source_language=source_lang, target_language=target_lang)
        return result['translatedText']
    except Exception as e:
        print(f"Translation error: {e}")
        # Return original text if translation fails
        return text

def process_recording_directly(recording_url):
    """Process recording directly using Google Cloud Speech-to-Text"""
    try:
        print(f"Downloading recording from: {recording_url}")
        # Download the recording
        response = requests.get(recording_url, timeout=30)
        if response.status_code != 200:
            print(f"Failed to download recording: {response.status_code}")
            return ""
        
        audio_content = response.content
        print(f"Downloaded {len(audio_content)} bytes of audio")
        
        # Initialize Speech-to-Text client
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
        print("Performing speech recognition...")
        response = client.recognize(config=config, audio=audio)
        
        if response.results:
            result = response.results[0]
            if result.is_final:
                transcript = result.alternatives[0].transcript
                confidence = result.alternatives[0].confidence
                print(f"Direct processing confidence: {confidence}")
                if confidence > 0.5:
                    return transcript
        
        return ""
        
    except Exception as e:
        print(f"Direct processing error: {e}")
        return ""

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
        print("RAILWAY TWILIO VOICE TRANSLATOR - FIXED CREDENTIALS")
        print("="*70)
        print("Features:")
        print("✓ Fixed Google Cloud credentials handling")
        print("✓ Hindi ↔ English translation")
        print("✓ Google Cloud Speech-to-Text")
        print("✓ Google Cloud Translation")
        print("✓ Proper language voice selection")
        print("✓ Railway cloud deployment")
        print("✓ Better error handling")
        print("✓ Direct recording processing fallback")
        print("✓ Enhanced logging for debugging")
        print(f"✓ Google Cloud available: {GOOGLE_CLOUD_AVAILABLE}")
        print(f"✓ Credentials setup: {credentials_setup}")
        print(f"✓ Port: {port}")
        print("="*70)
        
        if not GOOGLE_CLOUD_AVAILABLE:
            print("WARNING: Google Cloud libraries not available!")
            print("Please check your GOOGLE_APPLICATION_CREDENTIALS environment variable")
        
        if not credentials_setup:
            print("WARNING: Google Cloud credentials not properly set up!")
            print("Please check your GOOGLE_CREDENTIALS_JSON environment variable")
        
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
