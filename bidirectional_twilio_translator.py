import os
import asyncio
import json
import base64
import queue
import threading
import time
from flask import Flask, request, Response
import websockets
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/apple/text_to_voice_translator/google-credentials.json"

# Global variables for managing call state
active_calls = {}  # Store call information
audio_queues = {}  # Separate queues for each call

class CallSession:
    def __init__(self, call_sid, stream_sid):
        self.call_sid = call_sid
        self.stream_sid = stream_sid
        self.last_processed_transcript = ""
        self.file_counter = 0
        self.is_speaking = False
        self.last_activity_time = time.time()
        self.audio_queue = queue.Queue()

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
    """Convert English text to speech (for Hindi speaker to hear)"""
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
        
        # Save for debugging
        audio_file_name = f"/Users/apple/text_to_voice_translator/english_output_{file_counter}.wav"
        with open(audio_file_name, "wb") as audio_file:
            audio_file.write(response.audio_content)
            print(f"Saved English audio to {audio_file_name}")

        return response.audio_content
    except Exception as e:
        print(f"English Text-to-Speech error: {e}")
        return None

def synthesize_hindi_speech(hindi_text, file_counter):
    """Convert Hindi text to speech (for English speaker to hear)"""
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
        
        # Save for debugging
        audio_file_name = f"/Users/apple/text_to_voice_translator/hindi_output_{file_counter}.wav"
        with open(audio_file_name, "wb") as audio_file:
            audio_file.write(response.audio_content)
            print(f"Saved Hindi audio to {audio_file_name}")

        return response.audio_content
    except Exception as e:
        print(f"Hindi Text-to-Speech error: {e}")
        return None

# Voice Activity Detection
def detect_voice_activity(audio_data, threshold=0.01):
    """Simple voice activity detection based on audio amplitude"""
    try:
        # Convert base64 audio to bytes and calculate RMS
        audio_bytes = base64.b64decode(audio_data)
        if len(audio_bytes) < 2:
            return False
        
        # Calculate RMS (Root Mean Square) for volume detection
        import struct
        samples = struct.unpack('<' + 'h' * (len(audio_bytes) // 2), audio_bytes)
        rms = (sum(x * x for x in samples) / len(samples)) ** 0.5
        return rms > threshold
    except Exception as e:
        print(f"Voice activity detection error: {e}")
        return False

# WebSocket handler for Twilio media stream
async def twilio_websocket(websocket, path):
    print("New WebSocket connection established")
    
    # Initialize speech clients for both languages
    speech_client = speech.SpeechClient()
    
    # Configuration for Hindi speech recognition (incoming from Hindi speaker)
    hindi_config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
        sample_rate_hertz=8000,
        language_code="hi-IN"
    )
    
    # Configuration for English speech recognition (incoming from English speaker)
    english_config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
        sample_rate_hertz=8000,
        language_code="en-US"
    )
    
    call_session = None
    current_language = None
    last_processed_transcript = ""
    file_counter = 0
    stream_sid = None
    voice_activity_buffer = []
    silence_duration = 0
    last_voice_time = time.time()

    async def stream_audio_to_speech():
        nonlocal stream_sid, call_session, current_language, last_processed_transcript, file_counter
        nonlocal voice_activity_buffer, silence_duration, last_voice_time
        
        async for message in websocket:
            try:
                data = json.loads(message)
                
                if data['event'] == 'media':
                    stream_sid = data['streamSid']
                    audio_payload = data['media']['payload']
                    
                    # Voice activity detection
                    has_voice = detect_voice_activity(audio_payload)
                    voice_activity_buffer.append(has_voice)
                    
                    # Keep only last 10 frames for analysis
                    if len(voice_activity_buffer) > 10:
                        voice_activity_buffer.pop(0)
                    
                    # Determine if someone is speaking
                    if has_voice:
                        last_voice_time = time.time()
                        silence_duration = 0
                    else:
                        silence_duration = time.time() - last_voice_time
                    
                    # Auto-detect language based on voice patterns and content
                    # This is a simplified approach - in production, you might want more sophisticated detection
                    if has_voice and silence_duration < 2.0:  # Someone is actively speaking
                        # For now, we'll alternate between languages or use a more sophisticated detection
                        # You can implement language detection based on audio characteristics
                        if current_language is None:
                            # Start with Hindi detection (assuming the person who picks up speaks Hindi)
                            current_language = 'hi-IN'
                            print("Detected Hindi speaker")
                        elif silence_duration > 1.0:  # After silence, switch language
                            current_language = 'en-US' if current_language == 'hi-IN' else 'hi-IN'
                            print(f"Switched to {current_language} detection")
                    
                    # Send audio to speech recognition
                    audio = base64.b64decode(audio_payload)
                    yield speech.StreamingRecognizeRequest(audio_content=audio)
                    
                elif data['event'] == 'start':
                    print(f"Stream started: {data['streamSid']}")
                    stream_sid = data['streamSid']
                    call_session = CallSession(data.get('callSid', 'unknown'), stream_sid)
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
        # Start with Hindi recognition (assuming the person who picks up speaks Hindi)
        current_language = 'hi-IN'
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
            
            # Only process final results with good confidence
            if (response.results[0].is_final and 
                transcript.strip() and 
                transcript != last_processed_transcript and
                confidence > 0.7):
                
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
                            print(f"Sent English translation to caller: {english_text}")
                            
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
                            print(f"Sent Hindi translation to caller: {hindi_text}")
                
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
            <Stream url="wss://YOUR_NGROK_URL.ngrok-free.app/websocket" />
        </Start>
        <Say language="hi-IN">नमस्ते! आपका स्वागत है। आप अंग्रेजी में बोल सकते हैं और मैं हिंदी में सुनाऊंगा।</Say>
        <Say language="en-US">Hello! Welcome. You can speak in Hindi and I will translate it to English for you.</Say>
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

    # Start WebSocket server
    try:
        start_server = websockets.serve(twilio_websocket, '0.0.0.0', 8080)
        await start_server
        print("WebSocket server running on port 8080")
        print("\n" + "="*60)
        print("BIDIRECTIONAL VOICE TRANSLATION SYSTEM READY")
        print("="*60)
        print("1. Update the ngrok URL in the TwiML response")
        print("2. Configure your Twilio phone number webhook to:")
        print("   http://YOUR_NGROK_URL.ngrok-free.app/twilio-webhook")
        print("3. Make a call to your Twilio number")
        print("4. The system will translate:")
        print("   - Hindi speech → English audio")
        print("   - English speech → Hindi audio")
        print("="*60)
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
