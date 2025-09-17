import os
import asyncio
import json
import base64
import queue
import threading
from flask import Flask, Response
import websockets
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/apple/text_to_voice_translator/google-credentials.json"

# Audio queue for local playback (optional, for debugging)
audio_queue = queue.Queue()

# Translate Hindi to English
def translate_text(hindi_text):
    try:
        client = translate.Client()
        result = client.translate(hindi_text, source_language='hi', target_language='en')
        english_text = result['translatedText']
        print(f"Translated: {english_text}")
        return english_text
    except Exception as e:
        print(f"Translation error: {e}")
        return None

# Text-to-Speech (English, MULAW for Twilio)
def synthesize_speech(english_text, file_counter):
    try:
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=english_text)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Standard-A")
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MULAW, sample_rate_hertz=8000)

        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        
        # Save for debugging
        audio_file_name = f"/Users/apple/text_to_voice_translator/output_audio_{file_counter}.wav"
        with open(audio_file_name, "wb") as audio_file:
            audio_file.write(response.audio_content)
            print(f"Saved audio to {audio_file_name}")

        return response.audio_content
    except Exception as e:
        print(f"Text-to-Speech error: {e}")
        return None

# Audio playback thread (optional, for local debugging)
def audio_playback_thread():
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=8000, output=True)
        try:
            while True:
                try:
                    audio_content = audio_queue.get(timeout=1)
                    stream.write(audio_content)
                    audio_queue.task_done()
                except queue.Empty:
                    continue
        except KeyboardInterrupt:
            pass
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
    except Exception as e:
        print(f"Audio playback error: {e}")

# WebSocket handler for Twilio media stream
async def twilio_websocket(websocket, path):
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
        sample_rate_hertz=8000,
        language_code="hi-IN"
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

    file_counter = 0
    last_processed_transcript = ""
    stream_sid = None

    async def stream_audio_to_speech():
        async for message in websocket:
            try:
                data = json.loads(message)
                if data['event'] == 'media':
                    nonlocal stream_sid
                    stream_sid = data['streamSid']
                    audio = base64.b64decode(data['media']['payload'])
                    yield speech.StreamingRecognizeRequest(audio_content=audio)
                elif data['event'] == 'start':
                    print(f"Stream started: {data['streamSid']}")
                    stream_sid = data['streamSid']
                elif data['event'] == 'stop':
                    print("Stream stopped")
                    break
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                continue
            except Exception as e:
                print(f"WebSocket message error: {e}")
                continue

    try:
        responses = client.streaming_recognize(streaming_config, stream_audio_to_speech())
        async for response in responses:
            if not response.results or not response.results[0].alternatives:
                continue
            transcript = response.results[0].alternatives[0].transcript
            if response.results[0].is_final and transcript.strip() and transcript != last_processed_transcript:
                print(f"Final transcript: {transcript}")
                last_processed_transcript = transcript
                english_text = translate_text(transcript)
                if english_text:
                    file_counter += 1
                    audio_content = synthesize_speech(english_text, file_counter)
                    if audio_content and stream_sid:
                        # Send translated audio back to Twilio
                        await websocket.send(json.dumps({
                            'event': 'media',
                            'streamSid': stream_sid,
                            'media': {'payload': base64.b64encode(audio_content).decode('utf-8')}
                        }))
                        # Queue for local playback (optional)
                        audio_queue.put(audio_content)
    except Exception as e:
        print(f"Streaming error: {e}")
    finally:
        try:
            await websocket.close()
        except Exception as e:
            print(f"WebSocket close error: {e}")

# Flask app for HTTP webhook
app = Flask(__name__)

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Start>
            <Stream url="wss://af844c11418d.ngrok-free.app/websocket" />
        </Start>
        <Say>Please wait while we process your call.</Say>
    </Response>"""
    return Response(twiml, mimetype='text/xml')

# Start servers
async def start_servers():
    if not os.path.exists("/Users/apple/text_to_voice_translator/google-credentials.json"):
        print("Error: google-credentials.json not found.")
        return

    # Start audio playback thread (optional)
    playback_thread = threading.Thread(target=audio_playback_thread, daemon=True)
    playback_thread.start()

    # Start Flask in a separate thread
    from threading import Thread
    def run_flask():
        app.run(host='0.0.0.0', port=3000, debug=False, use_reloader=False)
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    print("Flask server running on port 3000")

    # Start WebSocket server
    try:
        start_server = websockets.serve(twilio_websocket, '0.0.0.0', 8080)
        await start_server
        print("WebSocket server running on port 8080")
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