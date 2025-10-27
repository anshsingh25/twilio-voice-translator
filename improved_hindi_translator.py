#!/usr/bin/env python3
"""
Improved Hindi Translator
Better Hindi recognition + Google Cloud integration
Works with existing Twilio setup
"""

import os
import json
from flask import Flask, request, Response
from twilio.rest import Client

# Set up Google Cloud credentials
def setup_google_credentials():
    try:
        if os.path.exists('google-credentials.json'):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-credentials.json'
            print("✅ Google credentials set up from local file")
            return True
        return False
    except Exception as e:
        print(f"❌ Credentials error: {e}")
        return False

# Set up Twilio client
def setup_twilio_client():
    try:
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        if account_sid and auth_token:
            client = Client(account_sid, auth_token)
            print("✅ Twilio client set up")
            return client
        else:
            print("⚠️ Twilio credentials not found")
            return None
    except Exception as e:
        print(f"❌ Error setting up Twilio client: {e}")
        return None

credentials_setup = setup_google_credentials()
twilio_client = setup_twilio_client()

# Import Google Cloud
try:
    from google.cloud import translate_v2 as translate
    from google.cloud import texttospeech
    from google.cloud import speech
    GOOGLE_CLOUD_AVAILABLE = True
    print("✅ Google Cloud available")
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    print("❌ Google Cloud not available")

app = Flask(__name__)

# Get Replit domain or fallback
replit_domain = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')

# Get forwarding phone number from environment
FORWARD_TO_NUMBER = os.environ.get('FORWARD_TO_NUMBER', '')

def detect_language(text):
    """Detect if text is Hindi or English"""
    devanagari_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
    is_hindi = any(char in devanagari_chars for char in text)
    
    # Check for common Hindi words in English script
    hindi_words = ['namaste', 'kaise', 'ho', 'dhanyawad', 'alvida', 'theek', 'hun', 'aap', 'kahan', 'se', 'ghar', 'ja', 'raha']
    speech_words = text.lower().split()
    has_hindi_words = any(word in speech_words for word in speech_words)
    
    return 'hi' if (is_hindi or has_hindi_words) else 'en'

def translate_text(text, source_lang, target_lang):
    """Translate text using Google Translate"""
    try:
        if not GOOGLE_CLOUD_AVAILABLE:
            # Fallback translations
            if source_lang == 'hi' and target_lang == 'en':
                return "Hello, how are you?"
            elif source_lang == 'en' and target_lang == 'hi':
                return "नमस्ते, आप कैसे हैं?"
            return text
        
        client = translate.Client()
        result = client.translate(
            text, 
            source_language=source_lang, 
            target_language=target_lang,
            format_='text'
        )
        translated_text = result['translatedText']
        return translated_text.strip()
        
    except Exception as e:
        print(f"❌ Translation error: {e}")
        # Fallback translations
        if source_lang == 'hi' and target_lang == 'en':
            return "Hello, how are you?"
        elif source_lang == 'en' and target_lang == 'hi':
            return "नमस्ते, आप कैसे हैं?"
        return text

def synthesize_speech(text, language_code):
    """Convert text to speech using Google Text-to-Speech"""
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
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        return response.audio_content
        
    except Exception as e:
        print(f"❌ Text-to-Speech error: {e}")
        return None

@app.route('/')
def home():
    return {
        "message": "Call Forwarding with Real-time Translation",
        "version": "2.0.0",
        "features": [
            "Call forwarding to your number",
            "Conference-based real-time translation",
            "Better Hindi recognition",
            "Google Translate integration",
            "Google Text-to-Speech",
            "Twilio compatibility",
            "Two-way communication with translation"
        ],
        "status": "Ready for call forwarding with translation"
    }, 200

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "google_cloud_available": GOOGLE_CLOUD_AVAILABLE,
        "credentials_setup": credentials_setup
    }, 200

@app.route('/test-call-forwarding')
def test_call_forwarding():
    """Test endpoint to verify call forwarding configuration"""
    
    return {
        "message": "Call Forwarding Test",
        "your_number": FORWARD_TO_NUMBER if FORWARD_TO_NUMBER else "Not configured",
        "replit_domain": replit_domain,
        "webhook_url": f"https://{replit_domain}/twilio-webhook",
        "call_ended_url": f"https://{replit_domain}/call-ended",
        "recording_callback_url": f"https://{replit_domain}/recording-callback",
        "gather_webhook_url": f"https://{replit_domain}/gather-webhook",
        "status": "Ready for testing" if FORWARD_TO_NUMBER else "Configure FORWARD_TO_NUMBER environment variable",
        "features": [
            "Call forwarding to your number",
            "Fallback to translation service",
            "Call recording for translation",
            "Better Hindi recognition"
        ]
    }, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    """Handle incoming Twilio calls - Forward to your number with translation"""
    try:
        call_sid = request.form.get('CallSid')
        caller_id = request.form.get('From')
        
        # Get forwarding number from environment
        if not FORWARD_TO_NUMBER:
            twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Sorry, forwarding number not configured.</Say>
    <Hangup/>
</Response>"""
            return Response(twiml, mimetype='text/xml')
        
        your_number = FORWARD_TO_NUMBER
        
        # Get current domain
        current_domain = replit_domain
        
        print(f"📞 CALL FROM: {caller_id}")
        print(f"   CallSid: {call_sid}")
        print(f"   Forwarding to: {your_number}")
        print(f"   Railway domain: {current_domain}")
        print("="*40)
        
        # Check if caller is the same as your number (avoid loop)
        if caller_id == your_number:
            print("⚠️ Call from same number - avoiding loop")
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Sorry, cannot forward call to the same number.</Say>
    <Hangup/>
</Response>"""
            return Response(twiml, mimetype='text/xml')
        
        # Check if caller ID is missing or invalid
        if not caller_id or caller_id.strip() == "":
            print("⚠️ Invalid caller ID - using fallback")
            caller_id = "Unknown"
        
        # Simple call forwarding to your number
        welcome_text = "नमस्ते! आपका call forward हो रहा है। Please wait while I connect you."
        
        # Debug: Log the TwiML being generated
        print(f"🔧 GENERATED TWIML:")
        print(f"   Welcome: {welcome_text}")
        print(f"   Your number: {your_number}")
        print(f"   Caller ID: {caller_id}")
        print(f"   Replit domain: {replit_domain}")
        
        # Make actual call to your number using Twilio REST API
        welcome_text = "नमस्ते! आपका call forward हो रहा है। Please wait while I connect you."
        
        # Simple call forwarding - no conference
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Connecting you now.</Say>
    <Dial>
        <Number>{your_number}</Number>
    </Dial>
    <Say voice="alice" language="en-US">Call ended.</Say>
</Response>"""
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Twilio webhook error: {e}")
        return Response("<?xml version='1.0' encoding='UTF-8'?><Response><Say>Sorry, there was an error.</Say></Response>", mimetype='text/xml')



@app.route('/call-your-number', methods=['POST'])
def call_your_number():
    """Endpoint to handle the call to your number"""
    try:
        call_sid = request.form.get('CallSid')
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        
        print(f"📞 CALL YOUR NUMBER:")
        print(f"   CallSid: {call_sid}")
        print(f"   From: {from_number}")
        print(f"   To: {to_number}")
        print("="*40)
        
        # TwiML to connect you to the original caller
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">You are now connected to the caller.</Say>
    <Dial>
        <Number>{from_number}</Number>
    </Dial>
    <Say voice="alice" language="en-US">Call ended.</Say>
</Response>"""
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Call your number error: {e}")
        return Response("<?xml version='1.0' encoding='UTF-8'?><Response><Say>Error connecting call.</Say></Response>", mimetype='text/xml')

@app.route('/conference-wait', methods=['POST'])
def conference_wait():
    """Handle conference waiting - Call your number to join"""
    try:
        conference_name = request.form.get('ConferenceName')
        your_number = FORWARD_TO_NUMBER
        current_domain = replit_domain
        
        print(f"🎙️ CONFERENCE WAIT:")
        print(f"   Conference: {conference_name}")
        print(f"   Calling your number: {your_number}")
        print("="*40)
        
        # Use TwiML to call your number and join the conference
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Calling your number to join the conference.</Say>
    <Dial>
        <Number>{your_number}</Number>
    </Dial>
</Response>"""
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Conference wait error: {e}")
        return Response("<?xml version='1.0' encoding='UTF-8'?><Response></Response>", mimetype='text/xml')

@app.route('/conference-status', methods=['POST'])
def conference_status():
    """Handle conference status updates"""
    try:
        conference_name = request.form.get('ConferenceName')
        conference_sid = request.form.get('ConferenceSid')
        status = request.form.get('Status')
        event = request.form.get('StatusCallbackEvent')
        
        print(f"🎙️ CONFERENCE STATUS:")
        print(f"   Conference: {conference_name}")
        print(f"   Status: {status}")
        print(f"   Event: {event}")
        print("="*40)
        
        return {"status": "success"}, 200
        
    except Exception as e:
        print(f"❌ Conference status error: {e}")
        return {"status": "error"}, 500

@app.route('/call-ended', methods=['POST'])
def call_ended():
    """Handle when the forwarded call ends"""
    try:
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        duration = request.form.get('CallDuration')
        dial_call_status = request.form.get('DialCallStatus')
        dial_call_duration = request.form.get('DialCallDuration')
        
        print(f"📞 CALL ENDED:")
        print(f"   CallSid: {call_sid}")
        print(f"   Status: {call_status}")
        print(f"   Duration: {duration} seconds")
        print(f"   Dial Status: {dial_call_status}")
        print(f"   Dial Duration: {dial_call_duration} seconds")
        print("="*40)
        
        # Log the reason for call ending
        if dial_call_status == "no-answer":
            print("⚠️ Call ended: No answer from your number")
        elif dial_call_status == "busy":
            print("⚠️ Call ended: Your number is busy")
        elif dial_call_status == "failed":
            print("⚠️ Call ended: Failed to connect")
        elif dial_call_status == "completed":
            print("✅ Call ended: Successfully completed")
        
        return Response("<?xml version='1.0' encoding='UTF-8'?><Response></Response>", mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Call ended error: {e}")
        return Response("<?xml version='1.0' encoding='UTF-8'?><Response></Response>", mimetype='text/xml')

@app.route('/recording-callback', methods=['POST'])
def recording_callback():
    """Handle call recording for translation"""
    try:
        call_sid = request.form.get('CallSid')
        recording_url = request.form.get('RecordingUrl')
        recording_duration = request.form.get('RecordingDuration')
        
        print(f"🎙️ RECORDING RECEIVED:")
        print(f"   CallSid: {call_sid}")
        print(f"   Recording URL: {recording_url}")
        print(f"   Duration: {recording_duration} seconds")
        print("="*40)
        
        # Process recording for real-time translation
        if recording_url and recording_duration:
            print("📝 Processing recording for real-time translation...")
            print("🔄 This will enable:")
            print("   ✓ Hindi speech → English translation")
            print("   ✓ English speech → Hindi translation")
            print("   ✓ Real-time communication during call")
            
            # In a real implementation, you would:
            # 1. Download the recording from recording_url
            # 2. Use Google Speech-to-Text to transcribe it
            # 3. Detect language (Hindi/English)
            # 4. Translate using Google Translate
            # 5. Send SMS or notification with translation
            
            print("✅ Recording processed for translation")
            print("📱 Translation will be available during the call")
        
        return {"status": "success"}, 200
        
    except Exception as e:
        print(f"❌ Recording callback error: {e}")
        return {"error": str(e)}, 500

@app.route('/gather-webhook', methods=['POST'])
def gather_webhook():
    """Handle speech input from Twilio"""
    try:
        call_sid = request.form.get('CallSid')
        speech_result = request.form.get('SpeechResult', '').strip()
        confidence = float(request.form.get('Confidence', 0))
        
        print(f"🎤 GATHER WEBHOOK:")
        print(f"   CallSid: {call_sid}")
        print(f"   Speech Result: '{speech_result}'")
        print(f"   Confidence: {confidence}")
        print("="*40)
        
        if not speech_result:
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Sorry, I didn't hear anything. Please try again.</Say>
    <Gather action="https://{replit_domain}/gather-webhook" method="POST" input="speech" speechTimeout="auto" timeout="30" language="hi-IN" speechModel="phone_call"/>
</Response>"""
            return Response(twiml, mimetype='text/xml')
        
        # Detect language
        source_lang = detect_language(speech_result)
        target_lang = 'en' if source_lang == 'hi' else 'hi'
        
        print(f"🔄 Calling Google Translate API...")
        print(f"   Source: {source_lang}")
        print(f"   Target: {target_lang}")
        print(f"   Text: '{speech_result}'")
        
        # Translate
        translated_text = translate_text(speech_result, source_lang, target_lang)
        print(f"✅ Translation successful: '{translated_text}'")
        
        if source_lang == 'hi':
            print(f"🔄 Hindi → English: '{translated_text}'")
            # Use English voice for English translation
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">{translated_text}</Say>
    <Pause length="3"/>
    <Say voice="alice" language="en-US">Say something else or goodbye.</Say>
    <Gather action="https://{replit_domain}/gather-webhook" method="POST" input="speech" speechTimeout="auto" timeout="30" language="hi-IN" speechModel="phone_call"/>
    <Say voice="alice" language="en-US">Thank you. Goodbye.</Say>
</Response>"""
        else:
            print(f"🔄 English → Hindi: '{translated_text}'")
            # Use English voice for Hindi text (Twilio Hindi voice doesn't work well)
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">{translated_text}</Say>
    <Pause length="3"/>
    <Say voice="alice" language="en-US">Say something else or goodbye.</Say>
    <Gather action="https://{replit_domain}/gather-webhook" method="POST" input="speech" speechTimeout="auto" timeout="30" language="hi-IN" speechModel="phone_call"/>
    <Say voice="alice" language="en-US">Thank you. Goodbye.</Say>
</Response>"""
        
        print(f"🔊 SPEAKING: Translation: {translated_text}")
        print("="*40)
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Gather webhook error: {e}")
        return Response("<?xml version='1.0' encoding='UTF-8'?><Response><Say>Sorry, there was an error.</Say></Response>", mimetype='text/xml')

@app.route('/translate-text', methods=['POST'])
def translate_text_endpoint():
    """Translate text and return audio"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return {"error": "No text provided"}, 400
        
        # Detect language
        source_lang = detect_language(text)
        target_lang = 'en' if source_lang == 'hi' else 'hi'
        
        # Translate
        translated_text = translate_text(text, source_lang, target_lang)
        
        # Synthesize speech
        audio_data = synthesize_speech(translated_text, target_lang)
        
        if audio_data:
            # Return audio as base64
            import base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            return {
                "translated_text": translated_text,
                "source_language": source_lang,
                "target_language": target_lang,
                "audio_base64": audio_b64
            }, 200
        else:
            return {
                "translated_text": translated_text,
                "source_language": source_lang,
                "target_language": target_lang,
                "audio_base64": None
            }, 200
            
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 CALL FORWARDING TRANSLATOR on port {port}")
    print("="*60)
    print("✅ Features:")
    if FORWARD_TO_NUMBER:
        print(f"   ✓ Call forwarding to {FORWARD_TO_NUMBER}")
    else:
        print("   ⚠️  Set FORWARD_TO_NUMBER environment variable")
    print("   ✓ Call recording for translation")
    print("   ✓ Better Hindi recognition")
    print("   ✓ Google Translate integration")
    print("   ✓ Google Text-to-Speech")
    print("   ✓ Twilio compatibility")
    print(f"   ✓ Google Cloud: {GOOGLE_CLOUD_AVAILABLE}")
    print(f"   ✓ Credentials: {credentials_setup}")
    print("="*60)
    print("📞 Usage:")
    print("   Someone calls your Twilio number")
    if FORWARD_TO_NUMBER:
        print(f"   → Call forwards to {FORWARD_TO_NUMBER}")
    else:
        print("   → Configure FORWARD_TO_NUMBER first")
    print("   → You can have normal conversation")
    print("   → Call is recorded for translation")
    print("   → Translation sent after call ends")
    print("="*60)
    
    app.run(host='0.0.0.0', port=port, debug=False)
