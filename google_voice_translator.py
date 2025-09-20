#!/usr/bin/env python3
"""
Google Cloud Voice Translator
No Twilio - Pure Google Cloud solution
"""

import os
import json
import pyaudio
import wave
import threading
import time
from flask import Flask, request, Response

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

credentials_setup = setup_google_credentials()

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

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 5

class VoiceTranslator:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.is_recording = False
        
    def record_audio(self, duration=5):
        """Record audio from microphone"""
        try:
            stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            print(f"🎤 Recording for {duration} seconds...")
            frames = []
            
            for _ in range(0, int(RATE / CHUNK * duration)):
                if not self.is_recording:
                    break
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            return b''.join(frames)
            
        except Exception as e:
            print(f"❌ Recording error: {e}")
            return None
    
    def transcribe_audio(self, audio_data):
        """Convert speech to text using Google Speech-to-Text"""
        try:
            client = speech.SpeechClient()
            
            audio = speech.RecognitionAudio(content=audio_data)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=RATE,
                language_code="hi-IN",  # Hindi
                alternative_language_codes=["en-US"]  # English fallback
            )
            
            response = client.recognize(config=config, audio=audio)
            
            for result in response.results:
                transcript = result.alternatives[0].transcript
                confidence = result.alternatives[0].confidence
                print(f"🎤 Speech: '{transcript}' (Confidence: {confidence:.2f})")
                return transcript, confidence
            
            return None, 0
            
        except Exception as e:
            print(f"❌ Speech-to-Text error: {e}")
            return None, 0
    
    def translate_text(self, text, source_lang, target_lang):
        """Translate text using Google Translate"""
        try:
            client = translate.Client()
            result = client.translate(
                text, 
                source_language=source_lang, 
                target_language=target_lang,
                format_='text'
            )
            translated_text = result['translatedText']
            print(f"🔄 Translation: '{text}' → '{translated_text}'")
            return translated_text
            
        except Exception as e:
            print(f"❌ Translation error: {e}")
            return text
    
    def synthesize_speech(self, text, language_code):
        """Convert text to speech using Google Text-to-Speech"""
        try:
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
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000
            )
            
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            print(f"🔊 Synthesized speech for: '{text}'")
            return response.audio_content
            
        except Exception as e:
            print(f"❌ Text-to-Speech error: {e}")
            return None
    
    def play_audio(self, audio_data):
        """Play audio through speakers"""
        try:
            stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=16000,
                output=True
            )
            
            print("🔊 Playing audio...")
            stream.write(audio_data)
            stream.stop_stream()
            stream.close()
            print("✅ Audio played successfully")
            
        except Exception as e:
            print(f"❌ Audio playback error: {e}")
    
    def detect_language(self, text):
        """Detect if text is Hindi or English"""
        devanagari_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
        is_hindi = any(char in devanagari_chars for char in text)
        
        # Check for common Hindi words in English script
        hindi_words = ['namaste', 'kaise', 'ho', 'dhanyawad', 'alvida', 'theek', 'hun', 'aap']
        speech_words = text.lower().split()
        has_hindi_words = any(word in speech_words for word in hindi_words)
        
        return 'hi' if (is_hindi or has_hindi_words) else 'en'
    
    def translate_and_speak(self, text):
        """Complete translation and speech pipeline"""
        if not text:
            return
        
        # Detect language
        source_lang = self.detect_language(text)
        target_lang = 'en' if source_lang == 'hi' else 'hi'
        
        # Translate
        translated_text = self.translate_text(text, source_lang, target_lang)
        
        # Synthesize speech
        audio_data = self.synthesize_speech(translated_text, target_lang)
        
        if audio_data:
            # Play audio
            self.play_audio(audio_data)
        else:
            print(f"❌ Could not synthesize speech for: '{translated_text}'")

# Global translator instance
translator = VoiceTranslator()

@app.route('/')
def home():
    return {
        "message": "Google Cloud Voice Translator",
        "version": "1.0.0",
        "features": [
            "Google Speech-to-Text",
            "Google Translate",
            "Google Text-to-Speech",
            "Real-time Hindi ↔ English translation"
        ],
        "status": "Ready"
    }, 200

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "google_cloud_available": GOOGLE_CLOUD_AVAILABLE,
        "credentials_setup": credentials_setup
    }, 200

@app.route('/start-recording', methods=['POST'])
def start_recording():
    """Start recording audio"""
    try:
        translator.is_recording = True
        
        # Record audio in a separate thread
        def record_and_translate():
            audio_data = translator.record_audio(RECORD_SECONDS)
            if audio_data:
                # Transcribe
                transcript, confidence = translator.transcribe_audio(audio_data)
                if transcript and confidence > 0.5:
                    # Translate and speak
                    translator.translate_and_speak(transcript)
                else:
                    print("❌ No speech detected or low confidence")
            translator.is_recording = False
        
        thread = threading.Thread(target=record_and_translate)
        thread.start()
        
        return {"status": "recording_started", "duration": RECORD_SECONDS}, 200
        
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/stop-recording', methods=['POST'])
def stop_recording():
    """Stop recording audio"""
    translator.is_recording = False
    return {"status": "recording_stopped"}, 200

@app.route('/translate-text', methods=['POST'])
def translate_text_endpoint():
    """Translate text and return audio"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return {"error": "No text provided"}, 400
        
        # Detect language
        source_lang = translator.detect_language(text)
        target_lang = 'en' if source_lang == 'hi' else 'hi'
        
        # Translate
        translated_text = translator.translate_text(text, source_lang, target_lang)
        
        # Synthesize speech
        audio_data = translator.synthesize_speech(translated_text, target_lang)
        
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
            return {"error": "Could not synthesize speech"}, 500
            
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    print(f"🚀 Google Cloud Voice Translator on port {port}")
    print("="*60)
    print("✅ Features:")
    print("   ✓ Google Speech-to-Text (Hindi + English)")
    print("   ✓ Google Translate (Hindi ↔ English)")
    print("   ✓ Google Text-to-Speech (High-quality voices)")
    print("   ✓ Real-time audio recording and playback")
    print("   ✓ No Twilio dependency")
    print(f"   ✓ Google Cloud: {GOOGLE_CLOUD_AVAILABLE}")
    print(f"   ✓ Credentials: {credentials_setup}")
    print("="*60)
    print("📞 Usage:")
    print("   POST /start-recording - Start recording and translation")
    print("   POST /stop-recording - Stop recording")
    print("   POST /translate-text - Translate text and get audio")
    print("="*60)
    
    app.run(host='0.0.0.0', port=port, debug=False)
