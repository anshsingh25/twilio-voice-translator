import os
import pyaudio
import queue
import threading
import time
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google-credentials.json"

# Audio stream parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024  # Smaller chunk size for lower latency

# Queues for passing transcriptions and translations between threads
transcript_queue = queue.Queue()
translation_queue = queue.Queue()

# Flag to control the streaming loop
running = True

# Set to keep track of processed transcripts to avoid duplicates
processed_transcripts = set()

def stream_audio_to_transcript():
    """Stream audio from microphone and send to Google Cloud for transcription."""
    global running
    try:
        client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code="en-US",
            enable_automatic_punctuation=True
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=False  # Disable interim results to reduce duplicates
        )

        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        print("Listening for English speech...")

        requests = (
            speech.StreamingRecognizeRequest(audio_content=chunk)
            for chunk in iter(lambda: stream.read(CHUNK, exception_on_overflow=False), b"")
        )

        responses = client.streaming_recognize(streaming_config, requests)

        for response in responses:
            if not running:
                break
            for result in response.results:
                if result.is_final:  # Only process final results
                    transcript = result.alternatives[0].transcript.strip()
                    # Check if transcript is new and non-empty
                    if transcript and transcript not in processed_transcripts:
                        print(f"English Text: {transcript}")
                        processed_transcripts.add(transcript)
                        transcript_queue.put(transcript)

        stream.stop_stream()
        stream.close()
        audio.terminate()
    except Exception as e:
        print(f"Streaming transcription error: {e}")
        running = False

def translate_transcripts():
    """Translate English transcripts to Hindi in real-time."""
    global running
    try:
        client = translate.Client()
        while running:
            try:
                # Get transcript from queue (non-blocking)
                transcript = transcript_queue.get(timeout=1)
                result = client.translate(transcript, source_language='en', target_language='hi')
                hindi_text = result['translatedText']
                print(f"Hindi Text: {hindi_text}")
                translation_queue.put(hindi_text)
                transcript_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Translation error: {e}")
    except Exception as e:
        print(f"Translator thread error: {e}")
        running = False

def synthesize_and_play():
    """Convert Hindi text to speech and play it in real-time."""
    global running
    try:
        client = texttospeech.TextToSpeechClient()
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, output=True)

        while running:
            try:
                # Get Hindi text from queue (non-blocking)
                hindi_text = translation_queue.get(timeout=1)
                synthesis_input = texttospeech.SynthesisInput(text=hindi_text)
                voice = texttospeech.VoiceSelectionParams(
                    language_code="hi-IN",
                    name="hi-IN-Standard-A"  # Hindi female voice
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000
                )

                response = client.synthesize_speech(
                    input=synthesis_input, voice=voice, audio_config=audio_config
                )

                print("Playing Hindi speech...")
                stream.write(response.audio_content)
                translation_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Text-to-Speech error: {e}")

        stream.stop_stream()
        stream.close()
        p.terminate()
    except Exception as e:
        print(f"Synthesis thread error: {e}")
        running = False

def main():
    global running
    try:
        # Verify credentials file
        if not os.path.exists("google-credentials.json"):
            print("Error: google-credentials.json not found in the current directory.")
            return False

        # Start threads for streaming transcription, translation, and synthesis
        transcription_thread = threading.Thread(target=stream_audio_to_transcript)
        translation_thread = threading.Thread(target=translate_transcripts)
        synthesis_thread = threading.Thread(target=synthesize_and_play)

        transcription_thread.start()
        translation_thread.start()
        synthesis_thread.start()

        # Wait for threads to complete
        transcription_thread.join()
        translation_thread.join()
        synthesis_thread.join()

        return True
    except Exception as e:
        print(f"Main error: {e}")
        running = False
        return True

if __name__ == "__main__":
    print("Starting real-time translator. Press Ctrl+C to abort.")
    try:
        if not main():
            print("Program terminated due to missing credentials.")
    except KeyboardInterrupt:
        print("\nProgram aborted by user.")
        running = False
    except Exception as e:
        print(f"Unexpected error: {e}")
        running = False