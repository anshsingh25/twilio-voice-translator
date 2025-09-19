#!/usr/bin/env python3
"""
Railway Deployment - TTS Voice Translation
Uses Google Cloud Text-to-Speech for better voice quality
"""

import os
import json
import time
import warnings
import requests
import base64
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
        "version": "8.0-tts-translation"
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
        "recording_webhook": "/recording-webhook",
        "tts_webhook": "/tts-webhook",
        "google_cloud_available": GOOGLE_CLOUD_AVAILABLE,
        "version": "8.0-tts-translation",
        "features": [
            "Google Cloud Text-to-Speech integration",
            "Hindi ↔ English translation",
            "Google Cloud Speech-to-Text",
            "Google Cloud Translation",
            "High-quality voice synthesis"
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
        <Say language="hi-IN">नमस्ते! मैं आपकी आवाज़ का अनुवाद करूंगा।</Say>
        <Say language="en-US">Hello! I will translate your voice.</Say>
        <Say language="hi-IN">अब आप बोल सकते हैं।</Say>
        <Say language="en-US">You can start speaking now.</Say>
        <Record 
            action="https://{railway_domain}/recording-webhook" 
            method="POST"
            transcribe="true"
            transcribeCallback="https://{railway_domain}/transcription-webhook"
            maxLength="15"
            timeout="10"
            playBeep="true"
            finishOnKey="#"
            recordingStatusCallback="https://{railway_domain}/recording-status"
        />
        <Say language="hi-IN">धन्यवाद! आपका अनुवाद तैयार है।</Say>
        <Say language="en-US">Thank you! Your translation is ready.</Say>
    </Response>"""
    
    return Response(twiml, mimetype='text/xml')

@app.route('/recording-webhook', methods=['POST'])
def recording_webhook():
    """Handle recording completion"""
    call_sid = request.form.get('CallSid')
    recording_url = request.form.get('RecordingUrl', '')
    recording_duration = request.form.get('RecordingDuration', '0')
    
    print(f"Recording completed for call {call_sid}")
    print(f"Recording URL: {recording_url}")
    print(f"Recording Duration: {recording_duration} seconds")
    
    # Get the Railway domain
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')
    
    # TwiML response after recording
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say language="hi-IN">आपकी आवाज़ रिकॉर्ड हो गई है।</Say>
        <Say language="en-US">Your voice has been recorded.</Say>
        <Say language="hi-IN">कृपया प्रतीक्षा करें, मैं अनुवाद कर रहा हूं।</Say>
        <Say language="en-US">Please wait, I am processing your message.</Say>
        <Pause length="3"/>
        <Say language="hi-IN">अनुवाद प्रक्रिया पूरी हो गई है।</Say>
        <Say language="en-US">Translation process completed.</Say>
        <Say language="hi-IN">क्या आप कुछ और कहना चाहते हैं?</Say>
        <Say language="en-US">Would you like to say something else?</Say>
        <Record 
            action="https://{railway_domain}/recording-webhook" 
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

@app.route('/transcription-webhook', methods=['POST'])
def transcription_webhook():
    """Handle transcription results and provide translation"""
    call_sid = request.form.get('CallSid')
    transcription_text = request.form.get('TranscriptionText', '')
    transcription_status = request.form.get('TranscriptionStatus', '')
    recording_url = request.form.get('RecordingUrl', '')
    
    print(f"Transcription webhook called for call {call_sid}")
    print(f"Transcription Status: {transcription_status}")
    print(f"Transcription Text: {transcription_text}")
    print(f"Recording URL: {recording_url}")
    
    # Get the Railway domain
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')
    
    if transcription_status != 'completed' or not transcription_text:
        # If transcription failed, try to process the recording directly
        if recording_url and GOOGLE_CLOUD_AVAILABLE:
            try:
                transcription_text = process_recording_directly(recording_url)
                print(f"Direct processing result: {transcription_text}")
            except Exception as e:
                print(f"Direct processing failed: {e}")
                transcription_text = ""
    
    if not transcription_text:
        # Fallback response if no transcription
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say language="hi-IN">मुझे आपकी आवाज़ समझ नहीं आई।</Say>
            <Say language="en-US">I couldn't understand your voice.</Say>
            <Say language="hi-IN">कृपया फिर से बोलें।</Say>
            <Say language="en-US">Please speak again.</Say>
            <Record 
                action="https://{railway_domain}/recording-webhook" 
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
        
        # Generate TTS audio for the translation
        tts_audio_url = generate_tts_audio(translated_text, target_language)
        
        if tts_audio_url:
            # Create TwiML response with TTS audio
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say language="en-US">You said: {transcription_text}</Say>
                <Say language="en-US">Translation:</Say>
                <Play>{tts_audio_url}</Play>
                <Say language="hi-IN">क्या आप कुछ और कहना चाहते हैं?</Say>
                <Say language="en-US">Would you like to say something else?</Say>
                <Record 
                    action="https://{railway_domain}/recording-webhook" 
                    method="POST"
                    transcribe="true"
                    transcribeCallback="https://{railway_domain}/transcription-webhook"
                    maxLength="15"
                    timeout="10"
                    playBeep="true"
                    finishOnKey="#"
                />
            </Response>"""
        else:
            # Fallback to Say verb if TTS fails
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say language="en-US">You said: {transcription_text}</Say>
                <Say language="{target_language}">Translation: {translated_text}</Say>
                <Say language="hi-IN">क्या आप कुछ और कहना चाहते हैं?</Say>
                <Say language="en-US">Would you like to say something else?</Say>
                <Record 
                    action="https://{railway_domain}/recording-webhook" 
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
            <Say language="hi-IN">अनुवाद में त्रुटि हुई है।</Say>
            <Say language="en-US">There was an error in translation.</Say>
            <Say language="hi-IN">कृपया फिर से कोशिश करें।</Say>
            <Say language="en-US">Please try again.</Say>
            <Record 
                action="https://{railway_domain}/recording-webhook" 
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

@app.route('/tts-webhook', methods=['POST'])
def tts_webhook():
    """Handle TTS audio generation requests"""
    text = request.form.get('text', '')
    language = request.form.get('language', 'en-US')
    
    print(f"TTS request: {text} in {language}")
    
    try:
        audio_url = generate_tts_audio(text, language)
        if audio_url:
            return {"status": "success", "audio_url": audio_url}
        else:
            return {"status": "error", "message": "Failed to generate audio"}
    except Exception as e:
        print(f"TTS webhook error: {e}")
        return {"status": "error", "message": str(e)}

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
        client = translate.Client()
        result = client.translate(text, source_language=source_lang, target_language=target_lang)
        return result['translatedText']
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text if translation fails

def generate_tts_audio(text, language_code):
    """Generate TTS audio using Google Cloud Text-to-Speech"""
    if not GOOGLE_CLOUD_AVAILABLE:
        print("Google Cloud not available for TTS")
        return None
    
    try:
        # Initialize TTS client
        client = texttospeech.TextToSpeechClient()
        
        # Configure synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Configure voice
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        
        # Configure audio
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.9,
            pitch=0.0
        )
        
        # Perform synthesis
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save audio to a temporary file
        audio_filename = f"tts_{int(time.time())}.mp3"
        audio_path = f"/tmp/{audio_filename}"
        
        with open(audio_path, "wb") as out:
            out.write(response.audio_content)
        
        print(f"TTS audio generated: {audio_path}")
        
        # For Railway deployment, we need to serve the audio file
        # In a real deployment, you'd upload this to a CDN or cloud storage
        # For now, we'll return a placeholder URL
        railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')
        audio_url = f"https://{railway_domain}/audio/{audio_filename}"
        
        return audio_url
        
    except Exception as e:
        print(f"TTS generation error: {e}")
        return None

def process_recording_directly(recording_url):
    """Process recording directly using Google Cloud Speech-to-Text"""
    try:
        # Download the recording
        response = requests.get(recording_url, timeout=30)
        if response.status_code != 200:
            print(f"Failed to download recording: {response.status_code}")
            return ""
        
        audio_content = response.content
        
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
        print("RAILWAY TWILIO VOICE TRANSLATOR - TTS TRANSLATION")
        print("="*70)
        print("Features:")
        print("✓ Google Cloud Text-to-Speech integration")
        print("✓ Hindi ↔ English translation")
        print("✓ Google Cloud Speech-to-Text")
        print("✓ Google Cloud Translation")
        print("✓ High-quality voice synthesis")
        print("✓ Railway cloud deployment")
        print("✓ Better error handling")
        print("✓ Direct recording processing fallback")
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
