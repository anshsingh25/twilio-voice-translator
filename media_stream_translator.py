#!/usr/bin/env python3
"""
Real-time Bidirectional Voice Translator with Twilio Media Streams
Handles audio streaming, transcription, translation, and TTS in real-time
"""

import os
import json
import base64
import asyncio
import audioop
from collections import defaultdict
from datetime import datetime
from flask import Flask, request, Response
from flask_sock import Sock
from google.cloud import speech_v1 as speech
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech
from twilio.rest import Client

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-credentials.json'

app = Flask(__name__)
sock = Sock(app)

# Configuration
FORWARD_TO_NUMBER = os.environ.get('FORWARD_TO_NUMBER', '')
railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
replit_domain = os.environ.get('REPLIT_DEV_DOMAIN')
app_domain = railway_domain or replit_domain or 'localhost:5000'

# Google Cloud clients
speech_client = speech.SpeechClient()
translate_client = translate.Client()
tts_client = texttospeech.TextToSpeechClient()

# Twilio client
twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_client = Client(twilio_account_sid, twilio_auth_token) if twilio_account_sid and twilio_auth_token else None

# Active streams storage
active_streams = {}
call_participants = defaultdict(dict)

@app.route('/')
def home():
    return {
        "message": "Real-time Bidirectional Voice Translator",
        "version": "4.0.0 - Media Streams",
        "status": "Ready",
        "features": [
            "Real-time English → Hindi translation",
            "Real-time Hindi → English translation",
            "Twilio Media Streams",
            "Google Cloud AI"
        ]
    }, 200

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "active_streams": len(active_streams),
        "forward_to": FORWARD_TO_NUMBER if FORWARD_TO_NUMBER else "not configured"
    }, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    """Handle incoming calls with Media Streams"""
    
    if not FORWARD_TO_NUMBER:
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Sorry, forwarding number not configured.</Say>
    <Hangup/>
</Response>"""
        return Response(twiml, mimetype='text/xml')
    
    call_sid = request.form.get('CallSid')
    caller = request.form.get('From')
    to_number = request.form.get('To')
    
    print(f"\n{'='*60}")
    print(f"📞 INCOMING CALL")
    print(f"   From: {caller}")
    print(f"   To: {to_number}")
    print(f"   CallSid: {call_sid}")
    print(f"{'='*60}\n")
    
    # Store caller as "English speaker" in this call
    call_participants[call_sid] = {
        'caller': caller,
        'caller_language': 'en',  # Caller speaks English
        'receiver_language': 'hi'  # You speak Hindi
    }
    
    # Connect caller and start Media Stream
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Connecting you with real-time translation. Please wait.</Say>
    <Start>
        <Stream url="wss://{app_domain}/media-stream/{call_sid}/caller" />
    </Start>
    <Dial action="https://{app_domain}/call-ended" callerId="{to_number}">
        <Number url="https://{app_domain}/receiver-connected/{call_sid}">{FORWARD_TO_NUMBER}</Number>
    </Dial>
</Response>"""
    
    print(f"✅ TwiML sent for caller")
    print(f"   Stream URL: wss://{app_domain}/media-stream/{call_sid}/caller\n")
    
    return Response(twiml, mimetype='text/xml')

@app.route('/receiver-connected/<call_sid>', methods=['POST'])
def receiver_connected(call_sid):
    """Handle when receiver (you) picks up"""
    
    print(f"\n{'='*60}")
    print(f"📱 RECEIVER CONNECTED")
    print(f"   CallSid: {call_sid}")
    print(f"{'='*60}\n")
    
    # Start Media Stream for receiver too
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="hi-IN">आप कॉल से जुड़ गए हैं। Translation चालू है।</Say>
    <Start>
        <Stream url="wss://{app_domain}/media-stream/{call_sid}/receiver" />
    </Start>
    <Pause length="3600"/>
</Response>"""
    
    print(f"✅ TwiML sent for receiver")
    print(f"   Stream URL: wss://{app_domain}/media-stream/{call_sid}/receiver\n")
    
    return Response(twiml, mimetype='text/xml')

@app.route('/call-ended', methods=['POST'])
def call_ended():
    """Handle call end"""
    call_sid = request.form.get('CallSid')
    
    print(f"\n{'='*60}")
    print(f"📞 CALL ENDED")
    print(f"   CallSid: {call_sid}")
    print(f"{'='*60}\n")
    
    # Clean up
    if call_sid in call_participants:
        del call_participants[call_sid]
    
    return Response('', mimetype='text/xml')

def detect_language(text):
    """Detect if text is Hindi or English"""
    if not text:
        return 'en'
    
    # Check for Devanagari characters
    devanagari_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
    if any(char in devanagari_chars for char in text):
        return 'hi'
    
    # Check for common Hindi words in English script
    hindi_words = ['namaste', 'kaise', 'ho', 'theek', 'hun', 'aap', 'kya', 'hai', 'haan', 'nahi']
    words = text.lower().split()
    if any(word in hindi_words for word in words):
        return 'hi'
    
    return 'en'

def translate_text(text, source_lang, target_lang):
    """Translate text between languages"""
    if not text or source_lang == target_lang:
        return text
    
    try:
        result = translate_client.translate(
            text,
            source_language=source_lang,
            target_language=target_lang
        )
        translated = result['translatedText']
        print(f"   🔄 Translated ({source_lang}→{target_lang}): {text[:50]}... → {translated[:50]}...")
        return translated
    except Exception as e:
        print(f"   ❌ Translation error: {e}")
        return text

def synthesize_speech_audio(text, language_code):
    """Convert text to speech and return audio bytes"""
    try:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Voice configuration based on language
        if language_code == 'hi':
            voice = texttospeech.VoiceSelectionParams(
                language_code="hi-IN",
                name="hi-IN-Neural2-A",
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
        else:
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Neural2-C",
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
        
        # Audio configuration - mulaw for Twilio
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MULAW,
            sample_rate_hertz=8000
        )
        
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        return response.audio_content
    except Exception as e:
        print(f"   ❌ TTS error: {e}")
        return None

@sock.route('/media-stream/<call_sid>/<participant>')
def media_stream(ws, call_sid, participant):
    """Handle Twilio Media Streams for real-time audio processing"""
    
    stream_sid = None
    audio_buffer = bytearray()
    last_transcript = ""
    last_speech_time = datetime.now()
    
    print(f"\n{'='*60}")
    print(f"🔌 WebSocket CONNECTED")
    print(f"   CallSid: {call_sid}")
    print(f"   Participant: {participant}")
    print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Store stream reference
    stream_key = f"{call_sid}_{participant}"
    active_streams[stream_key] = {
        'ws': ws,
        'participant': participant,
        'call_sid': call_sid,
        'connected_at': datetime.now()
    }
    
    try:
        while True:
            message = ws.receive()
            if message is None:
                break
            
            data = json.loads(message)
            event = data.get('event')
            
            if event == 'connected':
                print(f"✅ Stream connected for {participant}")
                
            elif event == 'start':
                stream_sid = data['start']['streamSid']
                print(f"🎤 Stream started: {stream_sid}")
                active_streams[stream_key]['stream_sid'] = stream_sid
                
            elif event == 'media':
                # Receive audio payload (mulaw, base64 encoded)
                payload = data['media']['payload']
                audio_chunk = base64.b64decode(payload)
                audio_buffer.extend(audio_chunk)
                
                # Process when buffer reaches ~2 seconds (16000 bytes at 8kHz)
                if len(audio_buffer) >= 16000:
                    try:
                        # Convert mulaw to linear PCM for Google Speech-to-Text
                        audio_pcm = audioop.ulaw2lin(bytes(audio_buffer), 2)
                        
                        # Transcribe with Google Speech-to-Text
                        audio_content = speech.RecognitionAudio(content=audio_pcm)
                        config = speech.RecognitionConfig(
                            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                            sample_rate_hertz=8000,
                            language_code="hi-IN" if participant == "receiver" else "en-US",
                            alternative_language_codes=["en-US"] if participant == "receiver" else ["hi-IN"],
                            enable_automatic_punctuation=True,
                        )
                        
                        response = speech_client.recognize(config=config, audio=audio_content)
                        
                        for result in response.results:
                            transcript = result.alternatives[0].transcript
                            confidence = result.alternatives[0].confidence
                            
                            if confidence > 0.7 and transcript != last_transcript:
                                print(f"\n🎤 {participant.upper()} spoke: {transcript}")
                                last_transcript = transcript
                                last_speech_time = datetime.now()
                                
                                # Detect language
                                detected_lang = detect_language(transcript)
                                
                                # Determine target language
                                if participant == "caller":
                                    # Caller speaks English → translate to Hindi for receiver
                                    target_lang = "hi"
                                else:
                                    # Receiver speaks Hindi → translate to English for caller
                                    target_lang = "en"
                                
                                # Translate
                                translated_text = translate_text(transcript, detected_lang, target_lang)
                                
                                # Synthesize speech
                                audio_output = synthesize_speech_audio(translated_text, target_lang)
                                
                                if audio_output:
                                    # Send audio to the OTHER participant
                                    target_participant = "receiver" if participant == "caller" else "caller"
                                    target_stream_key = f"{call_sid}_{target_participant}"
                                    
                                    if target_stream_key in active_streams:
                                        target_ws = active_streams[target_stream_key]['ws']
                                        
                                        # Encode audio for Twilio (already in mulaw from TTS)
                                        audio_base64 = base64.b64encode(audio_output).decode('utf-8')
                                        
                                        # Send media message
                                        media_message = {
                                            "event": "media",
                                            "streamSid": active_streams[target_stream_key].get('stream_sid'),
                                            "media": {
                                                "payload": audio_base64
                                            }
                                        }
                                        
                                        try:
                                            target_ws.send(json.dumps(media_message))
                                            print(f"   🔊 Sent translation to {target_participant}")
                                        except Exception as e:
                                            print(f"   ❌ Error sending audio: {e}")
                    
                    except Exception as e:
                        print(f"   ❌ Processing error: {e}")
                    
                    # Clear buffer
                    audio_buffer = bytearray()
            
            elif event == 'stop':
                print(f"⏹️  Stream stopped: {stream_sid}")
                break
                
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    
    finally:
        # Clean up
        if stream_key in active_streams:
            del active_streams[stream_key]
        
        print(f"\n{'='*60}")
        print(f"🔌 WebSocket DISCONNECTED")
        print(f"   CallSid: {call_sid}")
        print(f"   Participant: {participant}")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*60}")
    print(f"🚀 REAL-TIME TRANSLATOR WITH MEDIA STREAMS")
    print(f"{'='*60}")
    print(f"Port: {port}")
    print(f"Domain: {app_domain}")
    print(f"Forward to: {FORWARD_TO_NUMBER}")
    print(f"Webhook: https://{app_domain}/twilio-webhook")
    print(f"{'='*60}")
    print(f"📞 Features:")
    print(f"   ✓ Real-time English → Hindi translation")
    print(f"   ✓ Real-time Hindi → English translation")
    print(f"   ✓ Twilio Media Streams")
    print(f"   ✓ Google Cloud AI")
    print(f"{'='*60}\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)
