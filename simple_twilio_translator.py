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
import websockets
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/apple/text_to_voice_translator/google-credentials.json"

# Global variables for managing call state
active_calls = {}

class SimpleCallSession:
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

# WebSocket handler for Twilio media stream
async def twilio_websocket(websocket, path):
    print("New WebSocket connection established")
    print(f"WebSocket path: {path}")
    
    # Initialize speech client
    speech_client = speech.SpeechClient()
    
    # Speech recognition configurations
    hindi_config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
        sample_rate_hertz=8000,
        language_code="hi-IN",
        enable_automatic_punctuation=True
    )
    
    english_config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
        sample_rate_hertz=8000,
        language_code="en-US",
        enable_automatic_punctuation=True
    )
    
    # Call session variables
    call_session = None
    current_language = 'hi-IN'  # Start with Hindi detection
    last_processed_transcript = ""
    file_counter = 0
    stream_sid = None
    min_translation_interval = 2.0

    async def stream_audio_to_speech():
        nonlocal stream_sid, call_session, current_language, last_processed_transcript
        nonlocal file_counter
        
        async for message in websocket:
            try:
                data = json.loads(message)
                
                if data['event'] == 'media':
                    stream_sid = data['streamSid']
                    audio_payload = data['media']['payload']
                    
                    # Send audio for recognition
                    audio = base64.b64decode(audio_payload)
                    yield speech.StreamingRecognizeRequest(audio_content=audio)
                    
                elif data['event'] == 'start':
                    print(f"Stream started: {data['streamSid']}")
                    stream_sid = data['streamSid']
                    call_session = SimpleCallSession(data.get('callSid', 'unknown'), stream_sid)
                    active_calls[stream_sid] = call_session
                    
                elif data['event'] == 'stop':
                    print("Stream stopped")
                    if stream_sid in active_calls:
                        del active_calls[stream_sid]
                    break
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                continue
            except Exception as e:
                print(f"WebSocket message error: {e}")
                continue

    try:
        # Start with Hindi recognition
        streaming_config = speech.StreamingRecognitionConfig(
            config=hindi_config, 
            interim_results=True
        )
        
        responses = speech_client.streaming_recognize(streaming_config, stream_audio_to_speech())
        
        async for response in responses:
            if not response.results or not response.results[0].alternatives:
                continue
                
            transcript = response.results[0].alternatives[0].transcript
            confidence = response.results[0].alternatives[0].confidence
            
            # Process final results with good confidence
            if (response.results[0].is_final and 
                transcript.strip() and 
                transcript != last_processed_transcript and
                confidence > 0.6):
                
                current_time = time.time()
                
                # Rate limiting
                if current_time - call_session.last_translation_time < min_translation_interval:
                    continue
                
                call_session.last_translation_time = current_time
                
                print(f"Final transcript ({current_language}): {transcript} (confidence: {confidence:.2f})")
                last_processed_transcript = transcript
                
                # Translate and synthesize based on detected language
                if current_language == 'hi-IN':
                    # Hindi speaker → translate to English → synthesize English
                    english_text = translate_hindi_to_english(transcript)
                    if english_text:
                        file_counter += 1
                        audio_content = synthesize_english_speech(english_text, file_counter)
                        if audio_content and stream_sid:
                            await websocket.send(json.dumps({
                                'event': 'media',
                                'streamSid': stream_sid,
                                'media': {'payload': base64.b64encode(audio_content).decode('utf-8')}
                            }))
                            print(f"Sent English translation: {english_text}")
                            
                elif current_language == 'en-US':
                    # English speaker → translate to Hindi → synthesize Hindi
                    hindi_text = translate_english_to_hindi(transcript)
                    if hindi_text:
                        file_counter += 1
                        audio_content = synthesize_hindi_speech(hindi_text, file_counter)
                        if audio_content and stream_sid:
                            await websocket.send(json.dumps({
                                'event': 'media',
                                'streamSid': stream_sid,
                                'media': {'payload': base64.b64encode(audio_content).decode('utf-8')}
                            }))
                            print(f"Sent Hindi translation: {hindi_text}")
                
                # Switch language for next detection
                current_language = 'en-US' if current_language == 'hi-IN' else 'hi-IN'
                
                # Update streaming config for next language
                if current_language == 'hi-IN':
                    streaming_config = speech.StreamingRecognitionConfig(
                        config=hindi_config, 
                        interim_results=True
                    )
                else:
                    streaming_config = speech.StreamingRecognitionConfig(
                        config=english_config, 
                        interim_results=True
                    )
                
    except Exception as e:
        print(f"Streaming error: {e}")
    finally:
        try:
            await websocket.close()
        except Exception as e:
            print(f"WebSocket close error: {e}")

# Flask app for HTTP webhooks
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
            <Stream url="wss://2c4769e21ae0.ngrok-free.app/websocket" />
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

# Start servers
async def start_servers():
    if not os.path.exists("/Users/apple/text_to_voice_translator/google-credentials.json"):
        print("Error: google-credentials.json not found.")
        return

    # Start Flask in a separate thread
    def run_flask():
        app.run(host='0.0.0.0', port=3000, debug=False, use_reloader=False)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("Flask server running on port 3000")

    # Start WebSocket server on port 8080
    try:
        start_server = websockets.serve(twilio_websocket, '0.0.0.0', 8080)
        await start_server
        print("WebSocket server running on port 8080")
        print("\n" + "="*70)
        print("SIMPLE BIDIRECTIONAL VOICE TRANSLATION SYSTEM READY")
        print("="*70)
        print("Features:")
        print("✓ Real-time Hindi ↔ English translation")
        print("✓ Simple and reliable")
        print("✓ Automatic language switching")
        print("\nSetup Instructions:")
        print("1. Start ngrok: ngrok http 3000")
        print("2. Start ngrok for WebSocket: ngrok tcp 8080")
        print("3. Update the WebSocket URL in the TwiML response")
        print("4. Configure your Twilio phone number webhook")
        print("5. Make a call to your Twilio number")
        print("="*70)
    except Exception as e:
        print(f"WebSocket server error: {e}")

if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(start_servers())
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("Server stopped by user.")
    except Exception as e:
        print(f"Server startup error: {e}")
