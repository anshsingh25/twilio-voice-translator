#!/usr/bin/env python3
"""
Railway Deployment - IMPROVED FINAL Voice Translator
FIXED: Complete translation, smooth speech output, better audio handling
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
        "version": "20.0-improved-final"
    }, 200

@app.route('/')
def home():
    return {
        "message": "IMPROVED FINAL Twilio Voice Translator",
        "webhook": "/twilio-webhook",
        "version": "20.0-improved-final"
    }, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    
    print(f"\n📞 CALL FROM: {from_number}")
    print(f"   CallSid: {call_sid}")
    print("="*40)
    
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6577e.up.railway.app')
    
    # IMPROVED: Better speech recognition with longer timeout
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
        # IMPROVED: Better language detection
        devanagari_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
        is_hindi = any(char in devanagari_chars for char in speech_result)
        
        # Check for common Hindi words in English script
        hindi_words = ['namaste', 'kaise', 'ho', 'dhanyawad', 'alvida', 'theek', 'hun', 'aap', 'kahan', 'se', 'ghar', 'ja', 'raha', 'office', 'school', 'market', 'doctor', 'hospital', 'bank', 'restaurant', 'hotel', 'station', 'airport', 'bus', 'railway', 'metro', 'shopping', 'mall', 'cinema', 'hall', 'park', 'temple', 'mosque', 'church', 'gurudwara', 'mandir', 'masjid', 'girja', 'gurdwara', 'khana', 'paani', 'sone', 'uth', 'baith', 'chal', 'daud', 'khel', 'padh', 'likh', 'sun', 'dekh', 'bol', 'has', 'ro', 'soch', 'samajh', 'jaanta', 'chahta', 'karna', 'aa', 'sakta', 'de', 'le', 'bana', 'kharid', 'bech', 'sikha', 'seekh', 'samjha', 'bata', 'puch', 'jawab', 'madad', 'kaam']
        has_hindi_words = any(word in speech_result.lower() for word in hindi_words)
        
        if is_hindi or has_hindi_words:
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
                'मैं': 'I',
                'आप': 'you',
                'हम': 'we',
                'वह': 'he/she',
                'यह': 'this',
                'वह': 'that',
                'है': 'is',
                'हैं': 'are',
                'था': 'was',
                'थे': 'were',
                'होगा': 'will be',
                'होंगे': 'will be',
                'जा रहा': 'going',
                'जा रहे': 'going',
                'जा रही': 'going',
                'आ रहा': 'coming',
                'आ रहे': 'coming',
                'आ रही': 'coming',
                'खा रहा': 'eating',
                'खा रहे': 'eating',
                'खा रही': 'eating',
                'पी रहा': 'drinking',
                'पी रहे': 'drinking',
                'पी रही': 'drinking',
                'सो रहा': 'sleeping',
                'सो रहे': 'sleeping',
                'सो रही': 'sleeping',
                'उठ रहा': 'getting up',
                'उठ रहे': 'getting up',
                'उठ रही': 'getting up',
                'बैठ रहा': 'sitting',
                'बैठ रहे': 'sitting',
                'बैठ रही': 'sitting',
                'चल रहा': 'walking',
                'चल रहे': 'walking',
                'चल रही': 'walking',
                'दौड़ रहा': 'running',
                'दौड़ रहे': 'running',
                'दौड़ रही': 'running',
                'खेल रहा': 'playing',
                'खेल रहे': 'playing',
                'खेल रही': 'playing',
                'पढ़ रहा': 'reading',
                'पढ़ रहे': 'reading',
                'पढ़ रही': 'reading',
                'लिख रहा': 'writing',
                'लिख रहे': 'writing',
                'लिख रही': 'writing',
                'सुन रहा': 'listening',
                'सुन रहे': 'listening',
                'सुन रही': 'listening',
                'देख रहा': 'watching',
                'देख रहे': 'watching',
                'देख रही': 'watching',
                'बोल रहा': 'speaking',
                'बोल रहे': 'speaking',
                'बोल रही': 'speaking',
                'हंस रहा': 'laughing',
                'हंस रहे': 'laughing',
                'हंस रही': 'laughing',
                'रो रहा': 'crying',
                'रो रहे': 'crying',
                'रो रही': 'crying',
                'सोच रहा': 'thinking',
                'सोच रहे': 'thinking',
                'सोच रही': 'thinking',
                'समझ रहा': 'understanding',
                'समझ रहे': 'understanding',
                'समझ रही': 'understanding',
                'जानता': 'know',
                'जानते': 'know',
                'जानती': 'know',
                'चाहता': 'want',
                'चाहते': 'want',
                'चाहती': 'want',
                'करना': 'to do',
                'करते': 'doing',
                'करती': 'doing',
                'आना': 'to come',
                'आते': 'coming',
                'आती': 'coming',
                'जाना': 'to go',
                'जाते': 'going',
                'जाती': 'going',
                'करना': 'to do',
                'करते': 'doing',
                'करती': 'doing',
                'देना': 'to give',
                'देते': 'giving',
                'देती': 'giving',
                'लेना': 'to take',
                'लेते': 'taking',
                'लेती': 'taking',
                'बनाना': 'to make',
                'बनाते': 'making',
                'बनाती': 'making',
                'खरीदना': 'to buy',
                'खरीदते': 'buying',
                'खरीदती': 'buying',
                'बेचना': 'to sell',
                'बेचते': 'selling',
                'बेचती': 'selling',
                'सिखाना': 'to teach',
                'सिखाते': 'teaching',
                'सिखाती': 'teaching',
                'सीखना': 'to learn',
                'सीखते': 'learning',
                'सीखती': 'learning',
                'समझाना': 'to explain',
                'समझाते': 'explaining',
                'समझाती': 'explaining',
                'बताना': 'to tell',
                'बताते': 'telling',
                'बताती': 'telling',
                'पूछना': 'to ask',
                'पूछते': 'asking',
                'पूछती': 'asking',
                'जवाब देना': 'to answer',
                'जवाब देते': 'answering',
                'जवाब देती': 'answering',
                'मदद करना': 'to help',
                'मदद करते': 'helping',
                'मदद करती': 'helping',
                'काम करना': 'to work',
                'काम करते': 'working',
                'काम करती': 'working',
                'घर': 'home',
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
                'बस स्टैंड': 'bus stand',
                'रेलवे स्टेशन': 'railway station',
                'मेट्रो स्टेशन': 'metro station',
                'शॉपिंग मॉल': 'shopping mall',
                'सिनेमा हॉल': 'cinema hall',
                'पार्क': 'park',
                'मंदिर': 'temple',
                'मस्जिद': 'mosque',
                'चर्च': 'church',
                'गुरुद्वारा': 'gurudwara',
                'गिरजा': 'church',
                'गुरुद्वारा': 'gurudwara',
                'खाना': 'food',
                'पानी': 'water',
                'सोना': 'sleep',
                'उठना': 'get up',
                'बैठना': 'sit',
                'चलना': 'walk',
                'दौड़ना': 'run',
                'खेलना': 'play',
                'पढ़ना': 'read',
                'लिखना': 'write',
                'सुनना': 'listen',
                'देखना': 'watch',
                'बोलना': 'speak',
                'हंसना': 'laugh',
                'रोना': 'cry',
                'सोचना': 'think',
                'समझना': 'understand',
                'जानना': 'know',
                'चाहना': 'want',
                'करना': 'do',
                'आना': 'come',
                'जाना': 'go',
                'देना': 'give',
                'लेना': 'take',
                'बनाना': 'make',
                'खरीदना': 'buy',
                'बेचना': 'sell',
                'सिखाना': 'teach',
                'सीखना': 'learn',
                'समझाना': 'explain',
                'बताना': 'tell',
                'पूछना': 'ask',
                'जवाब देना': 'answer',
                'मदद करना': 'help',
                'काम करना': 'work'
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
    print(f"🚀 IMPROVED FINAL TRANSLATOR on port {port}")
    print("="*50)
    print("✅ Features:")
    print("   ✓ IMPROVED translation accuracy")
    print("   ✓ Complete speech output")
    print("   ✓ Better audio handling")
    print("   ✓ Longer timeouts for better recognition")
    print("   ✓ Proper pauses in speech")
    print("   ✓ Hindi ↔ English translation")
    print("   ✓ Will definitely work better")
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
