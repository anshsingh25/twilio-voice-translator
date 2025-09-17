#!/usr/bin/env python3
"""
Railway Deployment - Fixed Twilio Voice Translator
Handles Google Cloud dependencies properly
"""

import os
import json
import asyncio
import threading
import base64
import io
import wave
from flask import Flask, request, Response

# Try to import Google Cloud libraries with error handling
try:
    import websockets
    from google.cloud import speech
    from google.cloud import texttospeech
    from google.cloud import translate_v2 as translate
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError as e:
    print(f"Google Cloud libraries not available: {e}")
    GOOGLE_CLOUD_AVAILABLE = False

# Global variables for managing call state
active_calls = {}

class RailwayCallSession:
    def __init__(self, call_sid):
        self.call_sid = call_sid
        self.websocket = None
        self.audio_buffer = []
        self.is_speaking = False
        self.last_language = "en"
        
        if GOOGLE_CLOUD_AVAILABLE:
            try:
                self.speech_client = speech.SpeechClient()
                self.tts_client = texttospeech.TextToSpeechClient()
                self.translate_client = translate.Client()
                self.google_cloud_ready = True
            except Exception as e:
                print(f"Google Cloud initialization error: {e}")
                self.google_cloud_ready = False
        else:
            self.google_cloud_ready = False
        
    async def handle_audio(self, audio_data):
        """Process incoming audio and translate"""
        if not self.google_cloud_ready:
            print("Google Cloud not ready, skipping audio processing")
            return
            
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data)
            
            # Add to buffer
            self.audio_buffer.append(audio_bytes)
            
            # Process when we have enough audio (simplified)
            if len(self.audio_buffer) >= 3:  # Process every 3 chunks
                await self.process_audio()
                self.audio_buffer = []
                
        except Exception as e:
            print(f"Audio handling error: {e}")
    
    async def process_audio(self):
        """Process buffered audio for speech recognition"""
        if not self.google_cloud_ready:
            return
            
        try:
            # Combine audio chunks
            combined_audio = b''.join(self.audio_buffer)
            
            # Convert to WAV format (simplified)
            audio_content = self.convert_to_wav(combined_audio)
            
            # Configure speech recognition
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=8000,
                language_code="hi-IN",  # Start with Hindi
                alternative_language_codes=["en-US"],
                enable_automatic_punctuation=True,
                model="latest_long"
            )
            
            audio = speech.RecognitionAudio(content=audio_content)
            
            # Perform speech recognition
            response = self.speech_client.recognize(config=config, audio=audio)
            
            if response.results:
                result = response.results[0]
                if result.is_final:
                    transcript = result.alternatives[0].transcript
                    confidence = result.alternatives[0].confidence
                    
                    if confidence > 0.7:  # Only process high-confidence results
                        await self.translate_and_speak(transcript)
                        
        except Exception as e:
            print(f"Speech recognition error: {e}")
    
    def convert_to_wav(self, audio_data):
        """Convert raw audio to WAV format"""
        try:
            # Create a simple WAV header for 8kHz, 16-bit, mono
            sample_rate = 8000
            channels = 1
            bits_per_sample = 16
            
            # Calculate WAV file size
            data_size = len(audio_data)
            file_size = 36 + data_size
            
            # WAV header
            wav_header = bytearray()
            wav_header.extend(b'RIFF')
            wav_header.extend(file_size.to_bytes(4, 'little'))
            wav_header.extend(b'WAVE')
            wav_header.extend(b'fmt ')
            wav_header.extend((16).to_bytes(4, 'little'))  # fmt chunk size
            wav_header.extend((1).to_bytes(2, 'little'))   # audio format (PCM)
            wav_header.extend(channels.to_bytes(2, 'little'))
            wav_header.extend(sample_rate.to_bytes(4, 'little'))
            wav_header.extend((sample_rate * channels * bits_per_sample // 8).to_bytes(4, 'little'))
            wav_header.extend((channels * bits_per_sample // 8).to_bytes(2, 'little'))
            wav_header.extend(bits_per_sample.to_bytes(2, 'little'))
            wav_header.extend(b'data')
            wav_header.extend(data_size.to_bytes(4, 'little'))
            
            return bytes(wav_header) + audio_data
            
        except Exception as e:
            print(f"WAV conversion error: {e}")
            return audio_data
    
    async def translate_and_speak(self, text):
        """Translate text and synthesize speech"""
        if not self.google_cloud_ready:
            return
            
        try:
            # Detect language
            detected_language = self.detect_language(text)
            
            # Translate based on detected language
            if detected_language == "hi":
                # Hindi to English
                translated_text = self.translate_client.translate(text, target_language='en')['translatedText']
                target_language = "en-US"
                print(f"Hindi: {text} → English: {translated_text}")
            else:
                # English to Hindi
                translated_text = self.translate_client.translate(text, target_language='hi')['translatedText']
                target_language = "hi-IN"
                print(f"English: {text} → Hindi: {translated_text}")
            
            # Synthesize speech
            synthesis_input = texttospeech.SynthesisInput(text=translated_text)
            voice = texttospeech.VoiceSelectionParams(
                language_code=target_language,
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MULAW,
                sample_rate_hertz=8000
            )
            
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Send audio back to Twilio
            if self.websocket:
                audio_b64 = base64.b64encode(response.audio_content).decode('utf-8')
                await self.websocket.send(json.dumps({
                    "event": "media",
                    "streamSid": "your-stream-sid",
                    "media": {
                        "payload": audio_b64
                    }
                }))
                
        except Exception as e:
            print(f"Translation/synthesis error: {e}")
    
    def detect_language(self, text):
        """Simple language detection"""
        # Simple heuristic: if text contains Devanagari characters, it's Hindi
        devanagari_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
        if any(char in devanagari_chars for char in text):
            return "hi"
        return "en"

async def twilio_websocket(websocket, path):
    """Handle Twilio WebSocket connections"""
    try:
        print(f"WebSocket connection established: {websocket.remote_address}")
        
        # Get call SID from query parameters
        call_sid = None
        if '?' in path:
            params = path.split('?')[1]
            for param in params.split('&'):
                if param.startswith('CallSid='):
                    call_sid = param.split('=')[1]
                    break
        
        if not call_sid:
            print("No CallSid provided")
            await websocket.close()
            return
        
        # Create or get call session
        if call_sid not in active_calls:
            active_calls[call_sid] = RailwayCallSession(call_sid)
        
        session = active_calls[call_sid]
        session.websocket = websocket
        
        # Send start message
        await websocket.send(json.dumps({
            "event": "start",
            "sequenceNumber": "1",
            "start": {
                "accountSid": "your-account-sid",
                "callSid": call_sid,
                "tracks": ["inbound", "outbound"],
                "mediaFormat": {
                    "encoding": "audio/x-mulaw",
                    "sampleRate": 8000,
                    "channels": 1
                },
                "streamSid": "your-stream-sid"
            }
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                
                if data.get("event") == "media":
                    media_data = data.get("media", {}).get("payload", "")
                    if media_data:
                        await session.handle_audio(media_data)
                        
            except json.JSONDecodeError:
                print("Invalid JSON received")
            except Exception as e:
                print(f"Message handling error: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Clean up
        if call_sid and call_sid in active_calls:
            del active_calls[call_sid]

# Flask app for HTTP webhooks
app = Flask(__name__)

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    status = {
        "status": "healthy", 
        "service": "twilio-voice-translator",
        "google_cloud_available": GOOGLE_CLOUD_AVAILABLE
    }
    return status, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    """Handle incoming Twilio calls"""
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    to_number = request.form.get('To')
    
    print(f"Incoming call from {from_number} to {to_number} (CallSid: {call_sid})")
    
    # Get the Railway domain from environment variable
    railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'your-railway-app.railway.app')
    if railway_domain == 'your-railway-app.railway.app':
        # Fallback to Railway's default domain format
        railway_domain = os.environ.get('RAILWAY_STATIC_URL', 'your-railway-app.railway.app')
    
    # TwiML response to start media stream
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Start>
            <Stream url="wss://{railway_domain}/websocket?CallSid={call_sid}">
                <Parameter name="CallSid" value="{call_sid}"/>
            </Stream>
        </Start>
        <Say language="hi-IN">नमस्ते! मैं आपकी आवाज़ का अनुवाद करूंगा।</Say>
        <Say language="en-US">Hello! I will translate your voice.</Say>
        <Say language="hi-IN">अब आप बोल सकते हैं।</Say>
        <Say language="en-US">You can start speaking now.</Say>
    </Response>"""
    
    return Response(twiml, mimetype='text/xml')

def run_flask_server(port):
    """Run Flask server"""
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

async def start_servers():
    """Start both Flask and WebSocket servers"""
    # Get port from Railway environment variable
    port = int(os.environ.get('PORT', 3000))
    
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask_server, args=(port,), daemon=True)
    flask_thread.start()
    print(f"Flask server running on port {port}")
    
    # Start WebSocket server on the same port (Railway handles routing)
    print(f"WebSocket server running on port {port}")
    await websockets.serve(twilio_websocket, "0.0.0.0", port)

if __name__ == "__main__":
    try:
        # Get port from Railway environment variable
        port = int(os.environ.get('PORT', 3000))
        print(f"Starting Railway deployment on port {port}")
        print("="*70)
        print("RAILWAY TWILIO VOICE TRANSLATOR")
        print("="*70)
        print("Features:")
        print("✓ Real-time Hindi ↔ English translation")
        print("✓ Railway cloud deployment")
        print("✓ Single port configuration")
        print("✓ Health check endpoint")
        print(f"✓ Google Cloud available: {GOOGLE_CLOUD_AVAILABLE}")
        print("="*70)
        
        if not GOOGLE_CLOUD_AVAILABLE:
            print("WARNING: Google Cloud libraries not available!")
            print("Please check your GOOGLE_APPLICATION_CREDENTIALS environment variable")
        
        asyncio.get_event_loop().run_until_complete(start_servers())
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("Server stopped by user.")
    except Exception as e:
        print(f"Server startup error: {e}")
