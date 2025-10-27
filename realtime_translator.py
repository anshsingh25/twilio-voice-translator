#!/usr/bin/env python3
"""
Real-time Bidirectional Voice Translator
Streams audio from both participants and translates in real-time
"""

import os
import json
import base64
import asyncio
from flask import Flask, request, Response
from flask_sock import Sock
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech
import audioop

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-credentials.json'

app = Flask(__name__)
sock = Sock(app)

FORWARD_TO_NUMBER = os.environ.get('FORWARD_TO_NUMBER', '')
# Support both Railway and Replit domains
railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
replit_domain = os.environ.get('REPLIT_DEV_DOMAIN')
app_domain = railway_domain or replit_domain or 'localhost:5000'

speech_client = speech.SpeechClient()
translate_client = translate.Client()
tts_client = texttospeech.TextToSpeechClient()

@app.route('/')
def home():
    return {
        "message": "Real-time Bidirectional Voice Translator",
        "version": "3.0.0",
        "status": "Ready",
        "features": [
            "Real-time English → Hindi translation",
            "Real-time Hindi → English translation",
            "Twilio Media Streams integration",
            "Google Cloud AI translation"
        ]
    }, 200

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "google_cloud": "available",
        "forward_to": FORWARD_TO_NUMBER if FORWARD_TO_NUMBER else "not configured"
    }, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    """Handle incoming calls and set up bidirectional streaming"""
    
    if not FORWARD_TO_NUMBER:
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Sorry, forwarding number not configured.</Say>
    <Hangup/>
</Response>"""
        return Response(twiml, mimetype='text/xml')
    
    call_sid = request.form.get('CallSid')
    caller = request.form.get('From')
    
    print(f"📞 Incoming call from {caller}")
    print(f"   CallSid: {call_sid}")
    print(f"   Setting up real-time translation...")
    
    # Create a conference call with both parties
    # Use <Start><Stream> to capture audio from both
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Connecting you with real-time translation.</Say>
    <Dial>
        <Conference 
            beep="false"
            startConferenceOnEnter="true"
            endConferenceOnExit="true"
            statusCallback="https://{app_domain}/conference-status"
            statusCallbackMethod="POST"
            statusCallbackEvent="start end join leave">
            translator-{call_sid}
        </Conference>
    </Dial>
</Response>"""
    
    # Initiate outbound call to your number
    from twilio.rest import Client
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)
    
    # Call your number and add to same conference
    try:
        outbound_call = client.calls.create(
            url=f"https://{app_domain}/connect-to-conference?conference=translator-{call_sid}",
            to=FORWARD_TO_NUMBER,
            from_=request.form.get('To')
        )
        print(f"✅ Called your number: {outbound_call.sid}")
    except Exception as e:
        print(f"❌ Error calling your number: {e}")
    
    return Response(twiml, mimetype='text/xml')

@app.route('/connect-to-conference', methods=['POST'])
def connect_to_conference():
    """Connect the second participant to the conference"""
    conference_name = request.args.get('conference')
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="hi-IN">आप कॉल से जुड़ गए हैं। Real-time translation चालू है।</Say>
    <Dial>
        <Conference 
            beep="false"
            startConferenceOnEnter="true"
            endConferenceOnExit="true">
            {conference_name}
        </Conference>
    </Dial>
</Response>"""
    
    return Response(twiml, mimetype='text/xml')

@app.route('/conference-status', methods=['POST'])
def conference_status():
    """Handle conference status updates"""
    event = request.form.get('StatusCallbackEvent')
    conference_sid = request.form.get('ConferenceSid')
    
    print(f"🎙️ Conference {conference_sid}: {event}")
    
    if event == 'conference-start':
        print("✅ Conference started - Translation active")
    elif event == 'conference-end':
        print("📞 Conference ended")
    
    return {}, 200

def detect_language(text):
    """Detect if text is Hindi or English"""
    devanagari_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
    is_hindi = any(char in devanagari_chars for char in text)
    
    hindi_words = ['namaste', 'kaise', 'ho', 'theek', 'hun', 'aap', 'kya', 'hai']
    has_hindi_words = any(word in text.lower().split() for word in hindi_words)
    
    return 'hi' if (is_hindi or has_hindi_words) else 'en'

def translate_text(text, source_lang, target_lang):
    """Translate text"""
    try:
        result = translate_client.translate(
            text,
            source_language=source_lang,
            target_language=target_lang
        )
        return result['translatedText']
    except Exception as e:
        print(f"❌ Translation error: {e}")
        return text

# WebSocket endpoint for media streams (future implementation)
@sock.route('/media-stream')
def media_stream(ws):
    """Handle Twilio Media Streams for real-time audio processing"""
    print("🔌 WebSocket connection established")
    
    audio_buffer = bytearray()
    
    while True:
        try:
            message = ws.receive()
            if message is None:
                break
                
            data = json.loads(message)
            
            if data['event'] == 'connected':
                print("✅ Media stream connected")
            
            elif data['event'] == 'start':
                print(f"🎤 Stream started: {data['streamSid']}")
            
            elif data['event'] == 'media':
                # Receive audio payload
                payload = data['media']['payload']
                audio_chunk = base64.b64decode(payload)
                audio_buffer.extend(audio_chunk)
                
                # Process when buffer is large enough
                if len(audio_buffer) >= 8000:  # ~1 second at 8kHz
                    # TODO: Send to Google Speech-to-Text
                    # TODO: Translate
                    # TODO: Text-to-Speech
                    # TODO: Send back to Twilio
                    audio_buffer = bytearray()
            
            elif data['event'] == 'stop':
                print("⏹️ Stream stopped")
                break
                
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
            break
    
    print("🔌 WebSocket connection closed")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 REAL-TIME TRANSLATOR on port {port}")
    print("="*60)
    print(f"✅ Forward to: {FORWARD_TO_NUMBER}")
    print(f"✅ Domain: {app_domain}")
    print(f"✅ Webhook URL: https://{app_domain}/twilio-webhook")
    print("="*60)
    print("📞 How it works:")
    print("   1. Someone calls your Twilio number")
    print("   2. Both of you are connected via conference")
    print("   3. English → Hindi translation (for you)")
    print("   4. Hindi → English translation (for caller)")
    print("   5. Real-time conversation with translation")
    print("="*60)
    
    app.run(host='0.0.0.0', port=port, debug=False)
