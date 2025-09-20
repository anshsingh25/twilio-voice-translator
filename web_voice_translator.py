#!/usr/bin/env python3
"""
Web-based Voice Translator
Uses WebRTC for audio + Google Cloud for translation
No Twilio dependency
"""

import os
import json
from flask import Flask, request, Response, render_template_string

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
    GOOGLE_CLOUD_AVAILABLE = True
    print("✅ Google Cloud available")
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    print("❌ Google Cloud not available")

app = Flask(__name__)

# HTML template for web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Voice Translator</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .status { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .info { background: #d1ecf1; color: #0c5460; }
        textarea { width: 100%; height: 100px; margin: 10px 0; }
        audio { width: 100%; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🎤 Voice Translator</h1>
    <p>Hindi ↔ English Translation using Google Cloud</p>
    
    <div class="container">
        <h3>🎙️ Voice Recording</h3>
        <button id="startBtn" onclick="startRecording()">Start Recording</button>
        <button id="stopBtn" onclick="stopRecording()" disabled>Stop Recording</button>
        <div id="status" class="status info">Click "Start Recording" and speak for 5 seconds</div>
        <audio id="audioPlayer" controls style="display:none;"></audio>
    </div>
    
    <div class="container">
        <h3>📝 Text Translation</h3>
        <textarea id="textInput" placeholder="Type or paste text here..."></textarea>
        <button onclick="translateText()">Translate & Speak</button>
        <div id="textStatus" class="status info">Enter text and click translate</div>
        <audio id="textAudioPlayer" controls style="display:none;"></audio>
    </div>
    
    <div class="container">
        <h3>📊 System Status</h3>
        <div id="systemStatus">Loading...</div>
    </div>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;

        // Check system status
        async function checkStatus() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                document.getElementById('systemStatus').innerHTML = `
                    <div class="status ${data.status === 'healthy' ? 'success' : 'error'}">
                        Status: ${data.status}<br>
                        Google Cloud: ${data.google_cloud_available ? '✅ Available' : '❌ Not Available'}<br>
                        Credentials: ${data.credentials_setup ? '✅ Set up' : '❌ Not Set up'}
                    </div>
                `;
            } catch (error) {
                document.getElementById('systemStatus').innerHTML = `
                    <div class="status error">Error checking status: ${error.message}</div>
                `;
            }
        }

        // Start recording
        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    await processAudio(audioBlob);
                    stream.getTracks().forEach(track => track.stop());
                };

                mediaRecorder.start();
                isRecording = true;
                
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                document.getElementById('status').innerHTML = '<div class="status info">🎤 Recording... Speak now!</div>';
                
                // Auto-stop after 5 seconds
                setTimeout(() => {
                    if (isRecording) {
                        stopRecording();
                    }
                }, 5000);
                
            } catch (error) {
                document.getElementById('status').innerHTML = `<div class="status error">Error: ${error.message}</div>`;
            }
        }

        // Stop recording
        function stopRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
                isRecording = false;
                
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                document.getElementById('status').innerHTML = '<div class="status info">🔄 Processing audio...</div>';
            }
        }

        // Process recorded audio
        async function processAudio(audioBlob) {
            try {
                const formData = new FormData();
                formData.append('audio', audioBlob, 'recording.wav');

                const response = await fetch('/process-audio', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                
                if (response.ok) {
                    document.getElementById('status').innerHTML = `
                        <div class="status success">
                            ✅ Translation: "${result.translated_text}"<br>
                            Source: ${result.source_language} → Target: ${result.target_language}
                        </div>
                    `;
                    
                    if (result.audio_url) {
                        const audioPlayer = document.getElementById('audioPlayer');
                        audioPlayer.src = result.audio_url;
                        audioPlayer.style.display = 'block';
                        audioPlayer.play();
                    }
                } else {
                    document.getElementById('status').innerHTML = `<div class="status error">Error: ${result.error}</div>`;
                }
            } catch (error) {
                document.getElementById('status').innerHTML = `<div class="status error">Error: ${error.message}</div>`;
            }
        }

        // Translate text
        async function translateText() {
            const text = document.getElementById('textInput').value.trim();
            if (!text) {
                document.getElementById('textStatus').innerHTML = '<div class="status error">Please enter some text</div>';
                return;
            }

            try {
                document.getElementById('textStatus').innerHTML = '<div class="status info">🔄 Translating...</div>';

                const response = await fetch('/translate-text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text })
                });

                const result = await response.json();
                
                if (response.ok) {
                    document.getElementById('textStatus').innerHTML = `
                        <div class="status success">
                            ✅ Translation: "${result.translated_text}"<br>
                            Source: ${result.source_language} → Target: ${result.target_language}
                        </div>
                    `;
                    
                    if (result.audio_url) {
                        const audioPlayer = document.getElementById('textAudioPlayer');
                        audioPlayer.src = result.audio_url;
                        audioPlayer.style.display = 'block';
                        audioPlayer.play();
                    }
                } else {
                    document.getElementById('textStatus').innerHTML = `<div class="status error">Error: ${result.error}</div>`;
                }
            } catch (error) {
                document.getElementById('textStatus').innerHTML = `<div class="status error">Error: ${error.message}</div>`;
            }
        }

        // Initialize
        checkStatus();
        setInterval(checkStatus, 30000); // Check status every 30 seconds
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "google_cloud_available": GOOGLE_CLOUD_AVAILABLE,
        "credentials_setup": credentials_setup
    }, 200

def detect_language(text):
    """Detect if text is Hindi or English"""
    devanagari_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
    is_hindi = any(char in devanagari_chars for char in text)
    
    # Check for common Hindi words in English script
    hindi_words = ['namaste', 'kaise', 'ho', 'dhanyawad', 'alvida', 'theek', 'hun', 'aap']
    speech_words = text.lower().split()
    has_hindi_words = any(word in speech_words for word in hindi_words)
    
    return 'hi' if (is_hindi or has_hindi_words) else 'en'

def translate_text(text, source_lang, target_lang):
    """Translate text using Google Translate"""
    try:
        if not GOOGLE_CLOUD_AVAILABLE:
            return text
        
        client = translate.Client()
        result = client.translate(
            text, 
            source_language=source_lang, 
            target_language=target_lang,
            format_='text'
        )
        return result['translatedText']
        
    except Exception as e:
        print(f"❌ Translation error: {e}")
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
            # Save audio file and return URL
            import base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            audio_url = f"data:audio/mp3;base64,{audio_b64}"
            
            return {
                "translated_text": translated_text,
                "source_language": source_lang,
                "target_language": target_lang,
                "audio_url": audio_url
            }, 200
        else:
            return {
                "translated_text": translated_text,
                "source_language": source_lang,
                "target_language": target_lang,
                "audio_url": None
            }, 200
            
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/process-audio', methods=['POST'])
def process_audio():
    """Process uploaded audio file"""
    try:
        # For now, return a simple response
        # In a real implementation, you would:
        # 1. Save the audio file
        # 2. Use Google Speech-to-Text to transcribe it
        # 3. Translate the text
        # 4. Synthesize speech
        # 5. Return the result
        
        return {
            "error": "Audio processing not implemented yet. Use text translation instead.",
            "suggestion": "Type your text in the text area and click 'Translate & Speak'"
        }, 501
        
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    print(f"🚀 Web Voice Translator on port {port}")
    print("="*60)
    print("✅ Features:")
    print("   ✓ Web-based interface (no Twilio)")
    print("   ✓ Google Translate (Hindi ↔ English)")
    print("   ✓ Google Text-to-Speech (High-quality voices)")
    print("   ✓ Real-time text translation")
    print(f"   ✓ Google Cloud: {GOOGLE_CLOUD_AVAILABLE}")
    print(f"   ✓ Credentials: {credentials_setup}")
    print("="*60)
    print("🌐 Open in browser: http://localhost:3000")
    print("="*60)
    
    app.run(host='0.0.0.0', port=port, debug=False)
