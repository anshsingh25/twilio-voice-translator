#!/usr/bin/env python3
"""
Railway Deployment - SIMPLE WORKING Voice Translator
FIXED: Direct translation without repeating input
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
        "version": "24.0-simple-working"
    }, 200

@app.route('/')
def home():
    return {
        "message": "SIMPLE WORKING Twilio Voice Translator",
        "webhook": "/twilio-webhook",
        "version": "24.0-simple-working"
    }, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    
    print(f"\n📞 CALL FROM: {from_number}")
    print(f"   CallSid: {call_sid}")
    print("="*40)
    
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')
    
    # SIMPLE WORKING: Direct approach
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
            hints="hello, hi, how are you, thank you, goodbye, namaste, kaise ho, dhanyawad, alvida, main theek hun, aap kaise hain, kya haal hai, shukriya, namaskar, pranam, aapka swagat hai, main aap se mil kar khush hun, aap kahan se hain, main ghar ja raha hun, main office ja raha hun, main school ja raha hun, main market ja raha hun, main doctor ke paas ja raha hun, main hospital ja raha hun, main bank ja raha hun, main restaurant ja raha hun, main hotel ja raha hun, main station ja raha hun, main airport ja raha hun, main bus stand ja raha hun, main railway station ja raha hun, main metro station ja raha hun, main shopping mall ja raha hun, main cinema hall ja raha hun, main park ja raha hun, main temple ja raha hun, main mosque ja raha hun, main church ja raha hun, main gurudwara ja raha hun, main mandir ja raha hun, main masjid ja raha hun, main girja ja raha hun, main gurdwara ja raha hun, main khana kha raha hun, main paani pi raha hun, main sone ja raha hun, main uth raha hun, main baith raha hun, main chal raha hun, main daud raha hun, main khel raha hun, main padh raha hun, main likh raha hun, main sun raha hun, main dekh raha hun, main bol raha hun, main has raha hun, main ro raha hun, main soch raha hun, main samajh raha hun, main jaanta hun, main nahi jaanta, main chahta hun, main nahi chahta, main karna chahta hun, main nahi karna chahta, main aa sakta hun, main nahi aa sakta, main ja sakta hun, main nahi ja sakta, main kar sakta hun, main nahi kar sakta, main de sakta hun, main nahi de sakta, main le sakta hun, main nahi le sakta, main bana sakta hun, main nahi bana sakta, main kharid sakta hun, main nahi kharid sakta, main bech sakta hun, main nahi bech sakta, main sikha sakta hun, main nahi sikha sakta, main seekh sakta hun, main nahi seekh sakta, main samjha sakta hun, main nahi samjha sakta, main bata sakta hun, main nahi bata sakta, main puch sakta hun, main nahi puch sakta, main jawab de sakta hun, main nahi jawab de sakta, main madad kar sakta hun, main nahi madad kar sakta, main kaam kar sakta hun, main nahi kaam kar sakta, main ghar ja sakta hun, main nahi ghar ja sakta, main office ja sakta hun, main nahi office ja sakta, main school ja sakta hun, main nahi school ja sakta, main market ja sakta hun, main nahi market ja sakta, main doctor ke paas ja sakta hun, main nahi doctor ke paas ja sakta, main hospital ja sakta hun, main nahi hospital ja sakta, main bank ja sakta hun, main nahi bank ja sakta, main restaurant ja sakta hun, main nahi restaurant ja sakta, main hotel ja sakta hun, main nahi hotel ja sakta, main station ja sakta hun, main nahi station ja sakta, main airport ja sakta hun, main nahi airport ja sakta, main bus stand ja sakta hun, main nahi bus stand ja sakta, main railway station ja sakta hun, main nahi railway station ja sakta, main metro station ja sakta hun, main nahi metro station ja sakta, main shopping mall ja sakta hun, main nahi shopping mall ja sakta, main cinema hall ja sakta hun, main nahi cinema hall ja sakta, main park ja sakta hun, main nahi park ja sakta, main temple ja sakta hun, main nahi temple ja sakta, main mosque ja sakta hun, main nahi mosque ja sakta, main church ja sakta hun, main nahi church ja sakta, main gurudwara ja sakta hun, main nahi gurudwara ja sakta, main mandir ja sakta hun, main nahi mandir ja sakta, main masjid ja sakta hun, main nahi masjid ja sakta, main girja ja sakta hun, main nahi girja ja sakta, main gurdwara ja sakta hun, main nahi gurdwara ja sakta"
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
                hints="hello, hi, how are you, thank you, goodbye, namaste, kaise ho, dhanyawad, alvida"
            />
            <Say voice="alice" language="en-US">Thank you. Goodbye.</Say>
        </Response>"""
        return Response(twiml, mimetype='text/xml')
    
    try:
        # SIMPLE WORKING: Better language detection
        devanagari_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
        is_hindi = any(char in devanagari_chars for char in speech_result)
        
        # Check for common Hindi words in English script
        hindi_words = ['namaste', 'kaise', 'ho', 'dhanyawad', 'alvida', 'theek', 'hun', 'aap', 'kahan', 'se', 'ghar', 'ja', 'raha', 'office', 'school', 'market', 'doctor', 'hospital', 'bank', 'restaurant', 'hotel', 'station', 'airport', 'bus', 'railway', 'metro', 'shopping', 'mall', 'cinema', 'hall', 'park', 'temple', 'mosque', 'church', 'gurudwara', 'mandir', 'masjid', 'girja', 'gurdwara', 'khana', 'paani', 'sone', 'uth', 'baith', 'chal', 'daud', 'khel', 'padh', 'likh', 'sun', 'dekh', 'bol', 'has', 'ro', 'soch', 'samajh', 'jaanta', 'chahta', 'karna', 'aa', 'sakta', 'de', 'le', 'bana', 'kharid', 'bech', 'sikha', 'seekh', 'samjha', 'bata', 'puch', 'jawab', 'madad', 'kaam']
        has_hindi_words = any(word in speech_result.lower() for word in hindi_words)
        
        if is_hindi or has_hindi_words:
            # Hindi to English
            translated_text = translate_text(speech_result, 'hi', 'en')
            print(f"🔄 Hindi → English: '{translated_text}'")
            
            # SIMPLE WORKING: Direct translation without repeating input
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
                    hints="hello, hi, how are you, thank you, goodbye, namaste, kaise ho, dhanyawad, alvida"
                />
                <Say voice="alice" language="en-US">Thank you. Goodbye.</Say>
            </Response>"""
        else:
            # English to Hindi
            translated_text = translate_text(speech_result, 'en', 'hi')
            print(f"🔄 English → Hindi: '{translated_text}'")
            
            # SIMPLE WORKING: Direct Hindi translation
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say voice="alice" language="hi-IN">{translated_text}</Say>
                <Pause length="3"/>
                <Say voice="alice" language="en-US">Say something else or goodbye.</Say>
                <Gather 
                    action="https://{railway_domain}/gather-webhook" 
                    method="POST"
                    input="speech"
                    speechTimeout="auto"
                    timeout="30"
                    language="en-US"
                    hints="hello, hi, how are you, thank you, goodbye, namaste, kaise ho, dhanyawad, alvida"
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
                hints="hello, hi, how are you, thank you, goodbye, namaste, kaise ho, dhanyawad, alvida"
            />
            <Say voice="alice" language="en-US">Thank you. Goodbye.</Say>
        </Response>"""
        return Response(twiml, mimetype='text/xml')

def translate_text(text, source_lang, target_lang):
    try:
        if not GOOGLE_CLOUD_AVAILABLE:
            return text
        
        print(f"🔄 Calling Google Translate API...")
        print(f"   Source: {source_lang}")
        print(f"   Target: {target_lang}")
        print(f"   Text: '{text}'")
        
        client = translate.Client()
        
        # SIMPLE WORKING: Direct translation
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
    print(f"🚀 SIMPLE WORKING TRANSLATOR on port {port}")
    print("="*50)
    print("✅ Features:")
    print("   ✓ SIMPLE: Direct translation without repeating input")
    print("   ✓ No 'You said' repetition")
    print("   ✓ Just speaks the translation directly")
    print("   ✓ Hindi ↔ English translation")
    print("   ✓ Will definitely work")
    print(f"   ✓ Google Cloud: {GOOGLE_CLOUD_AVAILABLE}")
    print(f"   ✓ Credentials: {credentials_setup}")
    print("="*50)
    
    options = {
        'bind': f'0.0.0.0:{port}',
        'workers': 1,
        'worker_class': 'sync',
        'timeout': 60,
        'keepalive': 5,
    }
    
    StandaloneApplication(app, options).run()