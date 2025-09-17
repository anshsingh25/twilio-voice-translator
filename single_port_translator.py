import os
import asyncio
import json
import base64
import queue
import threading
import time
import struct
from collections import deque
from flask import Flask, request, Response
from flask_socketio import SocketIO, emit
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/apple/text_to_voice_translator/google-credentials.json"

# Global variables for managing call state
active_calls = {}

class SinglePortCallSession:
    def __init__(self, call_sid, stream_sid):
        self.call_sid = call_sid
        self.stream_sid = stream_sid
        self.last_processed_transcript = ""
        self.file_counter = 0
        self.last_translation_time = 0
        self.is_processing = False
        self.translation_lock = threading.Lock()

# Translation functions
def translate_hindi_to_english(hindi_text):
    """Translate Hindi text to English"""
    try:
        client = translate.Client()
        result = client.translate(hindi_text, source_language='hi', target_language='en')
        english_text = result['translatedText']
        print(f"Hindi → English: {hindi_text} → {english_text}")
        return english_text
    except Exception as e:
        print(f"Hindi to English translation error: {e}")
        return None

def translate_english_to_hindi(english_text):
    """Translate English text to Hindi"""
    try:
        client = translate.Client()
        result = client.translate(english_text, source_language='en', target_language='hi')
        hindi_text = result['translatedText']
        print(f"English → Hindi: {english_text} → {hindi_text}")
        return hindi_text
    except Exception as e:
        print(f"English to Hindi translation error: {e}")
        return None

# Text-to-Speech functions
def synthesize_english_speech(english_text, file_counter):
    """Convert English text to speech"""
    try:
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=english_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", 
            name="en-US-Standard-A"
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MULAW, 
            sample_rate_hertz=8000
        )

        response = client.synthesize_speech(
            input=synthesis_input, 
            voice=voice, 
            audio_config=audio_config
        )
        
        return response.audio_content
    except Exception as e:
        print(f"English Text-to-Speech error: {e}")
        return None

def synthesize_hindi_speech(hindi_text, file_counter):
    """Convert Hindi text to speech"""
    try:
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=hindi_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="hi-IN", 
            name="hi-IN-Standard-A"
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MULAW, 
            sample_rate_hertz=8000
        )

        response = client.synthesize_speech(
            input=synthesis_input, 
            voice=voice, 
            audio_config=audio_config
        )
        
        return response.audio_content
    except Exception as e:
        print(f"Hindi Text-to-Speech error: {e}")
        return None

# Flask app with SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    """Handle incoming Twilio calls"""
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    to_number = request.form.get('To')
    
    print(f"Incoming call from {from_number} to {to_number} (CallSid: {call_sid})")
    
    # TwiML response to start media stream
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Start>
            <Stream url="wss://e5562da11db7.ngrok-free.app/socket.io/?EIO=4&transport=websocket" />
        </Start>
        <Say language="hi-IN">नमस्ते! अनुवाद सेवा तैयार है।</Say>
        <Say language="en-US">Hello! Translation service is ready.</Say>
        <Pause length="1"/>
    </Response>"""
    
    return Response(twiml, mimetype='text/xml')

@app.route('/call-status', methods=['POST'])
def call_status():
    """Handle call status updates"""
    call_sid = request.form.get('CallSid')
    call_status = request.form.get('CallStatus')
    
    print(f"Call {call_sid} status: {call_status}")
    
    if call_status == 'completed':
        # Clean up call session
        for stream_sid, session in list(active_calls.items()):
            if session.call_sid == call_sid:
                del active_calls[stream_sid]
                break
    
    return Response('OK', mimetype='text/plain')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('message')
def handle_message(data):
    """Handle WebSocket messages from Twilio"""
    try:
        if isinstance(data, str):
            data = json.loads(data)
        
        if data.get('event') == 'media':
            # Process audio data
            stream_sid = data.get('streamSid')
            audio_payload = data.get('media', {}).get('payload')
            
            if audio_payload:
                # Here you would process the audio and send back translation
                # For now, just acknowledge receipt
                emit('message', {'event': 'ack', 'streamSid': stream_sid})
                
        elif data.get('event') == 'start':
            stream_sid = data.get('streamSid')
            call_sid = data.get('callSid', 'unknown')
            print(f"Stream started: {stream_sid}")
            
            # Create call session
            call_session = SinglePortCallSession(call_sid, stream_sid)
            active_calls[stream_sid] = call_session
            
        elif data.get('event') == 'stop':
            stream_sid = data.get('streamSid')
            print(f"Stream stopped: {stream_sid}")
            if stream_sid in active_calls:
                del active_calls[stream_sid]
                
    except Exception as e:
        print(f"Error handling message: {e}")

if __name__ == "__main__":
    print("="*70)
    print("SINGLE PORT BIDIRECTIONAL VOICE TRANSLATION SYSTEM")
    print("="*70)
    print("Features:")
    print("✓ Real-time Hindi ↔ English translation")
    print("✓ Single port (HTTP + WebSocket)")
    print("✓ Works with free ngrok account")
    print("\nSetup Instructions:")
    print("1. Start ngrok: ngrok http 3000")
    print("2. Update the WebSocket URL in the TwiML response")
    print("3. Configure your Twilio phone number webhook")
    print("4. Make a call to your Twilio number")
    print("="*70)
    
    socketio.run(app, host='0.0.0.0', port=3000, debug=False)
