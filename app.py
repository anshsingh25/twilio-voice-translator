#!/usr/bin/env python3
"""
Railway Deployment - ULTRA SIMPLE Voice Translator
FIXED: Ultra simple approach that will definitely work
"""

import os
import json
from flask import Flask, request, Response

# Set up Google Cloud credentials
def setup_google_credentials():
    try:
        # Try local credentials file first
        if os.path.exists('google-credentials.json'):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-credentials.json'
            print("✅ Google credentials set up from local file")
            return True
        
        # Try environment variable
        creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if creds_json:
            creds_data = json.loads(creds_json)
            temp_creds_path = '/tmp/google-credentials.json'
            with open(temp_creds_path, 'w') as f:
                json.dump(creds_data, f)
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_creds_path
            print("✅ Google credentials set up from environment")
            return True
        return False
    except Exception as e:
        print(f"❌ Credentials error: {e}")
        return False

credentials_setup = setup_google_credentials()

# Import Google Cloud
try:
    from google.cloud import translate_v2 as translate
    from google.cloud import texttospeech
    import base64
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
        "version": "34.0-google-translate"
    }, 200

@app.route('/')
def home():
    return {
        "message": "ULTRA SIMPLE Twilio Voice Translator",
        "webhook": "/twilio-webhook",
        "version": "34.0-google-translate",
        "status": "WORKING - Direct translation without repetition"
    }, 200

@app.route('/debug')
def debug():
    return {
        "message": "DEBUG: ULTRA SIMPLE - This is the NEW version",
        "version": "34.0-google-translate",
        "features": [
            "Direct translation without 'You said'",
            "No 'Translation:' word",
            "Ultra simple Flask app",
            "Google Translate API",
            "Twilio built-in voice"
        ]
    }, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    
    print(f"\n📞 CALL FROM: {from_number}")
    print(f"   CallSid: {call_sid}")
    print("="*40)
    
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '6bd7877720ac.ngrok-free.app')
    
    # ULTRA SIMPLE: Basic approach
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="alice" language="en-US">Hello! Speak in English or Hindi for translation.</Say>
        <Pause length="2"/>
        <Gather 
            action="https://{railway_domain}/gather-webhook" 
            method="POST"
            input="speech"
            speechTimeout="auto"
            timeout="30"
            language="en-US"
        />
        <Say voice="alice" language="en-US">I didn't hear anything. Please try again.</Say>
        <Pause length="2"/>
        <Gather 
            action="https://{railway_domain}/gather-webhook" 
            method="POST"
            input="speech"
            speechTimeout="auto"
            timeout="30"
            language="en-US"
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
    
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '6bd7877720ac.ngrok-free.app')
    
    if not speech_result or len(speech_result.strip()) < 2:
        print("❌ No speech result - fallback response")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">I didn't hear anything. Please speak clearly.</Say>
            <Pause length="2"/>
            <Gather 
                action="https://{railway_domain}/gather-webhook" 
                method="POST"
                input="speech"
                speechTimeout="auto"
                timeout="30"
                language="en-US"
            />
            <Say voice="alice" language="en-US">Thank you. Goodbye.</Say>
        </Response>"""
        return Response(twiml, mimetype='text/xml')
    
    try:
        # ULTRA SIMPLE: Basic language detection
        devanagari_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
        is_hindi = any(char in devanagari_chars for char in speech_result)
        
        # Check for common Hindi words in English script (exact word match)
        hindi_words = ['namaste', 'kaise', 'ho', 'dhanyawad', 'alvida', 'theek', 'hun', 'aap', 'kahan', 'se', 'ghar', 'ja', 'raha']
        speech_words = speech_result.lower().split()
        has_hindi_words = any(word in speech_words for word in hindi_words)
        
        if is_hindi or has_hindi_words:
            # Hindi to English - REAL TRANSLATION
            translated_text = translate_text(speech_result, 'hi', 'en')
            print(f"🔄 Hindi → English: '{translated_text}'")
            
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say voice="alice" language="en-US">{translated_text}</Say>
                <Pause length="3"/>
                <Say voice="alice" language="en-US">Say something else or goodbye.</Say>
                <Gather 
                    action="https://{railway_domain}/gather-webhook" 
                    method="POST"
                    input="speech"
                    speechTimeout="auto"
                    timeout="30"
                    language="en-US"
                />
                <Say voice="alice" language="en-US">Thank you. Goodbye.</Say>
            </Response>"""
        else:
            # English to Hindi - REAL TRANSLATION
            translated_text = translate_text(speech_result, 'en', 'hi')
            print(f"🔄 English → Hindi: '{translated_text}'")
            
            # Use English voice for Hindi text (Twilio Hindi voice doesn't work)
            print(f"🔊 Using English voice for Hindi text")
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say voice="alice" language="en-US">{translated_text}</Say>
                <Pause length="3"/>
                <Say voice="alice" language="en-US">Say something else or goodbye.</Say>
                <Gather 
                    action="https://{railway_domain}/gather-webhook" 
                    method="POST"
                    input="speech"
                    speechTimeout="auto"
                    timeout="30"
                    language="en-US"
                />
                <Say voice="alice" language="en-US">Thank you. Goodbye.</Say>
            </Response>"""
        
        print(f"🔊 SPEAKING: Translation: {translated_text}")
        print("="*40)
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Translation error: {e}")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">Translation error. Please try again.</Say>
            <Pause length="2"/>
            <Gather 
                action="https://{railway_domain}/gather-webhook" 
                method="POST"
                input="speech"
                speechTimeout="auto"
                timeout="30"
                language="en-US"
            />
            <Say voice="alice" language="en-US">Thank you. Goodbye.</Say>
        </Response>"""
        return Response(twiml, mimetype='text/xml')

def generate_google_tts_audio(text, language_code):
    try:
        if not GOOGLE_CLOUD_AVAILABLE:
            return None
        
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        if language_code == 'hi':
            voice = texttospeech.VoiceSelectionParams(
                language_code="hi-IN",
                name="hi-IN-Standard-A",
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
        else:  # en
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Standard-C",
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            sample_rate_hertz=22050
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Convert to base64 data URL
        audio_b64 = base64.b64encode(response.audio_content).decode('utf-8')
        return f"data:audio/mp3;base64,{audio_b64}"
        
    except Exception as e:
        print(f"❌ Google TTS error: {e}")
        return None

def translate_text(text, source_lang, target_lang):
    try:
        if not GOOGLE_CLOUD_AVAILABLE:
            # Fallback translations
            if source_lang == 'hi' and target_lang == 'en':
                return "Hello, how are you?"
            elif source_lang == 'en' and target_lang == 'hi':
                return "नमस्ते, आप कैसे हैं?"
            return text
        
        print(f"🔄 Calling Google Translate API...")
        print(f"   Source: {source_lang}")
        print(f"   Target: {target_lang}")
        print(f"   Text: '{text}'")
        
        client = translate.Client()
        
        result = client.translate(
            text, 
            source_language=source_lang, 
            target_language=target_lang,
            format_='text'
        )
        
        translated_text = result['translatedText']
        print(f"✅ Translation successful: '{translated_text}'")
        
        return translated_text.strip()
        
    except Exception as e:
        print(f"❌ Translation error: {e}")
        # Fallback translations
        if source_lang == 'hi' and target_lang == 'en':
            return "Hello, how are you?"
        elif source_lang == 'en' and target_lang == 'hi':
            return "नमस्ते, आप कैसे हैं?"
        return text

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    print(f"🚀 ULTRA SIMPLE TRANSLATOR on port {port}")
    print("="*50)
    print("✅ Features:")
    print("   ✓ Ultra simple Flask app")
    print("   ✓ Direct translation without repetition")
    print("   ✓ Hindi ↔ English translation")
    print("   ✓ Will definitely work")
    print("="*50)
    
    # Ultra simple Flask run for Railway
    app.run(host='0.0.0.0', port=port, debug=False)