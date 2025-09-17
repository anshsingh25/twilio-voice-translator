import os
import asyncio
import json
import base64
import queue
import threading
import time
import struct
from collections import deque
from flask import Flask, request, Response, jsonify
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/apple/text_to_voice_translator/google-credentials.json"

# Global variables for managing call state
active_calls = {}
audio_queues = {}

class SingleTunnelCallSession:
    def __init__(self, call_sid, stream_sid):
        self.call_sid = call_sid
        self.stream_sid = stream_sid
        self.last_processed_transcript = ""
        self.file_counter = 0
        self.last_translation_time = 0
        self.is_processing = False
        self.translation_lock = threading.Lock()
        self.audio_queue = queue.Queue()
        self.current_language = 'hi-IN'

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

# Flask app for HTTP webhooks and media streaming
app = Flask(__name__)

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
            <Stream url="wss://1e6d229a057a.ngrok-free.app/websocket" />
        </Start>
        <Say language="hi-IN">नमस्ते! अनुवाद सेवा तैयार है।</Say>
        <Say language="en-US">Hello! Translation service is ready.</Say>
        <Pause length="1"/>
    </Response>"""
    
    return Response(twiml, mimetype='text/xml')

@app.route('/websocket', methods=['GET', 'POST'])
def websocket_handler():
    """Handle WebSocket-like requests via HTTP"""
    if request.method == 'GET':
        # WebSocket upgrade request - return 404 to force Twilio to use HTTP
        return Response("WebSocket not supported", status=404)
    
    # Handle media stream data
    try:
        data = request.get_json()
        if not data:
            return Response("No data", status=400)
        
        event = data.get('event')
        stream_sid = data.get('streamSid')
        
        if event == 'start':
            print(f"Stream started: {stream_sid}")
            call_sid = data.get('callSid', 'unknown')
            call_session = SingleTunnelCallSession(call_sid, stream_sid)
            active_calls[stream_sid] = call_session
            return Response("OK", status=200)
        
        elif event == 'media':
            # Process audio data
            audio_payload = data.get('media', {}).get('payload')
            if audio_payload and stream_sid in active_calls:
                # Process audio in background
                threading.Thread(
                    target=process_audio, 
                    args=(audio_payload, stream_sid),
                    daemon=True
                ).start()
            return Response("OK", status=200)
        
        elif event == 'stop':
            print(f"Stream stopped: {stream_sid}")
            if stream_sid in active_calls:
                del active_calls[stream_sid]
            return Response("OK", status=200)
        
        return Response("OK", status=200)
        
    except Exception as e:
        print(f"WebSocket handler error: {e}")
        return Response("Error", status=500)

def process_audio(audio_payload, stream_sid):
    """Process audio data and generate translation"""
    try:
        if stream_sid not in active_calls:
            return
        
        call_session = active_calls[stream_sid]
        
        # Decode audio
        audio_data = base64.b64decode(audio_payload)
        
        # Simple voice activity detection
        if len(audio_data) < 2:
            return
        
        # Calculate RMS for voice detection
        samples = struct.unpack('<' + 'h' * (len(audio_data) // 2), audio_data)
        rms = (sum(x * x for x in samples) / len(samples)) ** 0.5
        
        # Only process if there's significant audio
        if rms < 0.01:
            return
        
        # For now, we'll simulate speech recognition
        # In a real implementation, you'd send this to Google Speech-to-Text
        print(f"Processing audio for stream {stream_sid}, RMS: {rms:.4f}")
        
        # Simulate speech recognition result (replace with actual Google Speech-to-Text)
        # This is a placeholder - you'd need to implement actual speech recognition
        if rms > 0.05:  # Threshold for "speech detected"
            # Simulate getting a transcript
            if call_session.current_language == 'hi-IN':
                # Simulate Hindi speech
                transcript = "नमस्ते कैसे हैं आप"
                print(f"Simulated Hindi transcript: {transcript}")
                
                # Translate to English
                english_text = translate_hindi_to_english(transcript)
                if english_text:
                    # Generate English speech
                    audio_content = synthesize_english_speech(english_text, call_session.file_counter)
                    if audio_content:
                        call_session.file_counter += 1
                        # Queue audio for playback
                        call_session.audio_queue.put(audio_content)
                        print(f"Generated English translation: {english_text}")
                
                # Switch to English detection
                call_session.current_language = 'en-US'
                
            else:
                # Simulate English speech
                transcript = "Hello how are you"
                print(f"Simulated English transcript: {transcript}")
                
                # Translate to Hindi
                hindi_text = translate_english_to_hindi(transcript)
                if hindi_text:
                    # Generate Hindi speech
                    audio_content = synthesize_hindi_speech(hindi_text, call_session.file_counter)
                    if audio_content:
                        call_session.file_counter += 1
                        # Queue audio for playback
                        call_session.audio_queue.put(audio_content)
                        print(f"Generated Hindi translation: {hindi_text}")
                
                # Switch to Hindi detection
                call_session.current_language = 'hi-IN'
        
    except Exception as e:
        print(f"Audio processing error: {e}")

@app.route('/get-audio/<stream_sid>')
def get_audio(stream_sid):
    """Get translated audio for a stream"""
    if stream_sid not in active_calls:
        return Response("Stream not found", status=404)
    
    call_session = active_calls[stream_sid]
    
    try:
        # Get audio from queue (non-blocking)
        audio_content = call_session.audio_queue.get_nowait()
        
        # Return audio as base64
        audio_b64 = base64.b64encode(audio_content).decode('utf-8')
        return jsonify({
            'audio': audio_b64,
            'streamSid': stream_sid
        })
        
    except queue.Empty:
        return jsonify({'audio': None, 'streamSid': stream_sid})

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

if __name__ == "__main__":
    print("="*70)
    print("SINGLE TUNNEL BIDIRECTIONAL VOICE TRANSLATION SYSTEM")
    print("="*70)
    print("Features:")
    print("✓ Real-time Hindi ↔ English translation")
    print("✓ Works with free ngrok account (single tunnel)")
    print("✓ HTTP-based media streaming")
    print("✓ Simulated speech recognition (for demo)")
    print("\nSetup Instructions:")
    print("1. Start ngrok: ngrok http 3000")
    print("2. Update the WebSocket URL in the TwiML response")
    print("3. Configure your Twilio phone number webhook")
    print("4. Make a call to your Twilio number")
    print("\nNote: This version uses simulated speech recognition")
    print("For production, integrate with Google Speech-to-Text API")
    print("="*70)
    
    app.run(host='0.0.0.0', port=3000, debug=False)
