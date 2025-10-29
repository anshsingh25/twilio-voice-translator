#!/usr/bin/env python3
"""
Real-time Bidirectional Voice Translator with Twilio Media Streams
Uses conference call architecture to inject translated audio
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
import threading
import time

# Load Google credentials from environment
google_creds_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
if google_creds_json:
    with open('google-credentials.json', 'w') as f:
        f.write(google_creds_json)
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

# Active streams and conference participants
active_streams = {}
conference_participants = defaultdict(dict)

@app.route('/')
def home():
    return {
        "message": "Real-time Bidirectional Voice Translator",
        "version": "5.0.0 - Conference Mode",
        "status": "Ready",
        "features": [
            "Real-time English → Hindi translation",
            "Real-time Hindi → English translation",
            "Twilio Conferences",
            "Google Cloud AI"
        ]
    }, 200

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "active_conferences": len(conference_participants),
        "forward_to": FORWARD_TO_NUMBER if FORWARD_TO_NUMBER else "not configured"
    }, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    """Handle incoming calls - put caller in conference"""
    
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
    
    # Create unique conference name
    conference_name = f"translator-{call_sid}"
    
    # Initialize conference tracking
    conference_participants[conference_name] = {
        'caller': {'call_sid': call_sid, 'number': caller, 'language': 'en'},
        'receiver': {'number': FORWARD_TO_NUMBER, 'language': 'hi'},
        'conference_sid': None
    }
    
    # Put caller in muted conference and start Media Stream
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Connecting you with real-time translation.</Say>
    <Start>
        <Stream url="wss://{app_domain}/media-stream/{conference_name}/caller" />
    </Start>
    <Dial>
        <Conference 
            muted="true"
            startConferenceOnEnter="true"
            endConferenceOnExit="true"
            statusCallback="https://{app_domain}/conference-status"
            statusCallbackEvent="start end join leave"
            statusCallbackMethod="POST">{conference_name}</Conference>
    </Dial>
</Response>"""
    
    print(f"✅ TwiML sent for caller")
    print(f"   Conference: {conference_name}")
    print(f"   Stream URL: wss://{app_domain}/media-stream/{conference_name}/caller\n")
    
    # Dial the receiver in a separate thread
    threading.Thread(target=dial_receiver, args=(conference_name, call_sid, to_number)).start()
    
    return Response(twiml, mimetype='text/xml')

def dial_receiver(conference_name, caller_call_sid, caller_number):
    """Dial the receiver and add them to the conference"""
    time.sleep(2)  # Wait for caller to join conference
    
    print(f"\n📞 Dialing receiver for conference: {conference_name}\n")
    
    try:
        # Create call to receiver
        call = twilio_client.calls.create(
            to=FORWARD_TO_NUMBER,
            from_=caller_number,
            url=f'https://{app_domain}/receiver-twiml/{conference_name}',
            status_callback=f'https://{app_domain}/call-status',
            status_callback_event=['answered', 'completed']
        )
        
        conference_participants[conference_name]['receiver']['call_sid'] = call.sid
        print(f"✅ Receiver call initiated: {call.sid}\n")
        
    except Exception as e:
        print(f"❌ Error dialing receiver: {e}\n")

@app.route('/receiver-twiml/<conference_name>', methods=['POST'])
def receiver_twiml(conference_name):
    """TwiML for receiver - join conference with Media Stream"""
    
    print(f"\n{'='*60}")
    print(f"📱 RECEIVER ANSWERED")
    print(f"   Conference: {conference_name}")
    print(f"{'='*60}\n")
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="hi-IN">आप कॉल से जुड़ गए हैं। Translation चालू है।</Say>
    <Start>
        <Stream url="wss://{app_domain}/media-stream/{conference_name}/receiver" />
    </Start>
    <Dial>
        <Conference muted="true">{conference_name}</Conference>
    </Dial>
</Response>"""
    
    print(f"✅ TwiML sent for receiver")
    print(f"   Stream URL: wss://{app_domain}/media-stream/{conference_name}/receiver\n")
    
    return Response(twiml, mimetype='text/xml')

@app.route('/conference-status', methods=['POST'])
def conference_status():
    """Track conference events and cleanup resources"""
    event = request.form.get('StatusCallbackEvent')
    conference_sid = request.form.get('ConferenceSid')
    conference_name = request.form.get('FriendlyName')
    call_sid = request.form.get('CallSid')
    
    print(f"📊 Conference {event}: {conference_name} (SID: {conference_sid})")
    
    if conference_name in conference_participants:
        conference_participants[conference_name]['conference_sid'] = conference_sid
        
        if event == 'participant-join':
            participant_sid = request.form.get('ParticipantSid')  # Use ParticipantSid, not CallSid
            print(f"   👤 Participant joined: {call_sid} (ParticipantSid: {participant_sid})")
            
            # Update participant SID
            if call_sid == conference_participants[conference_name]['caller']['call_sid']:
                conference_participants[conference_name]['caller']['participant_sid'] = participant_sid
                print(f"   ✅ Stored caller participant_sid: {participant_sid}")
            elif 'call_sid' in conference_participants[conference_name]['receiver'] and call_sid == conference_participants[conference_name]['receiver']['call_sid']:
                conference_participants[conference_name]['receiver']['participant_sid'] = participant_sid
                print(f"   ✅ Stored receiver participant_sid: {participant_sid}")
        
        elif event == 'conference-end':
            print(f"🧹 Cleaning up conference: {conference_name}")
            
            # Delete all TTS audio files for this conference
            if 'audio_files' in conference_participants[conference_name]:
                for filepath in conference_participants[conference_name]['audio_files']:
                    try:
                        if os.path.exists(filepath):
                            os.remove(filepath)
                            print(f"   🗑️  Deleted: {filepath}")
                    except Exception as e:
                        print(f"   ⚠️  Could not delete {filepath}: {e}")
            
            # Remove conference tracking data
            del conference_participants[conference_name]
            print(f"   ✅ Conference cleanup complete")
    
    return Response('', mimetype='text/xml')

@app.route('/call-status', methods=['POST'])
def call_status():
    """Track call status"""
    return Response('', mimetype='text/xml')

def detect_language(text):
    """Detect if text is Hindi or English"""
    if not text:
        return 'en'
    
    # Check for Devanagari characters
    devanagari_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
    if any(char in devanagari_chars for char in text):
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
        return translated
    except Exception as e:
        print(f"   ❌ Translation error: {e}")
        return text

def synthesize_speech_url(text, language_code, conference_name):
    """Generate TTS audio and save to temporary file, return filename"""
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
        
        # Audio configuration - MP3 for better quality and size
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save to file
        timestamp = int(time.time() * 1000)
        filename = f"tts_{timestamp}.mp3"
        filepath = f"static/{filename}"
        
        # Create static directory if it doesn't exist
        os.makedirs('static', exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(response.audio_content)
        
        # Track file for cleanup
        if conference_name in conference_participants:
            if 'audio_files' not in conference_participants[conference_name]:
                conference_participants[conference_name]['audio_files'] = []
            conference_participants[conference_name]['audio_files'].append(filepath)
        
        # Return filename only
        return filename
    except Exception as e:
        print(f"   ❌ TTS error: {e}")
        return None

def play_audio_to_participant(conference_sid, participant_sid, audio_filename):
    """Play audio to a specific conference participant using announce_url"""
    try:
        # Use the Conference Participant API to play audio
        # announce_url needs to point to a TwiML endpoint
        announce_twiml_url = f"https://{app_domain}/play-tts/{audio_filename}"
        
        twilio_client.conferences(conference_sid).participants(participant_sid).update(
            announce_url=announce_twiml_url,
            announce_method='GET'
        )
        print(f"   🔊 Playing audio to participant {participant_sid}")
        return True
    except Exception as e:
        print(f"   ❌ Error playing audio: {e}")
        return False

@sock.route('/media-stream/<conference_name>/<participant_role>')
def media_stream(ws, conference_name, participant_role):
    """Handle Twilio Media Streams for real-time audio processing"""
    
    stream_sid = None
    audio_buffer = bytearray()
    last_transcript = ""
    
    print(f"\n{'='*60}")
    print(f"🔌 WebSocket CONNECTED")
    print(f"   Conference: {conference_name}")
    print(f"   Role: {participant_role}")
    print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        while True:
            message = ws.receive()
            if message is None:
                break
            
            data = json.loads(message)
            event = data.get('event')
            
            if event == 'connected':
                print(f"✅ Stream connected for {participant_role}")
                
            elif event == 'start':
                stream_sid = data['start']['streamSid']
                print(f"🎤 Stream started: {stream_sid}")
                
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
                        
                        # Determine language based on participant role
                        if participant_role == "caller":
                            primary_lang = "en-US"
                            alt_langs = ["hi-IN", "en-IN"]
                        else:  # receiver
                            primary_lang = "hi-IN"
                            alt_langs = ["en-US", "en-IN"]
                        
                        # Transcribe with Google Speech-to-Text
                        audio_content = speech.RecognitionAudio(content=audio_pcm)
                        config = speech.RecognitionConfig(
                            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                            sample_rate_hertz=8000,
                            language_code=primary_lang,
                            alternative_language_codes=alt_langs,
                            enable_automatic_punctuation=True,
                            model="latest_short"
                        )
                        
                        response = speech_client.recognize(config=config, audio=audio_content)
                        
                        for result in response.results:
                            transcript = result.alternatives[0].transcript.strip()
                            confidence = result.alternatives[0].confidence
                            
                            if confidence > 0.6 and transcript and transcript != last_transcript:
                                print(f"\n🎤 {participant_role.upper()} spoke: {transcript} (confidence: {confidence:.2f})")
                                last_transcript = transcript
                                
                                # Detect language
                                detected_lang = detect_language(transcript)
                                print(f"   🔍 Detected language: {detected_lang}")
                                
                                # Determine target language and participant
                                if participant_role == "caller":
                                    target_lang = "hi"
                                    target_role = "receiver"
                                else:
                                    target_lang = "en"
                                    target_role = "caller"
                                
                                # Translate
                                translated_text = translate_text(transcript, detected_lang, target_lang)
                                print(f"   🔄 Translated to {target_lang}: {translated_text}")
                                
                                # Generate TTS audio file
                                audio_filename = synthesize_speech_url(translated_text, target_lang, conference_name)
                                
                                if audio_filename and conference_name in conference_participants:
                                    conf_info = conference_participants[conference_name]
                                    conference_sid = conf_info.get('conference_sid')
                                    target_participant = conf_info.get(target_role, {})
                                    target_participant_sid = target_participant.get('participant_sid')
                                    
                                    if conference_sid and target_participant_sid:
                                        # Play translated audio to the other participant
                                        play_audio_to_participant(conference_sid, target_participant_sid, audio_filename)
                                        print(f"   ✅ Translation delivered to {target_role}")
                                    else:
                                        print(f"   ⚠️  Target participant not ready yet")
                    
                    except Exception as e:
                        print(f"   ❌ Processing error: {e}")
                        import traceback
                        traceback.print_exc()
                    
                    # Clear buffer
                    audio_buffer = bytearray()
            
            elif event == 'stop':
                print(f"⏹️  Stream stopped: {stream_sid}")
                break
                
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print(f"\n{'='*60}")
        print(f"🔌 WebSocket DISCONNECTED")
        print(f"   Conference: {conference_name}")
        print(f"   Role: {participant_role}")
        print(f"{'='*60}\n")

# Serve TwiML endpoint for playing TTS audio
@app.route('/play-tts/<filename>')
def play_tts(filename):
    """Return TwiML to play TTS audio file"""
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>https://{app_domain}/static/{filename}</Play>
</Response>"""
    return Response(twiml, mimetype='text/xml')

# Serve static files for TTS audio
@app.route('/static/<filename>')
def serve_static(filename):
    from flask import send_from_directory
    return send_from_directory('static', filename)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*60}")
    print(f"🚀 REAL-TIME TRANSLATOR WITH CONFERENCE MODE")
    print(f"{'='*60}")
    print(f"Port: {port}")
    print(f"Domain: {app_domain}")
    print(f"Forward to: {FORWARD_TO_NUMBER}")
    print(f"Webhook: https://{app_domain}/twilio-webhook")
    print(f"{'='*60}")
    print(f"📞 Features:")
    print(f"   ✓ Real-time English → Hindi translation")
    print(f"   ✓ Real-time Hindi → English translation")
    print(f"   ✓ Twilio Conferences")
    print(f"   ✓ Google Cloud AI")
    print(f"{'='*60}\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)
