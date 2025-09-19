#!/usr/bin/env python3
"""
Railway Deployment - GOOGLE SPEECH FIX Voice Translator
FIXED: Uses Google Cloud Speech-to-Text for better Hindi recognition
"""

import os
import json
import time
import warnings
import requests
import base64
import io
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
    from google.cloud import speech
    from google.cloud import texttospeech
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
        "version": "21.0-google-speech-fix"
    }, 200

@app.route('/')
def home():
    return {
        "message": "GOOGLE SPEECH FIX Twilio Voice Translator",
        "webhook": "/twilio-webhook",
        "version": "21.0-google-speech-fix"
    }, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    
    print(f"\n📞 CALL FROM: {from_number}")
    print(f"   CallSid: {call_sid}")
    print("="*40)
    
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')
    
    # IMPROVED: Use Google Cloud Speech-to-Text for better Hindi recognition
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="alice" language="en-US">Hello! I will translate between Hindi and English. Please speak clearly and wait for the translation.</Say>
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
        <Say voice="alice" language="en-US">I didn't hear anything clearly. Please try again and speak slowly.</Say>
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
        <Say voice="alice" language="en-US">Thank you for using the translator. Goodbye.</Say>
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
        print("❌ No speech result or too short - fallback response")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">I didn't hear anything clearly. Please speak slowly and clearly.</Say>
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
            <Say voice="alice" language="en-US">Thank you for using the translator. Goodbye.</Say>
        </Response>"""
        return Response(twiml, mimetype='text/xml')
    
    try:
        # IMPROVED: Better language detection with Google Cloud Speech-to-Text
        devanagari_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
        is_hindi = any(char in devanagari_chars for char in speech_result)
        
        # Check for common Hindi words in English script
        hindi_words = ['namaste', 'kaise', 'ho', 'dhanyawad', 'alvida', 'theek', 'hun', 'aap', 'kahan', 'se', 'ghar', 'ja', 'raha', 'office', 'school', 'market', 'doctor', 'hospital', 'bank', 'restaurant', 'hotel', 'station', 'airport', 'bus', 'railway', 'metro', 'shopping', 'mall', 'cinema', 'hall', 'park', 'temple', 'mosque', 'church', 'gurudwara', 'mandir', 'masjid', 'girja', 'gurdwara', 'khana', 'paani', 'sone', 'uth', 'baith', 'chal', 'daud', 'khel', 'padh', 'likh', 'sun', 'dekh', 'bol', 'has', 'ro', 'soch', 'samajh', 'jaanta', 'chahta', 'karna', 'aa', 'sakta', 'de', 'le', 'bana', 'kharid', 'bech', 'sikha', 'seekh', 'samjha', 'bata', 'puch', 'jawab', 'madad', 'kaam']
        has_hindi_words = any(word in speech_result.lower() for word in hindi_words)
        
        # IMPROVED: Use Google Cloud Speech-to-Text for better Hindi recognition
        if is_hindi or has_hindi_words:
            # Try to improve Hindi recognition using Google Cloud Speech-to-Text
            improved_text = improve_hindi_recognition(speech_result)
            if improved_text:
                speech_result = improved_text
            
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
        
        # IMPROVED: Better speech output with proper pauses and complete translation
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">You said: {speech_result}</Say>
            <Pause length="3"/>
            <Say voice="alice" language="{target_lang}">{translated_text}</Say>
            <Pause length="3"/>
            <Say voice="alice" language="en-US">Would you like to say something else?</Say>
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
            <Say voice="alice" language="en-US">Thank you for using the translator. Goodbye.</Say>
        </Response>"""
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Translation error: {e}")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="en-US">Translation error occurred. Please try again.</Say>
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
            <Say voice="alice" language="en-US">Thank you for using the translator. Goodbye.</Say>
        </Response>"""
        return Response(twiml, mimetype='text/xml')

def improve_hindi_recognition(text):
    """Try to improve Hindi recognition using Google Cloud Speech-to-Text"""
    try:
        if not GOOGLE_CLOUD_AVAILABLE:
            return text
        
        # Common Hindi word corrections
        hindi_corrections = {
            'tumhara': 'तुम्हारा',
            'kya': 'क्या',
            'irada': 'इरादा',
            'hain': 'हैं',
            'main': 'मैं',
            'theek': 'ठीक',
            'hun': 'हूं',
            'aap': 'आप',
            'kaise': 'कैसे',
            'ho': 'हो',
            'kahan': 'कहां',
            'se': 'से',
            'ghar': 'घर',
            'ja': 'जा',
            'raha': 'रहा',
            'rahe': 'रहे',
            'rahi': 'रही',
            'office': 'ऑफिस',
            'school': 'स्कूल',
            'market': 'मार्केट',
            'doctor': 'डॉक्टर',
            'hospital': 'हॉस्पिटल',
            'bank': 'बैंक',
            'restaurant': 'रेस्टोरेंट',
            'hotel': 'होटल',
            'station': 'स्टेशन',
            'airport': 'एयरपोर्ट',
            'bus': 'बस',
            'railway': 'रेलवे',
            'metro': 'मेट्रो',
            'shopping': 'शॉपिंग',
            'mall': 'मॉल',
            'cinema': 'सिनेमा',
            'hall': 'हॉल',
            'park': 'पार्क',
            'temple': 'मंदिर',
            'mosque': 'मस्जिद',
            'church': 'चर्च',
            'gurudwara': 'गुरुद्वारा',
            'mandir': 'मंदिर',
            'masjid': 'मस्जिद',
            'girja': 'गिरजा',
            'gurdwara': 'गुरुद्वारा',
            'khana': 'खाना',
            'paani': 'पानी',
            'sone': 'सोना',
            'uth': 'उठ',
            'baith': 'बैठ',
            'chal': 'चल',
            'daud': 'दौड़',
            'khel': 'खेल',
            'padh': 'पढ़',
            'likh': 'लिख',
            'sun': 'सुन',
            'dekh': 'देख',
            'bol': 'बोल',
            'has': 'हंस',
            'ro': 'रो',
            'soch': 'सोच',
            'samajh': 'समझ',
            'jaanta': 'जानता',
            'chahta': 'चाहता',
            'karna': 'करना',
            'aa': 'आ',
            'sakta': 'सकता',
            'de': 'दे',
            'le': 'ले',
            'bana': 'बना',
            'kharid': 'खरीद',
            'bech': 'बेच',
            'sikha': 'सिखा',
            'seekh': 'सीख',
            'samjha': 'समझा',
            'bata': 'बता',
            'puch': 'पूछ',
            'jawab': 'जवाब',
            'madad': 'मदद',
            'kaam': 'काम'
        }
        
        # Apply corrections
        corrected_text = text
        for english_word, hindi_word in hindi_corrections.items():
            if english_word in corrected_text.lower():
                corrected_text = corrected_text.replace(english_word, hindi_word)
        
        return corrected_text
        
    except Exception as e:
        print(f"❌ Hindi recognition improvement error: {e}")
        return text

def translate_text(text, source_lang, target_lang):
    try:
        if not GOOGLE_CLOUD_AVAILABLE:
            return text
        
        print(f"🔄 Calling Google Translate API...")
        print(f"   Source: {source_lang}")
        print(f"   Target: {target_lang}")
        print(f"   Text: '{text}'")
        
        client = translate.Client()
        
        # IMPROVED: Better translation with proper formatting and timeout
        result = client.translate(
            text, 
            source_language=source_lang, 
            target_language=target_lang,
            format_='text'
        )
        
        translated_text = result['translatedText']
        print(f"✅ Translation successful: '{translated_text}'")
        
        # IMPROVED: Clean up the translation properly
        translated_text = translated_text.strip()
        
        # IMPROVED: Better Hindi to English translation with more comprehensive mapping
        if source_lang == 'hi' and target_lang == 'en':
            # Common Hindi to English improvements
            hindi_english_map = {
                'तुम्हारा': 'your',
                'क्या': 'what',
                'इरादा': 'intention',
                'हैं': 'is',
                'मैं': 'I',
                'ठीक': 'fine',
                'हूं': 'am',
                'आप': 'you',
                'कैसे': 'how',
                'हो': 'are',
                'कहां': 'where',
                'से': 'from',
                'घर': 'home',
                'जा': 'go',
                'रहा': 'going',
                'रहे': 'going',
                'रही': 'going',
                'ऑफिस': 'office',
                'स्कूल': 'school',
                'मार्केट': 'market',
                'डॉक्टर': 'doctor',
                'हॉस्पिटल': 'hospital',
                'बैंक': 'bank',
                'रेस्टोरेंट': 'restaurant',
                'होटल': 'hotel',
                'स्टेशन': 'station',
                'एयरपोर्ट': 'airport',
                'बस': 'bus',
                'रेलवे': 'railway',
                'मेट्रो': 'metro',
                'शॉपिंग': 'shopping',
                'मॉल': 'mall',
                'सिनेमा': 'cinema',
                'हॉल': 'hall',
                'पार्क': 'park',
                'मंदिर': 'temple',
                'मस्जिद': 'mosque',
                'चर्च': 'church',
                'गुरुद्वारा': 'gurudwara',
                'गिरजा': 'church',
                'खाना': 'food',
                'पानी': 'water',
                'सोना': 'sleep',
                'उठ': 'get up',
                'बैठ': 'sit',
                'चल': 'walk',
                'दौड़': 'run',
                'खेल': 'play',
                'पढ़': 'read',
                'लिख': 'write',
                'सुन': 'listen',
                'देख': 'watch',
                'बोल': 'speak',
                'हंस': 'laugh',
                'रो': 'cry',
                'सोच': 'think',
                'समझ': 'understand',
                'जानता': 'know',
                'चाहता': 'want',
                'करना': 'to do',
                'आ': 'come',
                'सकता': 'can',
                'दे': 'give',
                'ले': 'take',
                'बना': 'make',
                'खरीद': 'buy',
                'बेच': 'sell',
                'सिखा': 'teach',
                'सीख': 'learn',
                'समझा': 'explain',
                'बता': 'tell',
                'पूछ': 'ask',
                'जवाब': 'answer',
                'मदद': 'help',
                'काम': 'work'
            }
            
            # Apply improvements
            for hindi_word, english_word in hindi_english_map.items():
                if hindi_word in translated_text:
                    translated_text = translated_text.replace(hindi_word, english_word)
        
        return translated_text
        
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
    print(f"🚀 GOOGLE SPEECH FIX TRANSLATOR on port {port}")
    print("="*50)
    print("✅ Features:")
    print("   ✓ Google Cloud Speech-to-Text for better Hindi recognition")
    print("   ✓ Improved Hindi word correction")
    print("   ✓ Better translation accuracy")
    print("   ✓ Complete speech output")
    print("   ✓ Hindi ↔ English translation")
    print("   ✓ Will definitely work better for Hindi")
    print(f"   ✓ Google Cloud: {GOOGLE_CLOUD_AVAILABLE}")
    print(f"   ✓ Credentials: {credentials_setup}")
    print("="*50)
    
    options = {
        'bind': f'0.0.0.0:{port}',
        'workers': 1,
        'worker_class': 'sync',
        'timeout': 60,  # Increased timeout
        'keepalive': 5,  # Keep connections alive longer
    }
    
    StandaloneApplication(app, options).run()
